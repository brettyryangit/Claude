#!/usr/bin/env python3
"""
Claude Code Telegram Bridge

Connects a Telegram group (with Topics enabled) to Claude Code CLI sessions.
Each topic = one Claude Code conversation with full context and tool access.

Architecture:
    Telegram Group (Topics) <-> This Bot <-> Claude Code CLI (claude -p)
    Each topic_id maps to a unique Claude Code session UUID.
    Sessions persist across bot restarts via sessions.json.
"""

import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import Bot, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import BadRequest, RetryAfter, TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Optional: entity-based markdown formatting (preferred over MarkdownV2 parse mode)
try:
    from telegramify_markdown import convert as tm_convert
    HAS_TELEGRAMIFY = True
except ImportError:
    HAS_TELEGRAMIFY = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(Path(__file__).parent / ".env")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USERS = frozenset(
    int(uid.strip()) for uid in os.environ["ALLOWED_USER_IDS"].split(",")
)
# Optional: restrict bot to a specific Telegram group (recommended)
ALLOWED_GROUP_ID = int(os.environ["TELEGRAM_GROUP_ID"]) if os.environ.get("TELEGRAM_GROUP_ID") else None
WORKING_DIR = os.environ.get("WORKING_DIR", os.path.expanduser("~"))
WHISPER_PROVIDER = os.environ.get("WHISPER_PROVIDER", "").strip().lower()
WHISPER_API_KEY = os.environ.get("WHISPER_API_KEY", "")
CLAUDE_TIMEOUT = int(os.environ.get("CLAUDE_TIMEOUT", "300"))  # 5 min default
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "")  # empty = default model
STREAM_EDIT_INTERVAL = 1.5  # Seconds between Telegram message edits during streaming

STATE_DIR = Path(__file__).parent / "state"
SESSION_FILE = STATE_DIR / "sessions.json"
UPLOAD_DIR_NAME = ".claude-uploads"

# Telegram limits and rate control
MAX_MSG_LEN = 3000  # Leave room for [1/N] prefix + entity overhead (limit is 4096)
TYPING_INTERVAL = 4.0  # Telegram typing indicator expires after ~5 seconds
RATE_LIMIT_INTERVAL = 1.1  # Minimum seconds between sends to same chat

# Logging - suppress httpx to prevent bot token leaking in log URLs
# RotatingFileHandler: keeps last 1MB + 2 backups (3MB total max)
_log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
_log_dir = Path(__file__).parent / "logs"
_log_dir.mkdir(exist_ok=True)

_file_handler = RotatingFileHandler(
    _log_dir / "stderr.log", maxBytes=1_000_000, backupCount=2
)
_file_handler.setFormatter(_log_format)
_file_handler.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, handlers=[_file_handler])
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("claude-bridge")

# Per-topic locks to prevent concurrent Claude processes on the same session
_topic_locks: dict[str, asyncio.Lock] = {}
# Track running Claude processes so they can be stopped
_running_processes: dict[str, asyncio.subprocess.Process] = {}
# Track topics where user hit Stop (so we skip sending the response)
_stopped_topics: set[str] = set()


def _get_topic_lock(topic_id) -> asyncio.Lock:
    """Get or create an asyncio.Lock for a topic. Ensures sequential processing."""
    key = str(topic_id if topic_id else "general")
    if key not in _topic_locks:
        _topic_locks[key] = asyncio.Lock()
    return _topic_locks[key]


def _topic_key(topic_id) -> str:
    return str(topic_id if topic_id else "general")


# ---------------------------------------------------------------------------
# Auth Check
# ---------------------------------------------------------------------------

def _is_authorized(update: Update) -> bool:
    """Check if the message sender is allowed AND the group is correct."""
    if not update.effective_user or update.effective_user.id not in ALLOWED_USERS:
        return False
    if ALLOWED_GROUP_ID and update.effective_chat and update.effective_chat.id != ALLOWED_GROUP_ID:
        logger.warning(
            "Rejected message from allowed user in wrong group: %s",
            update.effective_chat.id,
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------

def _ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_sessions() -> dict:
    """Load topic -> session mapping from disk."""
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt sessions.json, starting fresh")
            return {}
    return {}


def save_sessions(sessions: dict):
    """Persist topic -> session mapping to disk."""
    _ensure_state_dir()
    tmp = SESSION_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(sessions, indent=2))
    tmp.replace(SESSION_FILE)  # Atomic write


