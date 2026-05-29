# LangQuest: Architecture

LangQuest is an AI-powered text adventure built entirely on the LangChain ecosystem. Every turn the player takes is a full pass through a compiled LangGraph state machine. This document explains how the pieces fit together.

---

## High-Level Architecture

```
                          ┌─────────────────────────────────────┐
                          │         LANGGRAPH STATE MACHINE     │
                          │                                     │
  Player                  │  ┌──────────┐                       │
  types text ──────────▶  │  │  input   │  Captures raw input,  │
                          │  │  node    │  normalizes it        │
                          │  └────┬─────┘                       │
                          │       │                             │
                          │  ┌────▼─────┐                       │
                          │  │ analyst  │  Pure Python.         │
                          │  │  node    │  Word-lexicon scoring:│
                          │  └────┬─────┘  attitude, curiosity, │
                          │       │        tone, token penalty  │
                          │  ┌────▼─────┐                       │
                          │  │   rag    │  Queries Chroma       │
                          │  │  node    │◀──────────────────────────── Vector DB (Chroma)
                          │  └────┬─────┘  Returns top-k lore   │   
                          │       │        chunks               │
                          │  ┌────▼─────┐                       │
                          │  │   dm     │  LLM interprets       │
                          │  │  node    │◀──────────────────────────── Claude Haiku or GPT-4o-mini
                          │  └────┬─────┘  natural language,    │   
                          │       │        picks legal command  │
                          │  ┌────▼─────┐                       │
                          │  │  rules   │  Pure Python.         │
                          │  │  node    │  Validates command,   │
                          │  └────┬─────┘  updates location,    │
                          │       │        objectives, tokens   │
                          │  ┌────▼─────┐                       │
                          │  │ answer   │  LLM answers in-world │
                          │  │  node    │◀──────────────────────────── LangChain (RAG-grounded)
                          │  └────┬─────┘  questions using      │   
                          │       │        RAG context          │
                          │  ┌────▼─────┐                       │
                          │  │narrative │  LLM scene painter    │
                          │  │  node    │  (Level 2+ only).     │
                          │  └────┬─────┘  Enhances skeleton    │
                          │       │        with atmosphere      │
                          │  ┌────▼─────┐                       │
                          │  │ display  │  Rich terminal        │
                          │  │  node    │  renderer             │
                          │  └────┬─────┘                       │
                          └───────┼─────────────────────────────┘
                                  │
                          Text rendered to terminal
                                  │
                          ┌───────▼─────────────────────────────┐
                          │            LANGSMITH                │
                          │  Scoped traces on every AI call:    │
                          │  dm_decision · in_world_answer      │
                          │  free_action · narrative_painter    │
                          │  lore_ingest · lore_retrieve        │
                          └─────────────────────────────────────┘
```

---

## LangGraph — The Game Loop

The entire turn cycle is a compiled `StateGraph` from `langgraph`. Each node is a plain Python function that receives the current `GameState` and returns a partial update dict. LangGraph merges those updates back into state before passing it to the next node.

```
input → analyst → rag → dm → rules → answer → narrative → display → END
```

The graph is compiled once at startup (`build_graph()`) and invoked on every player turn with the accumulated state object. Fields typed as `Annotated[list, operator.add]` (such as `messages` and `session_events`) append across nodes rather than overwrite.

**File:** [graph/graph_builder.py](graph/graph_builder.py)

---

## GameState — The Typed State Object

`GameState` is a single `TypedDict` that carries everything through the graph: player identity, current location, conversation history, RAG results, DM interpretation, token economy, and progression flags.

The player *is* the state. As you move through rooms, your position, inventory, and objectives are just fields on this dict — making the LangGraph concept of "state" tangible.

**File:** [state/game_state.py](state/game_state.py)

---

## RAG Engine — Retrieval Augmented Generation

The RAG system grounds AI answers in real documentation and world lore. When the player asks a question or mentions a LangChain term, the `rag_node` retrieves relevant chunks *before* the DM or Answer node responds.

