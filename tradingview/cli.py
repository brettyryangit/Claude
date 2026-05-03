#!/usr/bin/env python3
"""
Interactive CLI for the TradingView + Claude integration.

Usage:
    python cli.py

Commands you can type:
    add rsi                  → start tracking RSI
    add macd                 → start tracking MACD
    remove rsi               → stop tracking RSI
    list indicators          → show active indicators
    list symbols             → show symbols with data
    pine script              → generate TradingView Pine Script template
    analyze BTCUSDT          → ask Claude to check for divergence
    help                     → show this list
    exit / quit              → exit
    <anything else>          → sent directly to Claude as a message
"""

import asyncio
import os
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

import analyzer
import indicators as ind_manager
import store

console = Console()

COMMANDS = {
    "add": "add <indicator>  — start tracking an indicator",
    "remove": "remove <indicator>  — stop tracking an indicator",
    "list indicators": "list indicators  — show active indicators",
    "list symbols": "list symbols  — show symbols with stored data",
    "pine script": "pine script  — generate TradingView Pine Script webhook template",
    "analyze": "analyze <SYMBOL>  — run Claude divergence analysis",
    "help": "help  — show this help",
    "exit": "exit / quit  — exit the program",
}


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]TradingView + Claude[/bold cyan]\n"
        "[dim]Type [bold]help[/bold] for available commands[/dim]",
        border_style="cyan",
    ))


def print_help():
    console.print("\n[bold]Available commands:[/bold]")
    for desc in COMMANDS.values():
        console.print(f"  [cyan]{desc}[/cyan]")
    console.print()


async def handle_command(user_input: str, history: list[dict]) -> list[dict]:
    cmd = user_input.strip().lower()

    # --- add indicator ---
    if cmd.startswith("add "):
        name = user_input[4:].strip()
        ok, msg = ind_manager.add_indicator(name)
        style = "green" if ok else "yellow"
        console.print(f"[{style}]{msg}[/{style}]")
        if ok:
            console.print(
                "[dim]Remember to update your TradingView Pine Script to send this field.[/dim]"
            )
        return history

    # --- remove indicator ---
    if cmd.startswith("remove "):
        name = user_input[7:].strip()
        ok, msg = ind_manager.remove_indicator(name)
        style = "green" if ok else "yellow"
        console.print(f"[{style}]{msg}[/{style}]")
        return history

    # --- list indicators ---
    if cmd in ("list indicators", "indicators"):
        console.print(ind_manager.list_indicators())
        return history

    # --- list symbols ---
    if cmd in ("list symbols", "symbols"):
        symbols = await store.get_symbols()
        if not symbols:
            console.print("[yellow]No data stored yet. Start your webhook server and configure TradingView alerts.[/yellow]")
        else:
            for s in symbols:
                count = await store.get_candle_count(s)
                console.print(f"  [cyan]{s}[/cyan]  ({count} candles)")
        return history

    # --- pine script ---
    if cmd in ("pine script", "pinescript", "pine"):
        script = ind_manager.pine_script_template()
        console.print(Panel(script, title="[bold]Pine Script Template[/bold]", border_style="magenta"))
        return history

    # --- analyze ---
    if cmd.startswith("analyze"):
        parts = user_input.split()
        if len(parts) < 2:
            console.print("[yellow]Usage: analyze <SYMBOL>  e.g. analyze BTCUSDT[/yellow]")
            return history
        symbol = parts[1].upper()
        message = f"Please analyze {symbol} for bullish or bearish divergence using all available indicator data."
        return await _ask_claude(message, history)

    # --- help ---
    if cmd == "help":
        print_help()
        return history

    # --- exit ---
    if cmd in ("exit", "quit", "q"):
        console.print("[dim]Goodbye.[/dim]")
        sys.exit(0)

    # --- pass-through to Claude ---
    if user_input.strip():
        return await _ask_claude(user_input, history)

    return history


async def _ask_claude(message: str, history: list[dict]) -> list[dict]:
    console.print("[dim]Claude is thinking...[/dim]")
    try:
        response = await analyzer.analyze(message, history)
    except Exception as e:
        console.print(f"[red]Error calling Claude: {e}[/red]")
        return history

    # Update history
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ]

    console.print()
    console.print(Panel(
        Markdown(response),
        title="[bold green]Claude[/bold green]",
        border_style="green",
    ))
    console.print()
    return history


async def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable is not set.[/red]")
        console.print("Export it with:  export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    await store.init_db()
    print_banner()
    print_help()

    history: list[dict] = []

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        history = await handle_command(user_input, history)


if __name__ == "__main__":
    asyncio.run(main())
