# Tracing with LangSmith

## What LangSmith does

LangSmith records every call your application makes to a language model. It creates a **trace**: a tree of every node, every prompt, every response, every token count.

You can replay any run. See exactly what prompt was sent. See what the model generated. See why it chose what it chose.

## Why tracing matters

Without tracing, debugging an AI app is guesswork. "Why did the DM say that?" You don't know. You can't see inside the model call.

With tracing, you see:
```
Run: game_loop_turn_42
├── input_node         (0ms)
├── analyst_node       (340ms, 89 tokens)
│   ├── prompt: "Analyze player input: 'I attack the goblin'"
│   └── response: {"attitude_delta": -2, "caution_delta": -3}
├── rules_node         (1ms)
├── dm_node            (1,240ms, 412 tokens)
│   ├── prompt: [player profile] + [legal outcomes] + [world memories]
│   └── response: "The goblin snarls..."
└── display_node       (0ms)
```

Every call. Every cost. Every decision.

## In LangQuest

LangSmith is wired around AI work:
- You can see exactly what context the DM received
- You can see which legal outcome it chose and why
- You can see the prompt and output for narrative generation
- You can see PDF lore ingestion and retrieval matches
- You can see the token cost breakdown

The LangSmith Observatory (Level 7) teaches this by putting you inside a trace.

## X-Ray mode is a simplified trace

X-Ray shows a simplified version of what LangSmith would show you — but in the terminal, right now, as it happens.

## Setup

```bash
LANGSMITH_API_KEY=your_key
LANGSMITH_PROJECT=langQuest
# Optional escape hatch for full graph tracing:
# LANGADVENTURE_GLOBAL_TRACING=true
```

LangQuest keeps global tracing off by default. The game traces only explicit
AI/RAG operations: PDF lore ingestion, lore retrieval, DM decisions, and
narrative prompts. When no model is available, local DM routing decisions are
also traced as `ai.dm_local_decision` so command classification remains visible.