### Ingestion Pipeline

```
Source documents
  ├── lore/*.pdf                    (fantasy lore — via PyPDFLoader)
  ├── knowledge_base/universal/*.md (LangQuest concept notes — TextLoader)
  ├── knowledge_base/themes/*.md    (fantasy lore themes — TextLoader)
  └── data/langsmith_docs_export.json  (LangSmith product docs)
        │
        ▼
  LangChain RecursiveCharacterTextSplitter
  (chunk_size=1200, chunk_overlap=180)
        │
        ▼
  OpenAI Embeddings
        │
        ▼
  Chroma Vector DB  ──▶  persisted to data/chroma_db/
  (collection: "lore")   rebuilt only when source files change
                         (content-hash manifest at data/lore_manifest.json)
```

### Retrieval Pipeline

```
Query from player input
        │
        ▼
  LoreRetriever (custom langchain_core.BaseRetriever)
    1. similarity_search_with_relevance_scores(query, k=k×4)
       — Chroma cosine similarity against stored embeddings
    2. Per-source-kind score boost applied to each candidate:
         langquest_concepts  × 2.4   (concept notes rank highest)
         langsmith_docs      × 1.8   (product docs rank second)
         fantasy_lore        × 1.0   (no boost)
    3. Re-sort by boosted score, return top-k
        │
        ▼
  retrieved_context injected into GameState
  (consumed by dm_node and answer_node)
```

The boosting ensures that LangQuest concept notes and LangSmith product docs surface above generic fantasy lore when the query is technical. Tracing-related terms (`langsmith`, `trace`, `evaluation`) trigger an additional preference for LangSmith docs.

**File:** [memory/lore_store.py](memory/lore_store.py)

---

## Chroma — The Vector Database

Chroma is the local, embedded vector database. It persists to `data/chroma_db/` as a SQLite metadata store paired with an HNSW approximate-nearest-neighbour index (`data_level0.bin`). All documents carry a `source_kind` metadata field that the `LoreRetriever` uses for score boosting.

On startup the lore store checks `data/lore_manifest.json` (a list of file paths, sizes, and mtimes). If sources are unchanged, the existing index loads in under a second. If anything changed, `build_lore_index()` rebuilds from scratch.

**Files:** [memory/lore_store.py](memory/lore_store.py), [scripts/ingest_lore.py](scripts/ingest_lore.py)

---

## DM Node — The AI Dungeon Master

The DM node translates free-form natural language into a canonical game command that Python can execute. It uses `langchain_anthropic.ChatAnthropic` (Claude Haiku) or `langchain_openai.ChatOpenAI` (GPT-4o-mini fallback).

### Decision flow

```
Player input
        │
        ├─ Exact scene alias match? ──▶ Local deterministic routing (no LLM)
        │
        ├─ Looks like a question?   ──▶ Local: "ask <topic>" 
        │
        ├─ Looks like a free action? ─▶ Local: "free <verb>" 
        │
        └─ Ambiguous / complex      ──▶ LLM call
               SystemMessage: role + legal actions + rules
               HumanMessage:  location + scene + RAG chunks + player input
               Response (JSON):
                 { "chosen_action": "...", "confidence": 0.9,
                   "reason": "...", "clarification": "..." }
```

Python then validates the chosen action against the legal action list before passing it to `rules_node`. The DM interprets intent; Python owns the rules.

**File:** [graph/nodes/dm_node.py](graph/nodes/dm_node.py)

---

## Analyst Node — Deterministic Player Signals

Before any AI is called, the analyst node scores the player's raw input using a word-match lexicon (`data/player_signal_words.json`). It updates `player_profile` with:

| Signal | What drives it |
|---|---|
| `attitude_score` | Positive vs. hostile words |
| `curiosity_score` | Question words, learning verbs |
| `caution_score` | Careful vs. reckless verbs |
| `token_penalty` | Hostile wording costs in-game tokens |

This is intentionally pure Python — no LLM, no LangSmith traces.

