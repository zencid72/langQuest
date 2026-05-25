"""World builder AI — V3.

Player describes their world in natural language.
This node generates:
- 3 starting locations with descriptions
- 4 NPCs with full backstories
- Core story arc
- How token currency maps to this world's flavor
- What the "Prompt Goblin equivalent" is called
- Tone and flavor rules for the DM

Everything is indexed into the vector store immediately.
"""
from typing import Any


WORLD_BUILDER_PROMPT = """You are building a text adventure world for LangQuest.

The player has described: {player_description}

Generate a JSON world with this structure:
{{
  "world_name": "...",
  "tone": "...",
  "currency_name": "...",  // how tokens appear in this world's flavor
  "goblin_equivalent": "...",  // what the Prompt Goblin is called here
  "core_conflict": "...",
  "locations": [
    {{"name": "...", "key": "...", "description": "...", "concept": "..."}}
  ],
  "npcs": [
    {{"name": "...", "role": "...", "personality": "...", "goals": ["..."]}}
  ],
  "established_facts": ["..."]
}}

The world can be any genre — sci-fi, fantasy, noir, horror, western.
The game structure never changes. Only the costume does.
"""


def call_world_builder(player_description: str, client: Any = None) -> dict:
    """V3 stub. Will call Claude Sonnet and return a generated world."""
    return {
        "world_name": "Thornhaven",
        "tone": "epic fantasy with a knowing wink",
        "status": "V3: World builder not yet connected — using default fantasy world",
    }
