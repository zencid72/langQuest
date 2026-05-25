"""Input node — captures raw player text for the DM decision node."""
import os

from state.game_state import GameState


def detect_dm() -> tuple[str, str]:
    """Return (provider_id, display_label) for the active DM. Call at startup."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "claude", "Claude Haiku DM (Anthropic)"
    if os.getenv("OPENAI_API_KEY"):
        return "openai", "GPT-4o-mini DM (OpenAI)"
    return "none", "Pattern Matching — no AI key found"


# Meta-commands bypass the AI entirely — they always work and cost no tokens.
_META_COMMANDS = {"xray", "x", "/x", "/xray", "quit", "exit", "q", "bye", ":q", "help", "h", "?"}


def input_node(state: GameState) -> dict:
    raw = state.get("last_player_input", "").strip()
    normalized = raw.lower()

    if not normalized:
        return {
            "raw_player_input": raw,
            "last_player_input": normalized,
            "dm_heard": "",
            "dm_reason": "",
            "dm_clarification": "",
            "question_topic": "",
            "question_answered": False,
            "question_answer_source": "",
            "question_lore_chunks_used": 0,
            "free_action": "",
            "free_action_resolved": False,
        }

    # Meta-commands pass through unchanged. The DM node also bypasses these.
    if normalized in _META_COMMANDS:
        return {
            "raw_player_input": raw,
            "last_player_input": normalized,
            "dm_heard": "",
            "dm_reason": "",
            "dm_clarification": "",
            "question_topic": "",
            "question_answered": False,
            "question_answer_source": "",
            "question_lore_chunks_used": 0,
            "free_action": "",
            "free_action_resolved": False,
        }

    return {
        "raw_player_input": raw,
        "last_player_input": normalized,
        "dm_heard": "",
        "dm_reason": "",
        "dm_clarification": "",
        "question_topic": "",
        "question_answered": False,
        "question_answer_source": "",
        "question_lore_chunks_used": 0,
        "free_action": "",
        "free_action_resolved": False,
    }
