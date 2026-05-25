# Edges

## What an edge is

An **edge** connects two nodes. It tells LangGraph where to go next after a node completes.

```python
# Simple edge: always goes from A to B
builder.add_edge("rules_node", "display_node")

# Conditional edge: goes somewhere based on state
builder.add_conditional_edges(
    "rules_node",
    route_after_rules,          # a function that reads state and returns a node name
    {
        "combat": "combat_node",
        "dialogue": "dialogue_node",
        "default": "display_node",
    }
)
```

## The routing function

A conditional edge needs a function that reads state and returns a string key:

```python
def route_after_rules(state: GameState) -> str:
    if state["current_encounter"] == "goblin":
        return "combat"
    if state["action_result"] == "talk":
        return "dialogue"
    return "default"
```

The string it returns maps to a node name in the conditional dict.

## In LangQuest

The path you walk between locations is an edge being evaluated.

Walk into the tavern → conditional edge reads `current_location == "village_square"` and `action_result == "move_tavern"` → routes to the tavern node.

In V1, all edges are simple (always go input → rules → display).  
In V2, the DM node introduces conditional routing based on player profile.  
In V4, the RAG node creates edges based on what memories were retrieved.

The more complex the world, the more sophisticated the edge logic.

## Why this matters

Edges are where decisions live. The AI doesn't choose what happens — **the edges do**. The AI narrates. Python decides.
