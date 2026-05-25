"""Encounter and rules logic for LangQuest.

V1: Pure Python rules only. No AI. Sets legal outcomes for each situation.
V5: Prompt Goblin encounter will be added here.
"""
from typing import List


def get_legal_outcomes(location: str, player_profile: dict) -> List[str]:
    """Returns what can legally happen in this location for this player."""
    base_outcomes = {
        "village_square": ["look", "go_tavern", "go_well", "go_north"],
        "tavern": ["look", "talk_mira", "sit", "leave_tavern"],
        "well": ["look", "drop", "leave_well"],
    }
    outcomes = base_outcomes.get(location, ["look", "help"])

    # Future: player profile modifies available options
    # e.g. high curiosity_score unlocks hidden dialogue options
    # e.g. low health prevents certain actions
    # e.g. relationship_score with NPC changes what they say

    return outcomes


class EncounterResult:
    def __init__(self, narrative: str, state_updates: dict, significance: float = 0.0):
        self.narrative = narrative
        self.state_updates = state_updates
        self.significance = significance  # 0.0–1.0, used by memory writer


# V5: Prompt Goblin encounter placeholder
PROMPT_GOBLIN = {
    "name": "The Prompt Goblin",
    "description": (
        "A creature that feeds on wasted tokens. Vague answers make it stronger. "
        "Precise, efficient prompts deal damage. This is prompt engineering made physical."
    ),
    "health": 500,
    "weakness": "specificity",
    "location": "level_6_goblin_lair",
    "status": "LOCKED — Coming in V5",
}
