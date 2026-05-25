"""Dungeon Master AI — V2.

Claude Sonnet receives: player profile + legal outcomes + retrieved world memory.
Decides: which legal outcome happens based on who this player IS.
Narrates: what happens, in the world's tone and flavor.

The DM never invents rules. Python sets legal outcomes. AI chooses between them.
"""
from typing import Any


DM_SYSTEM_PROMPT = """You are the Dungeon Master of LangQuest, a game that teaches AI concepts.

You receive:
- The player's profile (attitude, caution, curiosity scores)
- The legal outcomes Python has set for this situation
- Retrieved world memories from previous sessions
- The current world tone and flavor

Your job:
1. Choose ONE of the legal outcomes (don't invent new ones)
2. Narrate what happens in the world's flavor
3. Make the same situation feel different based on who the player is

Aggressive player → the world meets them with edge.
Cautious player → the world gives them space.
Curious player → the world rewards their attention.

Keep responses under 150 words. Be vivid. Be specific.
"""


def call_dm(
    player_profile: dict,
    legal_outcomes: list[str],
    retrieved_context: list[str],
    world_bible: dict,
    player_input: str,
    client: Any = None,
) -> dict:
    """V2 stub. Will call Claude Sonnet and return narrative + chosen outcome."""
    return {
        "narrative": "[V2: DM not yet connected]",
        "chosen_outcome": legal_outcomes[0] if legal_outcomes else "look",
        "tokens_used": 0,
    }
