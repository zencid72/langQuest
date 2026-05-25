"""RAG node — retrieves relevant lore chunks for the DM decision."""
from state.game_state import GameState
from memory.lore_store import retrieve_lore

_META_COMMANDS = {"xray", "x", "/x", "/xray", "quit", "exit", "q", "bye", ":q", "help", "h", "?"}
_QUESTION_STARTERS = ("who ", "what ", "where ", "when ", "why ", "how ", "do ", "does ", "can ", "is ", "are ")
_ASK_SEARCH_STARTERS = (
    "ask ", "tell me about ", "explain ", "search ", "find ", "look up ",
    "read about ", "study ",
)
_DOC_TERMS = {
    "langquest", "langchain", "langgraph", "langsmith", "node", "nodes",
    "edge", "edges", "state", "graph", "rag", "retrieval", "retrieve",
    "prompt", "runnable", "tool", "parser", "trace", "tracing",
}
_LANGCHAIN_WORLD_TERMS = (
    "LangChain LangGraph LangSmith LangQuest node edge state graph RAG retrieval "
    "prompt runnable tool parser trace token"
)


def _looks_like_info_request(normalized: str) -> bool:
    words = set(normalized.replace("?", " ").split())
    return (
        normalized.endswith("?")
        or normalized.startswith(_QUESTION_STARTERS)
        or normalized.startswith(_ASK_SEARCH_STARTERS)
        or bool(words & _DOC_TERMS)
    )


def _lore_query(state: GameState, query: str, normalized: str) -> str:
    """Add scene intent to short movement commands so lore retrieval has something to grab."""
    location = state.get("current_location", "")
    level = state.get("current_level", 1)
    lower_query = query.lower()
    if any(term in lower_query for term in ("langquest", "langchain", "langgraph", "langsmith")):
        return f"{query} {_LANGCHAIN_WORLD_TERMS}"
    if location == "tavern" and any(term in lower_query for term in ("node", "edge", "state", "rag", "retrieval", "trace", "token")):
        return f"{query} {_LANGCHAIN_WORLD_TERMS}"
    if location == "village_square" and level >= 2 and normalized in {"north", "go north", "road", "north road"}:
        return (
            "ancient archive building sacred tree world tree threshold path "
            "Norse myth Odin Yggdrasil lore"
        )
    if location == "archive_approach" and normalized in {"tree", "go tree", "approach tree", "east"}:
        return "ancient sacred tree world tree Yggdrasil threshold branches roots lore"
    if location == "archive_approach" and normalized in {"building", "archive", "kirjasto", "enter archive"}:
        return "archive library records lore gods legends knowledge scrolls"
    return query


def rag_node(state: GameState) -> dict:
    query = state.get("raw_player_input") or state.get("last_player_input", "")
    normalized = state.get("last_player_input", "").strip().lower()
    if not query or normalized in _META_COMMANDS:
        return {}
    if not _looks_like_info_request(normalized):
        return {"retrieved_context": []}
    query = _lore_query(state, query, normalized)

    try:
        chunks = retrieve_lore(
            query=query,
            location=state.get("current_location", ""),
            k=4,
        )
    except Exception:
        chunks = []

    return {"retrieved_context": chunks}
