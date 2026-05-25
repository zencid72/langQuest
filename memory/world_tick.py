"""World tick — lightweight background process that runs between sessions — V6.

While the player is offline:
- NPCs move and change based on their goals
- World events progress
- NPCs react to player absence (worried, moved on, left something)

Player returns to a world that kept going.
"""
import asyncio


async def world_tick(world_id: str, world_bible: dict, npcs: dict) -> dict:
    """V6 stub. Will run as an async background process."""
    # Future: iterate NPC goals, advance world state, log events
    return {"tick_events": [], "npc_updates": {}}


def schedule_tick(world_id: str) -> None:
    """V6 stub. Will schedule world_tick to run on a timer."""
    pass