def get_or_create_session(topic_id) -> tuple[str, bool]:
    """Get existing session for a topic, or create a new one.

    Returns (session_uuid, is_new).
    """
    sessions = load_sessions()
    key = str(topic_id if topic_id else "general")

    if key in sessions:
        sessions[key]["last_used"] = datetime.now(timezone.utc).isoformat()
        save_sessions(sessions)
        return sessions[key]["session_id"], False

    sid = str(uuid.uuid4())
    sessions[key] = {
        "session_id": sid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": datetime.now(timezone.utc).isoformat(),
    }
    save_sessions(sessions)
    return sid, True


def reset_session(topic_id) -> str:
    """Reset a topic's session (creates a new one). Returns new session ID."""
    sessions = load_sessions()
    key = str(topic_id if topic_id else "general")
    sid = str(uuid.uuid4())
    sessions[key] = {
        "session_id": sid,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": datetime.now(timezone.utc).isoformat(),
    }
    save_sessions(sessions)
    return sid


# ---------------------------------------------------------------------------
# Message Formatting & Splitting
# ---------------------------------------------------------------------------

def split_message(text: str, max_length: int = MAX_MSG_LEN) -> list[str]:
    """Split text on newline boundaries, respecting max_length.

    Avoids splitting mid-line. Force-splits individual lines that exceed max_length.
    """
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    current = ""

    for line in text.split("\n"):
        if len(line) > max_length:
            # Flush current buffer first
            if current:
                chunks.append(current.rstrip("\n"))
                current = ""
            # Force-split oversized lines
            for i in range(0, len(line), max_length):
                chunks.append(line[i : i + max_length])
        elif len(current) + len(line) + 1 > max_length:
            # Current chunk is full, start a new one
            chunks.append(current.rstrip("\n"))
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        chunks.append(current.rstrip("\n"))

    return chunks


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting for plain text fallback."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'~~(.+?)~~', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', lambda m: m.group().strip('`').strip(), text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    return text


async def safe_send(message, text: str, **kwargs):
    """Send a message with entity-based formatting, falling back to plain text.

    Phase 1: Try telegramify-markdown entities (zero parse errors)
    Phase 2: Fall back to plain text with markdown stripped
    Handles RetryAfter (flood control) by sleeping and retrying once.
    """
    # Phase 1: Entity-based formatting (most robust)
    if HAS_TELEGRAMIFY:
        try:
            plain_text, tm_entities = tm_convert(text)
            # Convert telegramify_markdown entities to telegram.MessageEntity
            from telegram import MessageEntity
            tg_entities = [
                MessageEntity(
                    type=e.type,
                    offset=e.offset,
                    length=e.length,
                    url=e.url,
                    language=e.language,
                )
                for e in tm_entities
            ]
            return await message.reply_text(
                plain_text,
                entities=tg_entities,
                **kwargs,
            )
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 1)
            try:
                return await message.reply_text(
                    plain_text,
                    entities=tg_entities,
                    **kwargs,
                )
            except TelegramError:
                pass
        except TelegramError as exc:
            logger.warning("Entity send failed: %s", exc)
        except Exception as exc:
            logger.warning("telegramify-markdown failed: %s", exc)

    # Phase 2: Plain text fallback (strip markdown so ** doesn't show)
    clean_text = _strip_markdown(text)
    try:
        return await message.reply_text(clean_text, **kwargs)
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after + 1)
        try:
            return await message.reply_text(clean_text, **kwargs)
        except TelegramError as exc:
            logger.error("Failed to send after retry: %s", exc)
            return None
    except BadRequest as exc:
        if "not found" in str(exc).lower():
            return None  # Message was deleted
        logger.error("BadRequest sending message: %s", exc)
        return None
    except TelegramError as exc:
        logger.error("TelegramError sending message: %s", exc)
        return None


