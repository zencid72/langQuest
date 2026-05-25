"""X-Ray mode — renders the state object and graph internals to the terminal."""
from rich.console import Console
from rich.panel import Panel

from state.game_state import GameState

# Finnish ↔ English concept labels shown in X-Ray
CONCEPT_LABELS = {
    "tila":   "tila  (state)",
    "solmu":  "solmu (node)",
    "haku":   "haku  (retrieval / RAG)",
    "kaari":  "kaari (edge)",
    "muisti": "muisti (memory / state persistence)",
    "kehote": "kehote (prompt engineering)",
    "jäljitys": "jäljitys (tracing)",
    # legacy keys
    "state_management": "tila  (state)",
    "nodes":            "solmu (node)",
    "retrieval":        "haku  (retrieval / RAG)",
    "edges":            "kaari (edge)",
    "prompt_engineering": "kehote (prompt engineering)",
    "tracing":          "jäljitys (tracing)",
}


def render_xray(state: GameState, console: Console) -> None:
    profile = state.get("player_profile", {})
    events = state.get("session_events", [])
    legal = state.get("legal_outcomes", [])
    retrieved = state.get("retrieved_context", [])
    budget = state.get("token_budget", 0)
    spent = state.get("tokens_spent_session", 0)
    remaining = max(0, budget - spent)
    raw_concept = state.get("current_concept", "unknown")
    concept_label = CONCEPT_LABELS.get(raw_concept, raw_concept)

    lines = [
        f"[bold yellow]SOLMU (node):[/bold yellow]      [cyan]input → analyst → rag → dm → rules → answer → narrative → display[/cyan]",
        f"[bold yellow]KÄSITE (concept):[/bold yellow]  [cyan]{concept_label}[/cyan]",
        "",
        "[bold yellow]TILA — STATE SNAPSHOT:[/bold yellow]",
        f"  player_name        [white]{state.get('player_name', '?')}[/white]",
        f"  current_location   [white]{state.get('current_location', '?')}[/white]",
        f"  current_encounter  [white]{state.get('current_encounter', None) or 'none'}[/white]",
        f"  health             [white]{profile.get('health', 100)}[/white]",
        f"  attitude_score     [white]{profile.get('attitude_score', 0)}[/white]",
        f"  curiosity_score    [white]{profile.get('curiosity_score', 0)}[/white]",
        f"  token_budget       [white]{budget:,}[/white]",
        f"  tokens_remaining   [white]{remaining:,}[/white]",
        f"  tokens_spent_ai    [white]{spent:,}[/white]",
        f"  tokens_earned      [white]{state.get('tokens_earned_session', 0):,}[/white]",
        f"  xray_mode          [white]True[/white]",
        f"  session_events     [white]{len(events)} logged[/white]",
        f"  action_result      [white]{state.get('action_result', 'none')}[/white]",
        f"  question_answered  [white]{state.get('question_answered', False)}[/white]",
        f"  question_topic     [white]{state.get('question_topic', '') or 'none'}[/white]",
        f"  free_action        [white]{state.get('free_action', '') or 'none'}[/white]",
        f"  free_resolved      [white]{state.get('free_action_resolved', False)}[/white]",
        f"  answer_source      [white]{state.get('question_answer_source', '') or 'none'}[/white]",
        f"  lore_chunks_used   [white]{state.get('question_lore_chunks_used', 0)}[/white]",
        "",
        "[bold yellow]VERKKO — GRAPH:[/bold yellow]",
        "  [dim]syöte → analyysi → haku → dm → sääntö → vastaus → kerronta → näyttö → LOPPU[/dim]",
        "  [dim]input  →  analyst  →  rag  →  dm  →  rules  →  answer  →  narrative  →  display  →  END[/dim]",
        "  [dim]analyst_node: updates attitude, curiosity, caution, and tone penalties[/dim]",
        "  [dim]rag_node: retrieves local PDF lore chunks for context[/dim]",
        "  [dim]dm_node: AI chooses the action; rules_node validates it[/dim]",
        "  [dim]answer_node: AI answers questions and resolves harmless free actions[/dim]",
        "  [dim]narrative_node: AI scene painter for safe scene-setting actions[/dim]",
        "  [dim]V4 adds: muisti-kirjoittaja (memory_writer)[/dim]",
        "",
        "[bold yellow]KAARET — LEGAL EDGES:[/bold yellow]",
        f"  [dim]{', '.join(legal) if legal else 'none set this turn'}[/dim]",
        "",
        "[bold yellow]HAKU — RETRIEVED LORE:[/bold yellow]",
        f"  [dim]{len(retrieved)} chunks from the latest non-meta turn[/dim]",
        *[
            (
                f"  [dim]{item.get('source_kind', 'context')}: "
                f"{item.get('title') or item.get('source', 'unknown')}"
                f"{' p.' + str(item.get('page')) if item.get('page') else ''} "
                f"score={item.get('score', 0)}[/dim]"
            )
            for item in retrieved[:3]
        ],
        "",
        "[bold yellow]AI STATUS:[/bold yellow]",
        "  [dim]DM decision node active when an API key is available.[/dim]",
        "  [dim]Python still owns state changes, inventory, and objectives.[/dim]",
        "",
        "[bold yellow]LANGSMITH:[/bold yellow]",
        "  [dim]Scoped tracing: AI decisions and prompts are traced.[/dim]",
        "  [dim]Pure Python rules and display stay out of global tracing.[/dim]",
        "  [dim]tokens_spent_ai is game accounting from model usage, not LangSmith billing.[/dim]",
    ]

    if events:
        lines += ["", "[bold yellow]TAPAHTUMAT — SESSION EVENTS:[/bold yellow]"]
        for e in events[-5:]:
            lines.append(f"  [dim]· {e}[/dim]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold yellow]⚡ X-RAY / RÖNTGEN MODE[/bold yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))
