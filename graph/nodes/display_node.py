"""Display node — renders game state to the terminal using Rich."""
from rich.console import Console
from rich.panel import Panel

from state.game_state import GameState, LEVEL_OBJECTIVES
from world.locations import LOCATIONS, LEVEL_1_COMPLETE_TEXT, LEVEL_2_COMPLETE_TEXT
from learning.xray import render_xray

console = Console()

GAME_OVER_ART = r"""   _____          __  __ ______    ______      ________ _____
  / ____|   /\   |  \/  |  ____|  / __ \ \    / /  ____|  __ \
 | |  __   /  \  | \  / | |__    | |  | \ \  / /| |__  | |__) |
 | | |_ | / /\ \ | |\/| |  __|   | |  | |\ \/ / |  __| |  _  /
 | |__| |/ ____ \| |  | | |____  | |__| | \  /  | |____| | \ \
  \_____/_/    \_\_|  |_|______|  \____/   \/   |______|_|  \_\
"""


def _token_meter(state: GameState) -> str:
    budget = state.get("token_budget", 0)
    spent = state.get("tokens_spent_session", 0)
    remaining = max(0, budget - spent)
    pct = remaining / budget if budget else 0

    bar_width = 38
    filled = int(bar_width * pct)
    empty = bar_width - filled

    if pct > 0.6:
        color = "green"
        note = ""
    elif pct > 0.3:
        color = "yellow"
        note = "  [yellow]⚠  Watch your spending[/yellow]"
    else:
        color = "red"
        note = "  [red]⚠⚠ CRITICAL — be precise[/red]"

    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
    return f"[dim]Token Budget[/dim]  {bar}  [{color}]{remaining:,}[/{color}][dim] / {budget:,}[/dim]{note}"


def _objective_tracker(state: GameState) -> str | None:
    level = state.get("current_level", 1)
    location = state.get("current_location", "")
    objectives = state.get("completed_objectives", [])

    if level == 1 and location in ("village_square", "tavern", "well"):
        required = LEVEL_OBJECTIVES[1]
        labels = {"talked_to_mira": "Mira", "visited_kaivo": "Kaivo", "used_xray": "X-Ray"}
        parts = []
        for key in required:
            label = labels.get(key, key)
            parts.append(f"[green]✓ {label}[/green]" if key in objectives else f"[dim]○ {label}[/dim]")
        count = sum(1 for k in required if k in objectives)
        return f"[dim]Level 1:[/dim]  {'  ·  '.join(parts)}  [dim]({count}/3 — go [cyan]north[/cyan] when done)[/dim]"

    if level == 2 and location in ("archive_approach", "tree_exterior", "tree_interior", "tunnel_right", "tunnel_left"):
        required = LEVEL_OBJECTIVES[2]
        labels = {"found_key": "Key", "opened_chest": "Chest"}
        parts = []
        for key in required:
            label = labels.get(key, key)
            parts.append(f"[green]✓ {label}[/green]" if key in objectives else f"[dim]○ {label}[/dim]")
        count = sum(1 for k in required if k in objectives)
        return f"[dim]Level 2:[/dim]  {'  ·  '.join(parts)}  [dim]({count}/2 — find the key, open the chest)[/dim]"

    return None


def _location_name(state: GameState) -> str:
    key = state.get("current_location", "village_square")
    return LOCATIONS.get(key, {}).get("name", key.replace("_", " ").title())


def _hints(state: GameState) -> str:
    loc = state.get("current_location", "village_square")
    objectives = state.get("completed_objectives", [])
    xray_needed = "used_xray" not in objectives and state.get("current_level", 1) == 1

    # Xray hint is bright when it's still an outstanding Level 1 objective
    xray_hint = "[bold cyan]xray[/bold cyan]" if xray_needed else "[dim]xray[/dim]"

    has_key = "found_key" in objectives

    hint_map = {
        "village_square": f"look  ·  well  ·  tavern  ·  north  ·  {xray_hint}  ·  [dim]help · quit[/dim]",
        "tavern":         f"look  ·  mira  ·  ask tokens  ·  sit  ·  leave  ·  {xray_hint}  ·  [dim]help[/dim]",
        "well":           f"look  ·  drop  ·  back  ·  {xray_hint}  ·  [dim]help[/dim]",
        "archive_approach": "look  ·  building  ·  tree  ·  south  ·  [dim]xray · help[/dim]",
        "kirjasto":       f"aino  ·  catalog  ·  search <topic>  ·  read  ·  outside  ·  [dim]south · xray · help[/dim]",
        "tree_exterior":  "look  ·  open door  ·  back  ·  [dim]xray · help[/dim]",
        "tree_interior":  "right  ·  left  ·  look  ·  back  ·  [dim]xray · help[/dim]",
        "tunnel_right":   f"look  ·  {'open chest' if not has_key else '[bold cyan]open chest[/bold cyan]'}  ·  back  ·  [dim]xray · help[/dim]",
        "tunnel_left":    f"look  ·  {'[bold cyan]examine floor[/bold cyan]' if not has_key else 'examine floor'}  ·  back  ·  [dim]xray · help[/dim]",
    }
    return hint_map.get(loc, f"look  ·  {xray_hint}  ·  [dim]help · quit[/dim]")


def display_node(state: GameState) -> dict:
    if state.get("quit", False):
        return {}

    narrative = state.get("narrative_response", "")
    xray_mode = state.get("xray_mode", False)
    budget_discovered = state.get("token_budget_discovered", False)
    budget = state.get("token_budget", 0)
    spent = state.get("tokens_spent_session", 0)
    tokens_depleted = budget_discovered and budget > 0 and spent >= budget

    console.print()
    console.print(f"  {_token_meter(state)}")

    # Objective tracker (Level 1 only)
    tracker = _objective_tracker(state)
    if tracker:
        console.print(f"  {tracker}")

    console.print()

    # Level completion banner — shown once on the turn the level completes
    if state.get("level_just_completed", False):
        prev_level = state.get("current_level", 2) - 1
        banner = LEVEL_2_COMPLETE_TEXT if prev_level == 2 else LEVEL_1_COMPLETE_TEXT
        console.print(Panel(banner, border_style="bold green", padding=(0, 2)))
        console.print()

    if narrative:
        console.print(Panel(
            narrative,
            title=f"[bold]{_location_name(state)}[/bold]",
            border_style="cyan",
            padding=(1, 2),
        ))

    if xray_mode:
        render_xray(state, console)

    if tokens_depleted:
        console.print()
        console.print(Panel(
            GAME_OVER_ART.rstrip()
            + "\n\n[bold red]Your token budget is gone.[/bold red]\n"
            "[dim]The DM reaches for a word and finds only silence. "
            "The graph has no currency left to cross its next edge.[/dim]",
            title="[bold red]TOKEN BUDGET DEPLETED[/bold red]",
            border_style="red",
            padding=(1, 2),
        ))
        return {"quit": True, "game_over": True, "action_result": "game_over"}

    dm_heard = state.get("dm_heard", "")
    if dm_heard:
        console.print(f"  [dim]DM heard: [cyan]{dm_heard}[/cyan][/dim]")

    console.print(f"\n  [dim]Try: {_hints(state)}[/dim]")

    return {}


def state_update_node(state: GameState) -> dict:
    """V2: Updates all state objects after DM decision."""
    return {}


def memory_writer_node(state: GameState) -> dict:
    """V4: Writes significant events to ChromaDB vector store."""
    return {}


def bible_writer_node(state: GameState) -> dict:
    """V4: Writes named things and facts to the world bible SQLite."""
    return {}
