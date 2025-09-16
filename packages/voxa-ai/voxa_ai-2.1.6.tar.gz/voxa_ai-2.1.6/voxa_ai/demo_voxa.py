# voxa_ai/demo_voxa.py
from voxa_ai.agent import run_agent
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
import sys, os

console = Console()

def main():
    console.clear()
    welcome_panel = Panel(
        Align.center("✨ Welcome to Voxa AI - Hybrid Business Assistant ✨", vertical="middle"),
        style="bright_blue",
        padding=(2, 8),
        border_style="bright_blue"
    )
    console.print(Align.center(welcome_panel))

    while True:
        key_input = console.input(
            "\n[bold white]🔑 Press Enter for offline mode, or enter your OpenAI API key for GPT mode (type 'exit' to quit):[/bold white]\n>>> "
        ).strip()

        if key_input.lower() == "exit":
            bye_panel = Panel(
                Align.center("👋 Exiting Voxa AI. Goodbye!", vertical="middle"),
                style="bright_cyan",
                padding=(2, 8),
                border_style="bright_cyan"
            )
            console.print(Align.center(bye_panel))
            sys.exit(0)

        if not key_input:
            offline_panel = Panel(
                Align.center("⚠️ Voxa AI is now running in OFFLINE MODE. Answers come from local database.", vertical="middle"),
                style="yellow",
                padding=(2, 8),
                border_style="yellow"
            )
            console.print(Align.center(offline_panel))
            break
        else:
            os.environ["OPENAI_API_KEY"] = key_input
            valid_panel = Panel(
                Align.center("✅ Your API key is VALID. GPT mode ENABLED!", vertical="middle"),
                style="green",
                padding=(2, 8),
                border_style="green"
            )
            console.print(Align.center(valid_panel))
            break

    while True:
        query = console.input("\n[bold white]💬 Your Question › [/bold white]").strip()
        if query.lower() == "exit":
            goodbye_panel = Panel(
                Align.center("👋 Thank you for using Voxa AI! Goodbye!", vertical="middle"),
                style="bright_cyan",
                padding=(2, 8),
                border_style="bright_cyan"
            )
            console.print(Align.center(goodbye_panel))
            break

        run_agent(query)

if __name__ == "__main__":
    main()
