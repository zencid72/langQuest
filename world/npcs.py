"""NPC definitions and management for LangQuest."""
from pydantic import BaseModel, Field
from typing import List, Dict


class NPCProfile(BaseModel):
    name: str
    base_personality: str
    relationship_score: int = 0   # -100 to +100
    trust_level: int = 50
    interactions: List[str] = Field(default_factory=list)
    promises_player_made: List[str] = Field(default_factory=list)
    gifts_received: List[str] = Field(default_factory=list)
    location_history: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    current_situation: str = ""


STARTING_NPCS: Dict[str, NPCProfile] = {
    "mira": NPCProfile(
        name="Mira",
        base_personality=(
            "Dry wit. Seen everything. Quietly rooting for you. "
            "Knows the seven levels better than anyone still alive."
        ),
        relationship_score=0,
        trust_level=40,
        location_history=["tavern"],
        goals=[
            "Keep the Wandering Node running",
            "Warn travelers before they run north unprepared",
            "Secretly collect information about the Prompt Goblin",
        ],
        current_situation="Polishing glasses. Watching. Waiting for someone worth talking to.",
    ),
}


def get_npc(name: str) -> NPCProfile | None:
    return STARTING_NPCS.get(name.lower())


def npc_reaction(npc_name: str, player_profile: dict, context: str) -> str:
    """V1 stub — returns static dialogue. V2 will use AI based on relationship score."""
    npc = get_npc(npc_name)
    if not npc:
        return "No one by that name is here."

    attitude = player_profile.get("attitude_score", 0)
    caution = player_profile.get("caution_score", 0)

    if npc_name == "mira":
        if attitude < -5:
            return (
                "Mira eyes you warily. \"Careful with that energy. "
                "The Goblin likes angry travelers. Easier to waste their tokens.\""
            )
        elif caution > 5:
            return (
                "Mira nods approvingly. \"You're the careful type. Good. "
                "The road north has eaten plenty of the reckless ones.\""
            )
        else:
            return (
                "Mira gives you the look she reserves for people who might actually make it. "
                "\"You've got potential. Don't waste it on vague questions.\""
            )

    return f"{npc.name} is here but says nothing useful. Yet."
