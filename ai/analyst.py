"""Analyst AI — V2.

Claude Haiku reads player input each turn and updates their profile.
Cheap, fast. Runs before the DM call.

Tracks:
- Attitude score (aggressive vs. gentle language)
- Caution score (reckless vs. careful choices)
- Curiosity score (exploration and question behavior)
- Word fingerprint (vocabulary patterns)
- Prompt length and specificity
"""
from typing import Any


ANALYST_SYSTEM_PROMPT = """You are analyzing a player's input in a text adventure game.
Extract behavioral signals from their text.

Return a JSON object with these fields (all optional, only include if detected):
{
  "attitude_delta": -2 to +2 (negative = more aggressive, positive = more gentle),
  "caution_delta": -2 to +2 (negative = more reckless, positive = more cautious),
  "curiosity_delta": -2 to +2 (negative = less curious, positive = more curious),
  "words_detected": ["list", "of", "notable", "words"],
  "is_question": true/false,
  "specificity": 0.0 to 1.0 (how specific and precise the input is)
}

Be conservative. Small deltas. The profile accumulates over many turns.
"""


def call_analyst(player_input: str, client: Any = None) -> dict:
    """V2 stub. Will call Claude Haiku and return profile deltas."""
    return {
        "attitude_delta": 0,
        "caution_delta": 0,
        "curiosity_delta": 0,
        "words_detected": player_input.split()[:5],
        "is_question": "?" in player_input,
        "specificity": min(1.0, len(player_input.split()) / 10),
        "tokens_used": 0,
    }
