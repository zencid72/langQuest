"""LangQuest — The Learning Dungeon. Entry point."""
import os
import sys
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.rule import Rule

load_dotenv()

from ai.tracing import configure_scoped_tracing, invoke_without_tracing

configure_scoped_tracing()

from state.game_state import GameState, create_initial_state
from graph.graph_builder import build_graph
from graph.nodes.input_node import detect_dm
from memory.lore_store import warm_lore_index
from ui.terminal import show_title, show_loading, show_world_intro, show_farewell

console = Console()


def get_player_name() -> str:
    console.print(Panel(
        "[bold]What is your name, traveler?[/bold]\n\n"
        "[dim]In this world, you are the [italic]tila[/italic] — the state object.\n"
        "Your name travels with you through every node, every edge, every world.\n\n"
        "Press [cyan]Enter[/cyan] to be [bold cyan]Tila[/bold cyan] (Finnish: [italic]state[/italic])[/dim]",
        border_style="cyan",
        padding=(1, 2),
    ))
    name = console.input("[bold cyan]> [/bold cyan]").strip()
    return name if name else "Tila"


def main() -> None:
    show_title(console)
    _, dm_display = detect_dm()
    show_world_intro(dm_display, console)
    player_name = get_player_name()

    console.print()
    show_loading(player_name, console)
    time.sleep(1.2)

    app = build_graph()
    warm_lore_index()
    state = create_initial_state(player_name=player_name)

    # First look — show the opening room without prompting for input
    state["last_player_input"] = "look"
    state = invoke_without_tracing(app.invoke, state)

    # ── Main game loop ────────────────────────────────────────────────────────
    while not state.get("quit", False):
        try:
            raw = console.input("\n[bold green]>[/bold green] ").strip()
            if not raw:
                continue
            state["last_player_input"] = raw
            state = invoke_without_tracing(app.invoke, state)

        except KeyboardInterrupt:
            console.print("\n[dim]The world holds its breath...[/dim]")
            break
        except EOFError:
            break

    if not state.get("game_over", False):
        show_farewell(console)


if __name__ == "__main__":
    main()
