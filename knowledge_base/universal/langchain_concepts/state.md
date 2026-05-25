# State

## What state is

State is the data object that flows through the graph. Every node reads it. Every node can update it. It's the memory of the running system.

In LangGraph:
```python
from typing import TypedDict, Annotated
import operator

class MyState(TypedDict):
    name: str                                  # plain field: overwrites each update
    events: Annotated[list, operator.add]      # reducer: appends instead of overwrites
    count: int
```

## Reducers

When two branches update the same field, how does LangGraph reconcile them?

**No reducer:** last writer wins. The field is overwritten.  
**With reducer (`operator.add`):** both values are combined. For lists, this means append.

```python
# current state: events = ["login"]
# node returns: {"events": ["action_1"]}
# result: events = ["login", "action_1"]   ← operator.add
```

## In LangQuest

The `GameState` object IS the player. Everything the world knows about you lives in state:

- `player_name` — who you are
- `current_location` — where you are  
- `player_profile` — how you play (attitude, caution, curiosity scores)
- `token_budget` — how much you have left
- `session_events` — what happened this session (uses `operator.add`)
- `xray_mode` — whether you can see the machinery

When you walk into the tavern, `current_location` updates to `"tavern"`. That update propagates to every subsequent node. The world knows where you are because the state knows.

## Why TypedDict

TypedDict gives us:
- Type hints for autocomplete and error checking
- Compatibility with LangGraph's state management
- Clear documentation of what the state contains

Pydantic BaseModel works too, but TypedDict is lighter and LangGraph-native.
