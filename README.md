# LangQuest

LangQuest is a terminal RPG for learning LangGraph, LangChain, LangSmith tracing, RAG, prompts, nodes, edges, and state through play.

The project is self-contained. It uses local lore PDFs, local concept notes, and the checked-in LangSmith documentation export under `data/` for retrieval.

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

## Local RAG Sources

LangQuest builds its local retrieval index from:

- `lore/*.pdf`
- `knowledge_base/universal/**/*.md`
- `data/langsmith_docs_export.json`

The generated index is stored at `data/lore_index.json`.

## Refreshing Product Docs

The project already includes `data/langsmith_docs_export.json`, so the game does not need an external course repo to run. To refresh that export from a parquet file you have locally:

```bash
venv/bin/python scripts/export_langsmith_docs.py --parquet /path/to/union.parquet
venv/bin/python scripts/ingest_lore.py --force
```

The export script records only the parquet filename in the JSON metadata, keeping the project portable.

## Tracing

LangQuest uses scoped tracing around AI and RAG operations: DM decisions, prompt/response generation, document retrieval, and ingestion. Pure Python display, rules plumbing, and terminal rendering are intentionally kept out of global tracing.
