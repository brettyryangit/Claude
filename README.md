# Claude Code Telegram Bridge

Talk to Claude Code from your phone via Telegram. Each topic in a Telegram group becomes a separate Claude Code conversation with full tool access, file reading, code editing, and workspace context.

**Architecture**: Telegram Group (with Topics) <-> Python Bot <-> Claude Code CLI (stream-json mode)

---

## What It Does

- Send text messages in Telegram, get full Claude Code responses back
- Each **forum topic** = separate Claude Code session (persistent across restarts)
- **Streaming responses** - see Claude's output as it types, not just the final result
- **Voice messages** - transcribed via Whisper (local or API), then sent to Claude
- **Photo & file uploads** - saved to your workspace, Claude reads them directly
- **Session persistence** - resume conversations even after bot restarts
- **Inline Stop button** - kill a long-running Claude process mid-response
- **Concurrent topics** - multiple topics can run simultaneously (one at a time per topic)

---

## Prerequisites

- **Claude Code CLI** installed and working (`claude` command available in terminal)
- **Python 3.10+**
- **A Telegram Bot** (created via [@BotFather](https://t.me/BotFather))
- **A Telegram Group with Topics/Forum enabled** (Group Settings > Topics > turn on)
- **macOS** (for LaunchAgent auto-start; Linux users can use systemd instead)

---

## Setup

### 1. Create Your Telegram Bot

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`, follow the prompts
3. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrSTUVwxyz`)
4. **Important**: Send `/setjoingroups` > select your bot > Enable (so it can join groups)
5. Add the bot to your Telegram group
6. Make the bot an **admin** in the group (it needs permission to create topics and send messages)

### 2. Get Your IDs

Add the bot to your group, then send `/id` to it. Note down:
- **Your user ID** (e.g., `123456789`)
- **Group chat ID** (e.g., `-1001234567890`)

### 3. Clone This Repository

```bash
git clone https://github.com/brettyryangit/claude.git ~/.claude/telegram-bridge
cd ~/.claude/telegram-bridge
mkdir -p telegram-bridge/state telegram-bridge/logs
```

### 4. Install Dependencies

```bash
pip install -r telegram-bridge/requirements.txt
```

**Optional** (for local voice transcription on Apple Silicon):

```bash
pip install mlx-whisper>=0.4.0
```

### 5. Configure Environment

Copy and edit the example config:

```bash
cp telegram-bridge/.env.example telegram-bridge/.env
```

Edit `telegram-bridge/.env`:

```env
TELEGRAM_BOT_TOKEN=your-bot-token-here
ALLOWED_USER_IDS=your-telegram-user-id
TELEGRAM_GROUP_ID=your-group-chat-id
WORKING_DIR=/path/to/your/project
CLAUDE_TIMEOUT=300
CLAUDE_MODEL=

# Voice transcription (pick one or leave empty to disable)
WHISPER_PROVIDER=local
WHISPER_MODEL=mlx-community/whisper-small-mlx

# Or use OpenAI/Groq API:
# WHISPER_PROVIDER=openai
# WHISPER_API_KEY=sk-...

# Or Groq (free, fast):
# WHISPER_PROVIDER=groq
# WHISPER_API_KEY=gsk_...
```

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | From BotFather |
| `ALLOWED_USER_IDS` | Yes | Comma-separated Telegram user IDs that can use the bot |
| `TELEGRAM_GROUP_ID` | No | Restrict bot to one group (recommended) |
| `WORKING_DIR` | Yes | Absolute path to your project/workspace directory |
| `CLAUDE_TIMEOUT` | No | Max seconds per Claude response (default: 300) |
| `CLAUDE_MODEL` | No | Override Claude model (empty = default) |
| `WHISPER_PROVIDER` | No | `local`, `openai`, or `groq` (empty = voice disabled) |
| `WHISPER_API_KEY` | No | Required for openai/groq providers |
| `WHISPER_MODEL` | No | Local model name (default: `mlx-community/whisper-small-mlx`) |

### 6. Test It

```bash
cd telegram-bridge
python3 bridge.py
```

Send a message in your Telegram group. You should see "Thinking..." followed by Claude's response.

---

## Auto-Start on Login (macOS LaunchAgent)

1. Copy the plist template:
   ```bash
   cp telegram-bridge/com.claude.telegram-bridge.plist ~/Library/LaunchAgents/
   ```

2. Edit `~/Library/LaunchAgents/com.claude.telegram-bridge.plist` and replace `YOUR_USERNAME` with your macOS username.

3. **Important**: Update `ProgramArguments` to point to the Python binary that has your dependencies installed. Check with `which python3`.

4. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.claude.telegram-bridge.plist
   ```

To stop:
```bash
launchctl unload ~/Library/LaunchAgents/com.claude.telegram-bridge.plist
```

To check status:
```bash
launchctl list | grep claude
```

### Linux Alternative (systemd)

1. Copy the service template:
   ```bash
   cp telegram-bridge/claude-telegram-bridge.service ~/.config/systemd/user/
   ```

2. Edit it and replace `YOUR_USERNAME` with your Linux username.

3. Enable and start:
   ```bash
   systemctl --user enable claude-telegram-bridge
   systemctl --user start claude-telegram-bridge
   systemctl --user status claude-telegram-bridge
   ```

---

## Repository Structure

```
telegram-bridge/
├── bridge.py                          # Main bot script
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment config template
├── com.claude.telegram-bridge.plist   # macOS LaunchAgent template
├── claude-telegram-bridge.service     # Linux systemd template
├── state/                             # Session persistence (sessions.json)
└── logs/                              # Log files (stderr.log, stdout.log)
```

---

## How It Works

### Message Flow

```
You (Telegram) --> Send message in topic
                       |
                       v
              Bot receives message
                       |
                       v
              Auth check (user ID + group ID)
                       |
                       v
              Per-topic lock acquired (queue if busy)
                       |
                       v
              Get/create session UUID for this topic
                       |
                       v
              Start Claude CLI subprocess:
              claude --output-format stream-json \
                     --verbose \
                     --dangerously-skip-permissions \
                     --input-format stream-json \
                     --include-partial-messages \
                     --resume <session_id>
                       |
                       v
              Send initialize handshake (control_request)
                       |
                       v
              Wait for control_response (30s timeout)
                       |
                       v
              Send user message as JSON
                       |
                       v
              Read stream_event messages:
              - content_block_delta -> accumulate text
              - Edit Telegram message every 1.5s with progress
              - result -> final response
                       |
                       v
              Delete "Thinking..." message
              Send final formatted response
```

### Session Persistence

Sessions are stored in `state/sessions.json`:

```json
{
  "42": {
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "created_at": "2025-01-15T10:30:00.000000+00:00",
    "last_used": "2025-01-15T14:22:00.000000+00:00"
  },
  "general": {
    "session_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
    "created_at": "2025-01-16T08:00:00.000000+00:00",
    "last_used": "2025-01-16T08:15:00.000000+00:00"
  }
}
```

- Each topic ID maps to a Claude Code session UUID
- Messages outside topics use the key `"general"`
- `/new` resets the session for the current topic
- If a session resume fails, the bot automatically retries as a new session

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/new` | Start a fresh Claude session in the current topic |
| `/reset` | Alias for `/new` |
| `/stop` | Kill the currently running Claude process |
| `/topic <name>` | Create a new forum topic with a session |
| `/status` | Show session ID, creation time, last used |
| `/id` | Show chat/group/topic IDs (for configuration) |
| `/help` | List available commands |

There's also an inline **Stop** button that appears with every "Thinking..." message.

---

## Supported Input Types

| Type | How It Works |
|------|-------------|
| **Text** | Sent directly as Claude prompt |
| **Voice** | Downloaded, transcribed via Whisper, sent as text |
| **Photo** | Saved to `.claude-uploads/`, path sent to Claude (Claude reads the image) |
| **Document** | Saved to `.claude-uploads/`, path sent to Claude (50MB limit) |

---

## Voice Transcription Options

| Provider | Setup | Notes |
|----------|-------|-------|
| `local` | `pip install mlx-whisper` | Apple Silicon only, no API key needed, runs on-device |
| `openai` | Set `WHISPER_API_KEY` | OpenAI Whisper API, most accurate |
| `groq` | Set `WHISPER_API_KEY` | Free tier available, very fast |
| (empty) | - | Voice messages disabled |

---

## Security Notes

- **Auth**: Only Telegram user IDs in `ALLOWED_USER_IDS` can use the bot
- **Group lock**: Optionally restrict to one group via `TELEGRAM_GROUP_ID`
- **File uploads**: Sanitized filenames, path traversal protection, symlink detection
- **Permissions**: The bot runs Claude with `--dangerously-skip-permissions` so it can operate autonomously from mobile. If you want approval prompts, remove that flag (but then you can't approve from Telegram)
- **Token safety**: httpx logging is suppressed to prevent bot token appearing in logs

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Claude CLI not found" | Make sure `claude` is in PATH. Check with `which claude`. Add its directory to the LaunchAgent's PATH env var. |
| Bot doesn't respond | Check `logs/stderr.log` for errors |
| "Another bot instance running" | Only one instance can poll the same bot token. Stop the other one. |
| Session resume fails | Normal. The bot auto-retries as a new session. Use `/new` to force reset. |
| Voice not working | Check `WHISPER_PROVIDER` in `.env`. For `local`, you need Apple Silicon + mlx-whisper. |
| Responses cut off | Telegram has a 4096 char limit. The bot splits long messages with `[1/N]` prefixes. |
| Bot keeps restarting | Check logs. If it's a Conflict error, another instance is running. `launchctl list \| grep claude` to find it. |

---

## Architecture Decisions & Lessons Learned

1. **No Claude Agent SDK**: The Python Agent SDK uses `anyio` which conflicts with `python-telegram-bot`'s event loop. Pure subprocess with `asyncio` is the way.

2. **stream-json over plain text**: Streaming lets you edit the Telegram message in real-time instead of waiting for the full response. Worth the protocol complexity.

3. **Entity-based formatting over MarkdownV2**: Telegram's MarkdownV2 parse mode is extremely brittle (unescaped characters crash sends). `telegramify-markdown` converts to entities, which never have parse errors.

4. **Atomic session writes**: Writing to `.tmp` then renaming prevents corruption if the bot crashes mid-write.

5. **Per-topic locks**: Without these, sending two messages quickly to the same topic would start two Claude processes on the same session, causing conflicts.

6. **1MB stdout buffer**: Claude's initialization message is huge (contains the system prompt). The default 64KB asyncio buffer overflows and hangs the process.

---

Built with Claude Code. Works on macOS and Linux.