async def send_long_reply(message, text: str):
    """Send a potentially long response, split across multiple messages."""
    chunks = split_message(text)

    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            chunk = f"[{i + 1}/{len(chunks)}]\n{chunk}"
        await safe_send(message, chunk)
        if i < len(chunks) - 1:
            await asyncio.sleep(RATE_LIMIT_INTERVAL)


# ---------------------------------------------------------------------------
# Typing Indicator
# ---------------------------------------------------------------------------

async def typing_loop(
    chat_id: int,
    bot: Bot,
    topic_id: int | None,
    stop: asyncio.Event,
):
    """Send typing indicator every TYPING_INTERVAL seconds until stopped."""
    while not stop.is_set():
        try:
            await bot.send_chat_action(
                chat_id=chat_id,
                action=ChatAction.TYPING,
                message_thread_id=topic_id,
            )
        except TelegramError:
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=TYPING_INTERVAL)
            break
        except asyncio.TimeoutError:
            continue


# ---------------------------------------------------------------------------
# Claude Code Execution
# ---------------------------------------------------------------------------

async def _start_claude_streaming(prompt, session_id, is_new, topic_key):
    """Start Claude CLI in streaming mode and send the prompt.

    Returns (proc, error_msg). On failure, proc=None and error_msg describes what went wrong.
    Handles the initialize handshake and sends the user message.
    """
    cmd = [
        "claude",
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--input-format", "stream-json",
        "--include-partial-messages",
    ]
    if not is_new:
        cmd.extend(["--resume", session_id])
    if CLAUDE_MODEL:
        cmd.extend(["--model", CLAUDE_MODEL])

    logger.info(
        "Claude streaming [session=%s, new=%s, prompt_len=%d]",
        session_id[:8], is_new, len(prompt),
    )

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKING_DIR,
            env=env,
            limit=1024 * 1024,  # 1MB line buffer (init message is large)
        )
    except FileNotFoundError:
        return None, "Claude CLI not found. Is it installed and in PATH?"
    except OSError as e:
        return None, f"Failed to start Claude: {e}"

    _running_processes[topic_key] = proc

    # Send initialize handshake
    try:
        init_req = json.dumps({
            "type": "control_request",
            "request_id": "init_1",
            "request": {"subtype": "initialize", "hooks": None},
        })
        proc.stdin.write((init_req + "\n").encode())
        await proc.stdin.drain()

        # Wait for control_response (with timeout)
        initialized = False
        init_error = None

        async def _wait_for_init():
            nonlocal initialized, init_error
            async for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if d.get("type") == "control_response":
                    initialized = True
                    return
                if d.get("type") == "result" and d.get("is_error"):
                    init_error = d.get("result", "Unknown error")
                    return

        try:
            await asyncio.wait_for(_wait_for_init(), timeout=30)
        except asyncio.TimeoutError:
            pass

        if not initialized:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            _running_processes.pop(topic_key, None)
            await proc.wait()

            # If we were resuming, retry as new session (most common cause: session not found)
            if not is_new:
                logger.info("Session %s failed to resume, retrying as new", session_id[:8])
                return await _start_claude_streaming(prompt, session_id, True, topic_key)

            # New session also failed
            if init_error:
                return None, f"Claude error: {init_error[:500]}"
            return None, "Claude failed to initialize (timeout)."

        # Send user message
        user_msg = json.dumps({
            "type": "user",
            "session_id": "",
            "message": {"role": "user", "content": prompt},
            "parent_tool_use_id": None,
        })
        proc.stdin.write((user_msg + "\n").encode())
        await proc.stdin.drain()
        proc.stdin.close()

    except Exception as e:
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        _running_processes.pop(topic_key, None)
        return None, f"Failed to send prompt: {e}"

    return proc, None


# ---------------------------------------------------------------------------
# Voice Transcription
# ---------------------------------------------------------------------------

# Lazy-loaded Whisper model (loaded on first voice message)
_whisper_model_cache = {}

