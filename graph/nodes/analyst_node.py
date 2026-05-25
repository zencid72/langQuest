"""Analyst node — deterministic player signal tracking.

This is intentionally pure Python. It should update game state, but it should
not create LangSmith traces because it is not an AI/RAG operation.
"""
import json
import re
from pathlib import Path

from state.game_state import GameState

_ROOT = Path(__file__).resolve().parents[2]
_LEXICON_PATH = _ROOT / "data" / "player_signal_words.json"
_WORD_RE = re.compile(r"[a-zA-Z']+")
_META_COMMANDS = {"xray", "x", "/x", "/xray", "quit", "exit", "q", "bye", ":q"}


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _load_lexicon() -> dict:
    fallback = {
        "positive_words": ["please", "thanks", "thank", "kindly", "hello", "hi", "friend"],
        "negative_words": ["stupid", "idiot", "hate", "kill", "attack", "smash", "destroy", "damn"],
        "curiosity_words": ["why", "how", "what", "where", "who", "lore", "explain", "tell", "learn", "study", "inspect", "examine", "search", "read"],
        "cautious_words": ["careful", "slowly", "quietly", "listen", "check", "inspect", "examine"],
        "reckless_words": ["charge", "rush", "force", "smash", "attack", "destroy", "kick"],
    }
    try:
        with _LEXICON_PATH.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        return {**fallback, **loaded}
    except Exception:
        return fallback


def analyze_player_input(raw_input: str, lexicon: dict | None = None) -> dict:
    """Return repeatable behavior deltas for one player utterance."""
    lexicon = lexicon or _load_lexicon()
    normalized = raw_input.strip().lower()
    words = _WORD_RE.findall(normalized)
    word_set = set(words)

    positive = sorted(word_set & set(lexicon.get("positive_words", [])))
    negative = sorted(word_set & set(lexicon.get("negative_words", [])))
    curiosity = sorted(word_set & set(lexicon.get("curiosity_words", [])))
    cautious = sorted(word_set & set(lexicon.get("cautious_words", [])))
    reckless = sorted(word_set & set(lexicon.get("reckless_words", [])))

    is_question = "?" in raw_input or bool(word_set & {"who", "what", "where", "when", "why", "how"})
    attitude_delta = _clamp(len(positive) - len(negative), -2, 2)
    curiosity_delta = _clamp(len(curiosity) + (1 if is_question else 0), 0, 3)
    caution_delta = _clamp(len(cautious) - len(reckless), -2, 2)
    specificity = min(1.0, len(words) / 12)
    token_penalty = len(negative) * int(lexicon.get("negative_token_penalty", 50))

    return {
        "attitude_delta": attitude_delta,
        "curiosity_delta": curiosity_delta,
        "caution_delta": caution_delta,
        "positive_hits": positive,
        "negative_hits": negative,
        "curiosity_hits": curiosity,
        "cautious_hits": cautious,
        "reckless_hits": reckless,
        "words_detected": words[:12],
        "is_question": is_question,
        "specificity": specificity,
        "token_penalty": token_penalty,
    }


def analyst_node(state: GameState) -> dict:
    raw = state.get("raw_player_input") or state.get("last_player_input", "")
    normalized = raw.strip().lower()
    if not raw or normalized in _META_COMMANDS:
        return {}

    signal = analyze_player_input(raw)
    profile = dict(state.get("player_profile", {}))

    words_used = list(profile.get("words_used", []))
    for word in signal["words_detected"]:
        if word not in words_used:
            words_used.append(word)
    words_used = words_used[-60:]

    last_actions = list(profile.get("last_5_actions", []))
    last_actions.append(raw.strip())

    prompt_lengths = last_actions[-10:]
    avg_prompt_length = int(sum(len(action.split()) for action in prompt_lengths) / max(1, len(prompt_lengths)))

    profile.update({
        "attitude_score": _clamp(profile.get("attitude_score", 0) + signal["attitude_delta"], -10, 10),
        "curiosity_score": _clamp(profile.get("curiosity_score", 0) + signal["curiosity_delta"], 0, 30),
        "caution_score": _clamp(profile.get("caution_score", 0) + signal["caution_delta"], -10, 10),
        "words_used": words_used,
        "question_count": profile.get("question_count", 0) + (1 if signal["is_question"] else 0),
        "last_5_actions": last_actions[-5:],
        "avg_prompt_length": avg_prompt_length,
        "specificity_score": signal["specificity"],
    })

    updates = {"player_profile": profile}
    penalty = signal["token_penalty"]
    if penalty and state.get("token_budget_discovered", False):
        updates["tokens_spent_session"] = state.get("tokens_spent_session", 0) + penalty
        updates["session_events"] = [f"Tone penalty: -{penalty} tokens for hostile wording"]

    return updates
