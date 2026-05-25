"""ChromaDB vector store wrapper — V4.

Stores world memories as searchable embeddings.
The RAG node queries this every turn to retrieve relevant context.
"""


class WorldMemoryStore:
    """V4 stub. Will wrap ChromaDB collection per world_id."""

    def __init__(self, world_id: str):
        self.world_id = world_id
        self._store: list[dict] = []   # in-memory placeholder

    def add(self, text: str, metadata: dict | None = None) -> None:
        self._store.append({"text": text, "metadata": metadata or {}})

    def search(self, query: str, k: int = 3) -> list[dict]:
        """V4: Will use cosine similarity against embedded query. V1: returns nothing."""
        return []

    def count(self) -> int:
        return len(self._store)
