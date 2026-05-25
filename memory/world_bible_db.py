"""SQLite wrapper for the world bible — V4.

Stores hard facts: named locations, characters, established lore.
Only grows, never shrinks.
"""


class WorldBibleDB:
    """V4 stub. Will use SQLite to persist the WorldBible between sessions."""

    def __init__(self, world_id: str):
        self.world_id = world_id

    def save(self, world_bible: dict) -> None:
        pass

    def load(self) -> dict | None:
        return None

    def add_fact(self, fact: str) -> None:
        pass

    def add_location(self, name: str, description: str) -> None:
        pass

    def add_character(self, name: str, description: str) -> None:
        pass
