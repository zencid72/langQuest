# Nodes

## What a node is

In LangGraph, a **node** is a Python function. It takes the current state and returns a dict of updates.

```python
def my_node(state: GameState) -> dict:
    # read from state
    player_name = state["player_name"]
    
    # do one job
    result = do_something(player_name)
    
    # return what changed
    return {"narrative_response": result}
```

That's it. A function. One job.

## The single responsibility rule

Each node does **one thing**:
- `input_node` — normalizes raw player text
- `rules_node` — applies Python logic, sets legal outcomes
- `display_node` — renders the terminal UI
- `analyst_node` — reads player behavior, updates profile
- `dm_node` — narrates the outcome the AI chose

A node that does two jobs is two nodes waiting to happen.

## How nodes see the world

Every node receives the **complete current state**. It can read any field. But it only returns what it changed — LangGraph merges the update into the running state.

This means nodes are loosely coupled. `rules_node` doesn't need to know `display_node` exists. They communicate through state.

## In LangQuest

Every location in the game is a node. The village square. The tavern. The well.

When you walk from the square to the tavern, you are:
1. Triggering a conditional edge
2. Entering a new node
3. Receiving a new state update

The world is the graph. You are the state.
