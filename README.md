# LangQuest

```
██╗      █████╗ ███╗   ██╗ ██████╗      ██████╗ ██╗   ██╗███████╗███████╗████████╗
██║     ██╔══██╗████╗  ██║██╔════╝     ██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝
██║     ███████║██╔██╗ ██║██║  ███╗    ██║   ██║██║   ██║█████╗  ███████╗   ██║   
██║     ██╔══██║██║╚██╗██║██║   ██║    ██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   
███████╗██║  ██║██║ ╚████║╚██████╔╝    ╚██████╔╝╚██████╔╝███████╗███████║   ██║   
╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝      ╚══▀▀═╝  ╚═════╝╚══════╝╚══════╝   ╚═╝   
```

> ⚔ **Forge your knowledge through the dungeons of LangGraph.** ⚔  
> Learn nodes · edges · state · RAG · LangSmith tracing — through play.

```
        _____                                       _____
       |     |    .  *   .    *   .   *   .   *   |     |
       | [=] |                                     | [=] |
       |_____|   .-~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~.   |_____|
          |     ( Every room is a node.               )     |
        __|__    ( Every path is an edge.             )    __|__
       /     \    ( You are the state.               )   /     \
      | ENTRY |    `~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'  | VAULT |
       \_____/                                             \_____/
          |              ,-.   ,-.                           |
          |             ( o ) ( o )                          |
        ~~+~~            |=====|                           ~~+~~
          |              | [?] |    "Ask me anything,        |
          |              |     |     adventurer."            |
                          \___/
                          _| |_          — Mira, Innkeeper
                         (_____) ⚔       of the Gilded Node
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/ingest_lore.py --force
python main.py
```

After `source venv/bin/activate`, your shell prompt should show the active environment, usually as `(venv)`. From there, `python main.py` starts the interactive LangQuest prompt.

If you prefer not to activate the environment, you can run the same commands through the venv directly:

```bash
venv/bin/python scripts/ingest_lore.py --force
venv/bin/python main.py
```

The first `ingest_lore.py` run embeds all documents into a local Chroma vector database at `data/chroma_db/`. This takes 1–2 minutes. Subsequent runs use a content hash manifest and skip unchanged sources.

## Local RAG Sources

LangQuest builds its retrieval index from:

- `lore/*.pdf`
- `knowledge_base/universal/**/*.md`
- `knowledge_base/themes/**/*.md`
- `data/langsmith_docs_export.json`

The index is stored as a Chroma vector database at `data/chroma_db/`. Navigation-only scraped pages are filtered automatically during ingestion.

## Refreshing Product Docs

The project already includes `data/langsmith_docs_export.json`, so the game does not need an external course repo to run. To refresh that export from a parquet file you have locally:

```bash
venv/bin/python scripts/export_langsmith_docs.py --parquet /path/to/union.parquet
venv/bin/python scripts/ingest_lore.py --force
```

The export script records only the parquet filename in the JSON metadata, keeping the project portable.

## Tracing

LangQuest uses scoped tracing around AI and RAG operations: DM decisions, prompt/response generation, document retrieval, and ingestion. Pure Python display, rules plumbing, and terminal rendering are intentionally kept out of global tracing.

Set `LANGSMITH_API_KEY` in `.env` to send traces to LangSmith. Without it, tracing is a no-op.

## Tests

Each test file can run locally or upload results to a LangSmith dataset and experiment.

**Run all tests locally:**

```bash
python tests/test_player_signals.py
python tests/test_interpreter.py
python tests/test_dm_decisions.py
python tests/test_scenarios.py
python tests/test_answer_quality.py
```

Add `-v` for verbose output (all cases, not just failures). Pass an optional keyword to filter:

```bash
python tests/test_dm_decisions.py -v floor
python tests/test_interpreter.py -v well
```

**Upload to LangSmith** (requires `LANGSMITH_API_KEY`):

```bash
python tests/test_player_signals.py --langsmith
python tests/test_interpreter.py --langsmith
python tests/test_dm_decisions.py --langsmith
python tests/test_scenarios.py --langsmith
python tests/test_answer_quality.py --langsmith
```

Each `--langsmith` run upserts examples into a named dataset and records a new experiment run so results are tracked over time.

| File | Dataset | What it checks |
|---|---|---|
| `test_player_signals.py` | `langquest-player-signals` | Attitude/curiosity deltas and token penalties from analyst node |
| `test_interpreter.py` | `langquest-interpreter` | AI command interpreter exact-match on natural language inputs |
| `test_dm_decisions.py` | `langquest-dm-decisions` | DM routing decisions against golden expected actions |
| `test_scenarios.py` | `langquest-scenarios` | Multi-turn scenario walkthroughs including objective completion |
| `test_answer_quality.py` | `langquest-answer-quality` | Semantic quality of AI-generated in-world answers |