**File:** [graph/nodes/analyst_node.py](graph/nodes/analyst_node.py)

---

## Answer Node — RAG-Grounded AI Responses

When the DM routes a turn to `ask_question` or `free_action`, the answer node calls the LLM with the player's question, the current scene context, and the retrieved lore chunks. Answers blend in-world fantasy flavor with accurate LangChain/LangSmith product information pulled from the vector store.

The node reads `usage_metadata` from the API response and updates `tokens_spent_session` in game state.

**File:** [graph/nodes/answer_node.py](graph/nodes/answer_node.py)

---

## Narrative Node — AI Scene Painter

Active only in Level 2+ locations (`archive_approach`, `tree_exterior`, `tree_interior`, `tunnel_right`, `tunnel_left`). Takes the plain-text skeleton produced by `rules_node` and calls the LLM to add atmosphere, sensory detail, and LangGraph metaphors ("paths as edges, what you carry as state"). Costs tokens — that is the point.

**File:** [graph/nodes/narrative_node.py](graph/nodes/narrative_node.py)

---

## Rules Node — Pure Python Game Engine

`rules_node` is the authority on what is legal. It receives the command chosen by the DM, validates it, applies the state change (move to new location, award objectives, unlock doors), and sets `legal_outcomes` for the next turn. No AI. No LangSmith traces. Nothing here can be hallucinated.

**File:** [graph/nodes/rules_node.py](graph/nodes/rules_node.py)

---

## LLM Prompts

There are four system prompts across the three nodes that call the LLM, plus a dynamic `HumanMessage` assembled per turn from live game state.

### DM Node — Command Interpreter ([graph/nodes/dm_node.py](graph/nodes/dm_node.py))

Instructs the model to act as a command interpreter, not a narrator. Output is always compact JSON — no prose.

```
You are the Dungeon Master for LangQuest, an AI-native text adventure.

Your job is to interpret what the player is trying to do and choose the command
Python should apply next. Python owns the rules and state changes. You choose
only a safe command; you do not invent inventory, locations, rewards, or facts.
Use Retrieved lore to understand names, mythology, artifacts, and tone. Treat it
as reference material, not as permission to bypass Legal actions.

Reply as compact JSON only:
{
  "chosen_action": "exact command for Python, or clarify",
  "confidence": 0.0,
  "reason": "short reason",
  "clarification": "short in-world reply if the request cannot map to a command"
}

Rules:
- Prefer a command from Legal actions.
- If the player asks an informational question, choose "ask <topic>".
- If the player attempts a plausible physical action not on the legal list, choose "free <action>".
- When choosing a multi-word legal action, copy it verbatim from Legal actions.
- If nothing fits, use "clarify".
- JSON only. No markdown.
```

The `HumanMessage` is built at runtime and includes: current location, location description, current concept, completed objectives, retrieved lore (JSON), legal actions, and the player's raw and normalized input.

---

### Answer Node — In-World Question ([graph/nodes/answer_node.py](graph/nodes/answer_node.py))

Used when the player asks a question. Blends LangChain/LangSmith product documentation from the RAG context with in-world fantasy flavor. Enforces exact vocabulary for core LangGraph terms.

```
You are the Dungeon Master answering an in-world question in LangQuest.

Use the current scene first. Retrieved context may include fantasy lore,
LangQuest concept notes, and LangChain/LangSmith product documentation. When
the player asks about AI concepts, answer accurately from the product docs and
translate the idea into the fantasy scene.

Vocabulary rules — use these exact words when the concept appears:
  "state" — the typed dict carried through every node (not "data" or "record")
  "edge"  — the connection that routes state from one node to the next
  "node"  — the Python function that reads and updates state

Keep the answer concise: 2-5 sentences. Plain text only.
```

---

### Answer Node — Free Action ([graph/nodes/answer_node.py](graph/nodes/answer_node.py))

Used for harmless player experiments not on the legal action list ("kick the tree", "sing to Mira"). Resolves with a small consequence, no state changes.

