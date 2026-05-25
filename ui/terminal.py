"""Rich terminal UI components for LangQuest."""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.rule import Rule

console = Console()

TITLE_ART = r"""
  _                              ___                  _
 | |    __ _ _ __   __ _        / _ \ _   _  ___  ___| |_
 | |   / _` | '_ \ / _` |_____ | | | | | | |/ _ \/ __| __|
 | |__| (_| | | | | (_| |_____|| |_| | |_| |  __/\__ \ |_
 |_____\__,_|_| |_|\__, |       \__\_\\__,_|\___||___/\__|
                   |___/
"""


def show_title(con: Console = console) -> None:
    con.clear()
    con.print()
    con.print(Align.center(Text(TITLE_ART.strip(), style="bold magenta")))
    con.print()
    con.print(Align.center(Rule(style="dim magenta")))
    con.print()
    con.print(Align.center(Panel(
        "[dim]A terminal RPG where YOU are the state object.\n"
        "Every room teaches. Every token matters.\n"
        "The world is a graph. You are moving through it.[/dim]\n\n"
        "[dim]  [cyan]tila[/cyan] = state  ·  [cyan]solmu[/cyan] = node  ·  "
        "[cyan]kaari[/cyan] = edge  ·  [cyan]verkko[/cyan] = graph[/dim]",
        border_style="dim magenta",
        padding=(1, 4),
    )))
    con.print()


def show_loading(player_name: str, con: Console = console) -> None:
    con.print(Panel(
        f"[bold green]Welcome, {player_name}.[/bold green]\n\n"
        "[dim]Compiling you into existence...\n"
        "Initializing state object...\n"
        "Building the graph...\n"
        "Populating Thornhaven...[/dim]\n\n"
        "[cyan]Ready.[/cyan]",
        border_style="green",
        padding=(1, 2),
    ))


def show_world_intro(dm_display: str, con: Console = console) -> None:
    con.print(Panel(
        "[bold]The World Structure[/bold]\n\n"
        "You are playing inside a [cyan]LangGraph[/cyan] — a directed graph of nodes and edges.\n"
        "Every room is a [cyan]solmu[/cyan] (node). Every path is a [cyan]kaari[/cyan] (edge).\n"
        "You are the [cyan]tila[/cyan] — the state object. Your choices travel with you.\n\n"
        "  [cyan]tila[/cyan]   (state)      — you. Your history, choices, and knowledge.\n"
        "  [cyan]solmu[/cyan]  (node)       — each room does exactly one job.\n"
        "  [cyan]kaari[/cyan]  (edge)       — the paths between rooms.\n"
        "  [cyan]haku[/cyan]   (retrieval)  — fetching knowledge from memory. RAG.\n"
        "  [cyan]verkko[/cyan] (graph)      — the whole world, wired together.\n\n"
        "[bold]The Dungeon Master[/bold]\n\n"
        "The DM is an AI. Before every response it reads your full [italic]tila[/italic] — "
        "where you've been, who you've spoken to, what you know.\n"
        "It interprets what you type in plain language and maps it to what happens in the world.\n\n"
        f"  [dim]Active DM: [cyan]{dm_display}[/cyan][/dim]\n\n"
        "[bold]Tokens[/bold]\n\n"
        "Tokens are the currency of attention here. Every word you send to the DM "
        "can cost [yellow]tokens[/yellow]. Every word it sends back can cost tokens.\n"
        "Vague questions burn more than specific ones. You start with "
        "[bold yellow]5,000[/bold yellow], and Thornhaven holds ways to earn more.\n\n"
        "  [dim]'what do I do?'      → ~400 tokens  (model guesses, hedges, asks back)[/dim]\n"
        "  [dim]'talk to mira'       → ~40 tokens   (direct, unambiguous, cheap)[/dim]\n\n"
        "[dim]Press [cyan]Enter[/cyan] to continue...[/dim]",
        title="[bold cyan]How This World Works[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))
    con.input("")


def show_farewell(con: Console = console) -> None:
    con.print()
    con.print(Panel(
        "[bold magenta]Your journey is woven into this world.[/bold magenta]\n"
        "[dim]Return anytime. The world will remember.[/dim]",
        border_style="magenta",
        padding=(1, 2),
    ))
    con.print()