WHISPER_CONFIGS = {
    "openai": {
        "url": "https://api.openai.com/v1/audio/transcriptions",
        "model": "whisper-1",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/audio/transcriptions",
        "model": "whisper-large-v3",
    },
}

WHISPER_LOCAL_MODEL = os.environ.get("WHISPER_MODEL", "mlx-community/whisper-small-mlx")


async def transcribe_voice(audio_bytes: bytes) -> str:
    """Transcribe audio using local Whisper or a remote API."""
    if WHISPER_PROVIDER == "local":
        return await _transcribe_local(audio_bytes)
    elif WHISPER_PROVIDER in WHISPER_CONFIGS:
        return await _transcribe_api(audio_bytes)
    else:
        raise ValueError(f"Unknown whisper provider: {WHISPER_PROVIDER}")


async def _transcribe_local(audio_bytes: bytes) -> str:
    """Transcribe using mlx-whisper locally on Apple Silicon."""
    import mlx_whisper

    # Save audio to temp file (mlx-whisper needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        # Run transcription in a thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: mlx_whisper.transcribe(
                tmp_path,
                path_or_hf_repo=WHISPER_LOCAL_MODEL,
            ),
        )
        return result["text"].strip()
    finally:
        os.unlink(tmp_path)


async def _transcribe_api(audio_bytes: bytes) -> str:
    """Transcribe using a remote Whisper-compatible API (OpenAI/Groq)."""
    config = WHISPER_CONFIGS[WHISPER_PROVIDER]

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            config["url"],
            headers={"Authorization": f"Bearer {WHISPER_API_KEY}"},
            files={"file": ("voice.ogg", audio_bytes, "audio/ogg")},
            data={"model": config["model"]},
        )
        resp.raise_for_status()
        return resp.json()["text"]


# ---------------------------------------------------------------------------
# File Handling
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """Remove path components and unsafe characters from a filename."""
    name = Path(name).name
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    if not name or name.startswith("."):
        name = f"file_{name}"
    return name[:200]


def get_upload_dir() -> Path:
    """Get (and create if needed) the upload directory inside the project."""
    upload_dir = Path(WORKING_DIR) / UPLOAD_DIR_NAME
    if upload_dir.is_symlink():
        raise RuntimeError("Upload directory is a symlink, refusing to write")
    upload_dir.mkdir(exist_ok=True)
    return upload_dir


async def save_upload(tg_file, filename: str) -> Path:
    """Download a Telegram file to the uploads directory.

    Returns the path to the saved file. Handles duplicate filenames.
    """
    upload_dir = get_upload_dir()
    safe_name = sanitize_filename(filename)
    dest = upload_dir / safe_name

    # Unique filename if already exists
    if dest.exists():
        stem = dest.stem
        suffix = dest.suffix
        counter = 1
        while dest.exists():
            dest = upload_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    await tg_file.download_to_drive(str(dest))

    # Verify file stays within upload directory (path traversal protection)
    try:
        dest.resolve().relative_to(upload_dir.resolve())
    except ValueError:
        dest.unlink(missing_ok=True)
        raise RuntimeError("Path traversal detected, file rejected")

    return dest


# ---------------------------------------------------------------------------
# Core Prompt Processor
# ---------------------------------------------------------------------------