```
You are the Dungeon Master narrating a harmless free-form action in LangQuest.

Resolve the action with a small, immediate consequence. Do not move the player,
grant items, complete objectives, reveal secrets, or change inventory.

Write in second person, present tense. 2-4 sentences. Plain text only.
```

---

### Narrative Node — Scene Painter ([graph/nodes/narrative_node.py](graph/nodes/narrative_node.py))

Active only in Level 2+ locations. Takes the plain-text skeleton from `rules_node` and enhances it with atmosphere and LangGraph metaphors. Facts from the skeleton must not change.

```
You are the Dungeon Master narrating LangQuest — a text adventure where LangGraph
concepts are woven into a fantasy world. Nodes, edges, state, and branching paths
exist as real things in Thornhaven.

Your task: take a plain scene description and enhance it with atmosphere and sensory detail.

Rules:
- Keep ALL facts from the input exactly as stated
- Write in second person ("You see...", "You feel..."), present tense
- Weave in graph/AI metaphors when they fit naturally: paths as edges,
  choices as branches, what you carry as state, memory as context
- Add 2-3 sentences of sensory detail that creates tension and wonder
- Plain text only — no markdown, no formatting
- Total output: 4-6 sentences, no more
```

---

### Prompt Summary

| Node | System prompt purpose | Output format | Max tokens |
|---|---|---|---|
| `dm_node` | Interpret intent → pick legal command | Compact JSON | 180 |
| `answer_node` (question) | Answer grounded in RAG + scene context | Plain text, 2-5 sentences | 220 |
| `answer_node` (free action) | Narrate harmless player experiment | Plain text, 2-4 sentences | 220 |
| `narrative_node` | Enhance skeleton scene with atmosphere | Plain text, 4-6 sentences | 220 |

---

## LangSmith — Observability and Evaluation

Ambient tracing is disabled globally so ordinary Python nodes (rules, analyst, display) stay out of the trace view. AI-facing operations opt in explicitly via the `@trace_ai_operation` decorator — a thin wrapper around `langsmith.traceable`.

| Trace name | What it captures |
|---|---|
| `ai.dm_decision` | LLM call, messages, legal actions, chosen command |
| `ai.dm_local_decision` | Deterministic routing decisions |
| `ai.in_world_answer` | Question answering with RAG context |
| `ai.free_action` | Free-form action resolution |
| `ai.narrative_scene_painter` | Scene enhancement in Level 2+ |
| `rag.lore_ingest` | Document loading, chunking, embedding counts |
| `rag.lore_retrieve` | Query, boosted scores, retrieved chunk snippets |

Set `LANGSMITH_API_KEY` in `.env` to activate. Without it every decorator is a no-op.

**File:** [ai/tracing.py](ai/tracing.py)

---

## Token Economy

Tokens are both a real cost and a game mechanic. `token_budget`, `tokens_spent_session`, and `tokens_earned_session` live on `GameState` and are updated by multiple nodes:

- **DM node** — deducts tokens per LLM call (capped at 75 to keep it fair)
- **Answer node** — deducts based on actual `usage_metadata` from the API
- **Analyst node** — applies a penalty for hostile wording
- **Rules node** — awards tokens for reaching milestones (visiting the well, completing a level, opening the chest)

The mechanic makes the cost of vague or aggressive prompts tangible.

**File:** [economy/token_tracker.py](economy/token_tracker.py)

---

## Data Flow — One Full Turn

```
Player: "what is an edge in langchain?"
        │
input_node     → raw_player_input = "what is an edge in langchain?"
        │
analyst_node   → curiosity_score += 2  (question + "what" detected)
        │
rag_node       → _looks_like_info_request() = True
        │        retrieve_lore(query, location="tavern", k=4)
        │          Chroma cosine search → LoreRetriever boost
        │        retrieved_context = [4 chunks about LangGraph edges]
        │
dm_node        → _looks_like_question() = True
        │        chosen = "ask langchain edge"  (local fast path, no LLM call)
        │
rules_node     → action_result = "ask_question"
        │        question_topic = "langchain edge"
        │
answer_node    → LLM called:
        │          SystemMessage: answer instructions + vocabulary rules
        │          HumanMessage:  question + scene + 4 lore chunks
        │        narrative_response = "Mira sets down her ledger. 'An edge
        │          routes state from one node to the next — every door in
        │          this tavern is an edge, but the graph decides which ones
        │          are real.' ..."
        │        tokens_spent_session += actual_usage
        │
narrative_node → location not in _AI_LOCATIONS → returns {}
        │
display_node   → Rich console renders narrative_response
```

