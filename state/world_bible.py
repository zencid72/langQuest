from pydantic import BaseModel, Field
from typing import Dict, List


class WorldBible(BaseModel):
    world_id: str
    world_name: str
    tone: str = "epic fantasy with a knowing wink"
    currency_name: str = "tokens"
    core_conflict: str = "The Prompt Goblin grows fat on wasted words"

    named_locations: Dict[str, str] = Field(default_factory=dict)
    named_characters: Dict[str, str] = Field(default_factory=dict)
    established_facts: List[str] = Field(default_factory=list)
    player_reputation: Dict[str, int] = Field(default_factory=dict)

    locations_named_by_player: List[str] = Field(default_factory=list)
    characters_created_by_player: List[str] = Field(default_factory=list)
    lore_written_by_player: List[str] = Field(default_factory=list)


def default_fantasy_bible(world_id: str) -> WorldBible:
    return WorldBible(
        world_id=world_id,
        world_name="Thornhaven",
        tone="epic fantasy with a knowing wink",
        currency_name="tokens",
        core_conflict="The Prompt Goblin grows fat on wasted words",
        named_locations={
            "village_square": "The heart of Thornhaven, where all journeys begin",
            "tavern": "The Wandering Node — warmth, ale, and dangerous knowledge",
            "well": "The Old Well — deeper than it looks, full of retrieved wisdom",
            "north_road": "The road into Thornwood — seven levels wait beyond the trees",
        },
        named_characters={
            "mira": "Mira the innkeeper — knows more than she lets on",
        },
        established_facts=[
            "Tokens are the currency of this world and of language models",
            "The Prompt Goblin lives in the deepest level, growing fat on wasted words",
            "Precision is power — vague prompts cost more than specific ones",
            "The world is a graph. Every location is a node. Every path is an edge.",
        ],
    )