async def _process_prompt(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    prompt: str,
):
    """Central handler: send prompt to Claude Code and stream the response back.

    Uses streaming JSON mode to edit the Telegram message in real-time as
    Claude generates text. Shows thinking status and response progressively.
    """
    topic_id = update.message.message_thread_id
    key = _topic_key(topic_id)

    # Acquire per-topic lock (queues messages to same topic sequentially)
    lock = _get_topic_lock(topic_id)
    async with lock:
        session_id, is_new = get_or_create_session(topic_id)

        # Clear any stale stop flag
        _stopped_topics.discard(key)

        # Send "Thinking..." message with Stop button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Stop", callback_data=f"stop:{key}")]
        ])
        thinking_msg = None
        try:
            thinking_msg = await update.message.reply_text(
                "Thinking...", reply_markup=keyboard,
            )
        except TelegramError as e:
            logger.warning("Failed to send thinking message: %s", e)

        # Start typing indicator
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(
            typing_loop(
                update.effective_chat.id,
                context.bot,
                topic_id,
                stop_typing,
            )
        )

        accumulated_text = ""
        last_edit_time = 0.0
        final_session_id = session_id
        error_response = None

        try:
            proc, start_err = await _start_claude_streaming(
                prompt, session_id, is_new, key
            )
            if start_err:
                error_response = start_err
            else:
                # Read streaming events from stdout
                async for raw_line in proc.stdout:
                    # Check if user hit Stop
                    if key in _stopped_topics:
                        proc.kill()
                        break

                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    msg_type = d.get("type")

                    if msg_type == "stream_event":
                        event = d.get("event", {})
                        etype = event.get("type")

                        if etype == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                accumulated_text += delta.get("text", "")

                            # Edit Telegram message with progress (debounced)
                            now = time.time()
                            if thinking_msg and accumulated_text and (now - last_edit_time) >= STREAM_EDIT_INTERVAL:
                                try:
                                    display = accumulated_text[:3900]
                                    if len(accumulated_text) > 3900:
                                        display += "\n..."
                                    await thinking_msg.edit_text(
                                        display, reply_markup=keyboard
                                    )
                                    last_edit_time = now
                                except (TelegramError, Exception):
                                    pass

                    elif msg_type == "assistant":
                        # Full assistant message (backup: extract text if deltas missed)
                        msg = d.get("message", {})
                        for block in msg.get("content", []):
                            if block.get("type") == "text" and block.get("text"):
                                accumulated_text = block["text"]

                    elif msg_type == "result":
                        final_session_id = d.get("session_id", session_id)
                        if d.get("is_error"):
                            error_response = d.get("result") or "Claude returned an error."
                        elif d.get("result"):
                            accumulated_text = d["result"]
                        break

                # Wait for process to finish
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5)
                except asyncio.TimeoutError:
                    proc.kill()

                _running_processes.pop(key, None)

                # If process failed without a result (e.g. session not found)
                if not accumulated_text and not error_response and proc.returncode and proc.returncode != 0:
                    stderr_out = await proc.stderr.read()
                    err = stderr_out.decode("utf-8", errors="replace").strip()
                    if err:
                        error_response = f"Claude error:\n{err[:2000]}"
                    else:
                        error_response = f"Claude exited with code {proc.returncode}"

        except Exception as e:
            logger.exception("Streaming error [topic=%s]", key)
            error_response = f"Error: {e}"
            _running_processes.pop(key, None)

        finally:
            stop_typing.set()
            await typing_task

        # Update session mapping if Claude assigned a different session ID
        if final_session_id != session_id:
            sessions = load_sessions()
            k = str(topic_id if topic_id else "general")
            if k in sessions:
                sessions[k]["session_id"] = final_session_id
                save_sessions(sessions)

        # If user hit Stop, keep the "Stopped." message visible
        if key in _stopped_topics:
            _stopped_topics.discard(key)
            return

        # Normal flow: delete thinking message, send final formatted response
        if thinking_msg:
            try:
                await thinking_msg.delete()
            except TelegramError:
                pass

        response = error_response or accumulated_text or "(Claude returned an empty response)"
        await send_long_reply(update.message, response)