---

## LangChain Libraries Used

| Library | Role |
|---|---|
| `langgraph` | Compiles and runs the `StateGraph` turn loop |
| `langchain-core` | `BaseRetriever`, `Document`, message types |
| `langchain-anthropic` | `ChatAnthropic` (Claude Haiku as DM and narrator) |
| `langchain-openai` | `ChatOpenAI` (GPT-4o-mini fallback) + `OpenAIEmbeddings` |
| `langchain-community` | `PyPDFLoader`, `TextLoader` for document ingestion |
| `langchain-chroma` | `Chroma` vector store wrapper |
| `langchain-text-splitters` | `RecursiveCharacterTextSplitter` |
| `langsmith` | Scoped tracing and LangSmith evaluation datasets |
| `chromadb` | Local embedded vector database (HNSW + SQLite) |

---

## Project Structure

```
langQuest/
├── main.py                         # Entry point — builds graph, runs game loop
├── requirements.txt
│
├── graph/
│   ├── graph_builder.py            # Assembles and compiles the StateGraph
│   └── nodes/
│       ├── input_node.py           # Captures and normalizes player input
│       ├── analyst_node.py         # Deterministic player signal scoring
│       ├── rag_node.py             # Chroma retrieval trigger
│       ├── dm_node.py              # AI Dungeon Master (LLM command interpreter)
│       ├── rules_node.py           # Pure Python game rules engine
│       ├── answer_node.py          # AI question answering + free actions
│       ├── narrative_node.py       # AI scene painter (Level 2+)
│       └── display_node.py         # Rich terminal renderer
│
├── state/
│   ├── game_state.py               # GameState TypedDict + level objectives
│   ├── player_profile.py           # Player behavior profile schema
│   └── world_bible.py              # World metadata model
│
├── memory/
│   └── lore_store.py               # RAG: loaders, splitter, Chroma, LoreRetriever
│
├── ai/
│   ├── tracing.py                  # LangSmith scoped trace decorators
│   ├── dungeon_master.py           # DM AI helpers
│   ├── analyst.py                  # Analyst AI helpers
│   └── world_builder.py            # World generation helpers
│
├── economy/
│   ├── token_tracker.py            # Token budget accounting
│   └── token_rewards.py            # Reward definitions
│
├── world/
│   └── locations.py                # Location definitions, exits, actions, text
│
├── ui/
│   └── terminal.py                 # Rich UI components
│
├── scripts/
│   ├── ingest_lore.py              # Rebuild Chroma index from source files
│   └── export_langsmith_docs.py    # Export LangSmith docs from parquet
│
├── tests/
│   ├── test_player_signals.py      # Analyst node signal scoring
│   ├── test_interpreter.py         # DM command interpretation accuracy
│   ├── test_dm_decisions.py        # DM routing against golden labels
│   ├── test_scenarios.py           # Multi-turn scenario walkthroughs
│   └── test_answer_quality.py      # Semantic quality of AI answers
│
├── data/
│   ├── chroma_db/                  # Persisted Chroma vector index
│   ├── lore_manifest.json          # Content-hash manifest for incremental ingest
│   ├── langsmith_docs_export.json  # Bundled LangSmith product docs
│   └── player_signal_words.json    # Word lexicon for analyst node
│
├── knowledge_base/
│   ├── universal/                  # LangQuest concept notes (Markdown)
│   └── themes/                     # Fantasy lore themes (Markdown)
│
└── lore/                           # Fantasy lore source PDFs
```
