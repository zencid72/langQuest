"""LangChain/LangGraph concept definitions — one per game area."""

CONCEPTS = {
    "state_management": {
        "name": "State Management",
        "level": 1,
        "location": "village_square",
        "description": (
            "State is what the graph remembers between nodes. "
            "Your player IS a state object moving through the graph. "
            "Health, location, words used — all of it lives in state."
        ),
        "mastery_condition": "Player explores all three areas of level 1",
        "xray_label": "STATE",
    },
    "nodes": {
        "name": "Nodes",
        "level": 3,
        "location": "wizard_tower",
        "description": (
            "A node is a function that takes state and returns updates. "
            "One job. No more. The rules_node sets outcomes. "
            "The display_node renders. They never talk to each other directly."
        ),
        "mastery_condition": "Player understands each location is a node with one job",
        "xray_label": "NODES",
    },
    "retrieval": {
        "name": "Retrieval (RAG)",
        "level": 2,
        "location": "library",
        "description": (
            "RAG: Retrieve relevant context, Augment the prompt, Generate the response. "
            "The well is a retrieval system in miniature. "
            "In V4, every turn will search world memory for relevant context."
        ),
        "mastery_condition": "Player interacts with the memory retrieval system",
        "xray_label": "RAG",
    },
    "edges": {
        "name": "Conditional Edges",
        "level": 4,
        "location": "crossroads",
        "description": (
            "Edges route state between nodes. Conditional edges make decisions: "
            "if health < 20, route to death node. If prompt efficient, route to reward. "
            "The path you take IS the edge being evaluated."
        ),
        "mastery_condition": "Player navigates the crossroads",
        "xray_label": "EDGES",
    },
    "prompt_engineering": {
        "name": "Prompt Engineering",
        "level": 6,
        "location": "prompt_goblin_lair",
        "description": (
            "Vague prompts cost more tokens. Specific prompts cost less. "
            "The Prompt Goblin feeds on wasted words. "
            "Precision is not just efficient — it is power."
        ),
        "mastery_condition": "Player defeats the Prompt Goblin with efficient prompts",
        "xray_label": "PROMPTS",
    },
    "tracing": {
        "name": "LangSmith Tracing",
        "level": 7,
        "location": "observatory",
        "description": (
            "LangSmith records every node, every edge, every token. "
            "You can replay any run and see what the model was thinking. "
            "X-Ray mode is a simplified version of this."
        ),
        "mastery_condition": "Player reads a LangSmith trace in the Observatory",
        "xray_label": "TRACES",
    },
}

LOCATION_CONCEPTS = {
    "village_square": "state_management",
    "tavern": "nodes",
    "well": "retrieval",
}


def get_concept(key: str) -> dict:
    return CONCEPTS.get(key, {})


def concept_for_location(location: str) -> str:
    return LOCATION_CONCEPTS.get(location, "state_management")