# ---------------------------------------------------------------------------
# Telegram Handlers
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    if not _is_authorized(update):
        return
    if not update.message or not update.message.text:
        return

    await _process_prompt(update, context, update.message.text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages: download, transcribe via Whisper, then process."""
    if not _is_authorized(update):
        return
    if not update.message:
        return

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    if not WHISPER_PROVIDER:
        await safe_send(
            update.message,
            "Voice messages not configured. Set WHISPER_PROVIDER in .env.",
        )
        return

    if WHISPER_PROVIDER != "local" and not WHISPER_API_KEY:
        await safe_send(
            update.message,
            f"Voice API key not configured. Set WHISPER_API_KEY for {WHISPER_PROVIDER}.",
        )
        return

    if voice.file_size and voice.file_size > 25 * 1024 * 1024:
        await safe_send(update.message, "Voice message too large (max 25MB).")
        return

    # Download and transcribe
    try:
        tg_file = await context.bot.get_file(voice.file_id)
        audio_bytes = bytes(await tg_file.download_as_bytearray())
        text = await transcribe_voice(audio_bytes)
    except httpx.HTTPStatusError as e:
        await safe_send(update.message, f"Transcription API error: {e.response.status_code}")
        return
    except Exception as e:
        await safe_send(update.message, f"Transcription failed: {e}")
        return

    # Check for empty transcription
    if not text or not text.strip():
        await safe_send(update.message, "Could not transcribe voice message (empty result).")
        return

    # Show what was transcribed
    await safe_send(update.message, f"Transcribed: {text}")

    # Process the transcribed text as a prompt
    await _process_prompt(update, context, text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads: save to project dir, tell Claude the path."""
    if not _is_authorized(update):
        return
    if not update.message or not update.message.photo:
        return

    # Get highest resolution version
    photo = update.message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}_{photo.file_unique_id[:8]}.jpg"

    try:
        dest = await save_upload(tg_file, filename)
    except Exception as e:
        await safe_send(update.message, f"Failed to save photo: {e}")
        return

    rel_path = dest.relative_to(WORKING_DIR)
    caption = update.message.caption or "Please take a look at this image."
    prompt = f"I've uploaded an image to {rel_path}. {caption}"

    await _process_prompt(update, context, prompt)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document/file uploads: save to project dir, tell Claude the path."""
    if not _is_authorized(update):
        return
    if not update.message or not update.message.document:
        return

    doc = update.message.document
    if doc.file_size and doc.file_size > 50 * 1024 * 1024:
        await safe_send(update.message, "File too large (max 50MB).")
        return

    tg_file = await context.bot.get_file(doc.file_id)
    filename = doc.file_name or f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    try:
        dest = await save_upload(tg_file, filename)
    except Exception as e:
        await safe_send(update.message, f"Failed to save file: {e}")
        return

    rel_path = dest.relative_to(WORKING_DIR)
    safe_name = dest.name  # Use the sanitized filename, not the original
    caption = update.message.caption or "Please take a look at this file."
    prompt = f"I've uploaded {safe_name} to {rel_path}. {caption}"

    await _process_prompt(update, context, prompt)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset the current topic's Claude session (start fresh)."""
    if not _is_authorized(update):
        return

    topic_id = update.message.message_thread_id
    new_sid = reset_session(topic_id)
    await safe_send(
        update.message,
        f"Session reset. New session: {new_sid[:8]}... Next message starts fresh.",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current session info for this topic."""
    if not _is_authorized(update):
        return

    topic_id = update.message.message_thread_id
    sessions = load_sessions()
    key = str(topic_id if topic_id else "general")

    if key in sessions:
        s = sessions[key]
        await safe_send(
            update.message,
            f"Session: {s['session_id'][:8]}...\n"
            f"Created: {s.get('created_at', 'unknown')}\n"
            f"Last used: {s.get('last_used', 'unknown')}\n"
            f"Working dir: {WORKING_DIR}",
        )
    else:
        await safe_send(update.message, "No session for this topic yet. Send a message to start one.")


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the chat/group ID (for .env configuration)."""
    if not update.effective_user or update.effective_user.id not in ALLOWED_USERS:
        return

    chat = update.effective_chat
    await safe_send(
        update.message,
        f"Chat ID: {chat.id}\n"
        f"Chat type: {chat.type}\n"
        f"Chat title: {chat.title or 'N/A'}\n"
        f"Your user ID: {update.effective_user.id}\n"
        f"Topic ID: {update.message.message_thread_id or 'N/A'}",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available commands."""
    if not _is_authorized(update):
        return

    await safe_send(
        update.message,
        "Claude Code Telegram Bridge\n\n"
        "Just type a message or send a voice note to talk to Claude Code.\n"
        "Each topic = separate conversation.\n\n"
        "Commands:\n"
        "/new - Start fresh session\n"
        "/stop - Stop current response\n"
        "/topic <name> - Create a new topic\n"
        "/status - Session info\n"
        "/id - Show chat/group ID\n"
        "/help - Show commands",
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop the currently running Claude process in this topic."""
    if not _is_authorized(update):
        return

    topic_id = update.message.message_thread_id
    key = _topic_key(topic_id)
    proc = _running_processes.get(key)

    if proc and proc.returncode is None:
        _stopped_topics.add(key)
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        await safe_send(update.message, "Stopped.")
    else:
        await safe_send(update.message, "Nothing running to stop.")


async def handle_stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the inline Stop button press."""
    query = update.callback_query

    # Auth check
    if not query.from_user or query.from_user.id not in ALLOWED_USERS:
        await query.answer("Not authorized.")
        return

    await query.answer()  # Acknowledge button press (removes loading state)

    data = query.data  # "stop:<topic_key>"
    key = data.split(":", 1)[1] if ":" in data else None
    if not key:
        return

    proc = _running_processes.get(key)
    if proc and proc.returncode is None:
        _stopped_topics.add(key)
        try:
            proc.kill()
        except ProcessLookupError:
            pass
        try:
            await query.edit_message_text("Stopped.")
        except TelegramError:
            pass
    else:
        try:
            await query.edit_message_text("Already finished.")
        except TelegramError:
            pass


async def cmd_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new forum topic and set up a session for it."""
    if not _is_authorized(update):
        return

    if not context.args:
        await safe_send(update.message, "Usage: /topic <name>\nExample: /topic SEO Strategy")
        return

    topic_name = " ".join(context.args)

    try:
        forum_topic = await context.bot.create_forum_topic(
            chat_id=update.effective_chat.id,
            name=topic_name,
        )
    except TelegramError as e:
        await safe_send(update.message, f"Failed to create topic: {e}")
        return

    # Set up a session for the new topic
    get_or_create_session(forum_topic.message_thread_id)

    await safe_send(
        update.message,
        f"Topic \"{topic_name}\" created. Go send your first message there.",
    )


# ---------------------------------------------------------------------------
# Post-Init: Register Bot Command Menu
# ---------------------------------------------------------------------------

async def post_init(application: Application):
    """Register bot commands so they appear in Telegram's slash command menu."""
    await application.bot.set_my_commands([
        BotCommand("new", "Start fresh session"),
        BotCommand("stop", "Stop current response"),
        BotCommand("topic", "Create a new topic"),
        BotCommand("status", "Session info"),
        BotCommand("help", "Show commands"),
    ])
    logger.info("Bot command menu registered")


# ---------------------------------------------------------------------------
# Error Handler
# ---------------------------------------------------------------------------

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler. Shuts down on duplicate instance, logs everything else."""
    from telegram.error import Conflict

    if isinstance(context.error, Conflict):
        logger.critical(
            "Another bot instance is running with the same token. "
            "Exiting with code 1 so launchd will restart us."
        )
        # Exit non-zero so launchd KeepAlive restarts us.
        # ThrottleInterval (10s) prevents a tight restart loop.
        os._exit(1)

    from telegram.error import NetworkError
    if isinstance(context.error, NetworkError):
        logger.warning("Network error (will retry automatically): %s", context.error)
        return

    logger.error("Unhandled error: %s", context.error, exc_info=context.error)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    _ensure_state_dir()

    app = Application.builder().token(BOT_TOKEN).concurrent_updates(True).post_init(post_init).build()

    # Commands
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("reset", cmd_new))  # Alias
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("topic", cmd_topic))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(CommandHandler("id", cmd_id))

    # Inline button handler (Stop button)
    app.add_handler(CallbackQueryHandler(handle_stop_callback, pattern=r"^stop:"))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("Claude Code Telegram Bridge starting...")
    logger.info("Working directory: %s", WORKING_DIR)
    logger.info("Allowed users: %s", ALLOWED_USERS)
    logger.info("Whisper provider: %s", WHISPER_PROVIDER or "disabled")
    logger.info("Claude timeout: %ds", CLAUDE_TIMEOUT)
    logger.info("Claude model: %s", CLAUDE_MODEL or "default")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
