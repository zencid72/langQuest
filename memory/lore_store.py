"""Local lore and product documentation ingestion/retrieval — LangChain vector store edition.

Documents are loaded with LangChain loaders, split with RecursiveCharacterTextSplitter,
embedded with OpenAIEmbeddings, and persisted in a Chroma vector store.
Retrieval goes through a custom BaseRetriever that applies per-source-kind score boosts
on top of Chroma cosine similarity scores.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import ConfigDict

from ai.tracing import trace_ai_operation

ROOT = Path(__file__).resolve().parents[1]
LORE_DIR = ROOT / "lore"
KNOWLEDGE_DIR = ROOT / "knowledge_base" / "universal"
THEMES_DIR = ROOT / "knowledge_base" / "themes"
DATA_DIR = ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
LANGSMITH_DOCS_EXPORT = DATA_DIR / "langsmith_docs_export.json"
MANIFEST_PATH = DATA_DIR / "lore_manifest.json"

COLLECTION_NAME = "lore"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180
MAX_TRACE_CHARS = 700

_DOC_QUERY_TERMS = {
    "agent", "chain", "dataset", "docs", "document", "embedding", "evaluation",
    "graph", "langchain", "langgraph", "langquest", "langsmith", "llm", "node",
    "prompt", "rag", "retrieval", "retriever", "run", "runnable", "state",
    "trace", "tracing", "vector",
}
_TRACING_TERMS = {"langsmith", "trace", "tracing", "evaluation"}

# Per-source-kind score multipliers applied after cosine similarity.
_SOURCE_BOOSTS: dict[str, float] = {
    "langquest_concepts": 2.4,
    "langsmith_docs": 1.8,
    "fantasy_lore": 1.0,
}

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)
_embeddings = OpenAIEmbeddings()

_VECTOR_STORE: Chroma | None = None


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def _fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {"path": str(path.relative_to(ROOT)), "size": stat.st_size, "mtime": int(stat.st_mtime)}


def _current_manifest() -> list[dict[str, Any]]:
    paths = list(sorted(LORE_DIR.glob("*.pdf")))
    paths += list(sorted(KNOWLEDGE_DIR.rglob("*.md")))
    paths += list(sorted(THEMES_DIR.rglob("*.md")))
    if LANGSMITH_DOCS_EXPORT.exists():
        paths.append(LANGSMITH_DOCS_EXPORT)
    return [_fingerprint(p) for p in paths if p.exists()]


def _load_pdf_documents(path: Path) -> list[Document]:
    loader = PyPDFLoader(str(path))
    docs = loader.load()
    for doc in docs:
        doc.metadata.update({"source_kind": "fantasy_lore", "title": path.stem, "url": ""})
    return docs


def _load_markdown_documents(path: Path) -> list[Document]:
    loader = TextLoader(str(path), encoding="utf-8")
    docs = loader.load()
    rel = str(path.relative_to(ROOT))
    title = path.stem.replace("_", " ").replace("-", " ").title()
    for doc in docs:
        doc.page_content = re.sub(r"```.*?```", " ", doc.page_content, flags=re.DOTALL)
        doc.page_content = re.sub(r"\s+", " ", doc.page_content).strip()
        doc.metadata.update({"source": rel, "source_kind": "langquest_concepts", "title": title, "url": ""})
    return docs


# Sentinel that appears near the top of every scraped LangSmith doc page that
# captured browser-rendered navigation HTML rather than article content.
_NAV_SENTINEL = "Skip to main content"


def _is_nav_chunk(text: str) -> bool:
    """Return True for docs that are mostly scraped page navigation, not content."""
    return _NAV_SENTINEL in text[:600]


def _load_langsmith_export() -> list[Document]:
    if not LANGSMITH_DOCS_EXPORT.exists():
        return []
    data = json.loads(LANGSMITH_DOCS_EXPORT.read_text(encoding="utf-8"))
    docs = []
    skipped = 0
    for entry in data.get("documents", []):
        text = str(entry.get("text") or "").strip()
        if len(text) < 80:
            continue
        if _is_nav_chunk(text):
            skipped += 1
            continue
        docs.append(Document(
            page_content=text,
            metadata={
                "source": entry.get("source") or "LangSmith docs",
                "source_kind": "langsmith_docs",
                "title": entry.get("title") or "LangSmith docs",
                "url": entry.get("url") or "",
            },
        ))
    if skipped:
        print(f"  [lore_store] skipped {skipped} nav-only LangSmith docs")
    return docs


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------

def _is_doc_query(query: str) -> bool:
    tokens = set(re.findall(r"[a-z]+", query.lower()))
    return bool(tokens & _DOC_QUERY_TERMS)


class LoreRetriever(BaseRetriever):
    """Wraps a Chroma vector store with per-source-kind score boosting."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vector_store: Any
    k: int = 4

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        doc_query = _is_doc_query(query)
        candidates = self.vector_store.similarity_search_with_relevance_scores(
            query, k=self.k * 4
        )
        query_tokens = set(query.lower().split())
        scored: list[tuple[float, Document]] = []
        for doc, base_score in candidates:
            source_kind = doc.metadata.get("source_kind", "fantasy_lore")
            boost = 1.0
            if doc_query:
                boost = _SOURCE_BOOSTS.get(source_kind, 1.0)
                if source_kind == "langsmith_docs" and not (query_tokens & _TRACING_TERMS):
                    boost = 1.15
            scored.append((base_score * boost, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[: self.k]
        for boosted_score, doc in top:
            doc.metadata["score"] = round(boosted_score, 4)
        return [doc for _, doc in top]


# ---------------------------------------------------------------------------
# Vector store lifecycle
# ---------------------------------------------------------------------------

def _get_or_build_vector_store() -> Chroma:
    global _VECTOR_STORE
    if _VECTOR_STORE is not None:
        return _VECTOR_STORE
    if CHROMA_DIR.exists() and MANIFEST_PATH.exists():
        stored = json.loads(MANIFEST_PATH.read_text())
        if stored == _current_manifest():
            _VECTOR_STORE = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=_embeddings,
                collection_name=COLLECTION_NAME,
            )
            return _VECTOR_STORE
    build_lore_index()
    assert _VECTOR_STORE is not None
    return _VECTOR_STORE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _trace_ingest_inputs(inputs: dict) -> dict:
    return {"lore_dir": str(inputs.get("lore_dir")), "force": inputs.get("force")}


def _trace_ingest_outputs(output: dict) -> dict:
    return {
        "documents": output.get("documents"),
        "chunks": output.get("chunks"),
        "index_path": output.get("index_path"),
    }


@trace_ai_operation(
    name="rag.lore_ingest",
    tags=["rag", "document-load"],
    process_inputs=_trace_ingest_inputs,
    process_outputs=_trace_ingest_outputs,
)
def build_lore_index(lore_dir: Path = LORE_DIR, force: bool = False) -> dict:
    """Load docs with LangChain loaders, split, embed, and persist to Chroma."""
    global _VECTOR_STORE
    lore_dir = Path(lore_dir)
    manifest = _current_manifest()

    if not manifest:
        raise FileNotFoundError(f"No lore or documentation files found under {ROOT}")

    if not force and CHROMA_DIR.exists() and MANIFEST_PATH.exists():
        stored = json.loads(MANIFEST_PATH.read_text())
        if stored == manifest:
            _VECTOR_STORE = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=_embeddings,
                collection_name=COLLECTION_NAME,
            )
            return {
                "documents": len(manifest),
                "chunks": _VECTOR_STORE._collection.count(),
                "index_path": str(CHROMA_DIR),
                "status": "unchanged",
            }

    print("  [lore_store] building lore index — embedding all documents (this takes ~1-2 min the first time)...")
    all_docs: list[Document] = []
    for path in sorted(lore_dir.glob("*.pdf")):
        all_docs.extend(_load_pdf_documents(path))
    for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        all_docs.extend(_load_markdown_documents(path))
    for path in sorted(THEMES_DIR.rglob("*.md")):
        docs = _load_markdown_documents(path)
        for doc in docs:
            doc.metadata["source_kind"] = "fantasy_lore"
        all_docs.extend(docs)
    all_docs.extend(_load_langsmith_export())

    chunks = _splitter.split_documents(all_docs)
    chunks = [c for c in chunks if len(c.page_content.strip()) >= 80]
    print(f"  [lore_store] embedding {len(chunks)} chunks...")

    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    DATA_DIR.mkdir(exist_ok=True)
    store = Chroma.from_documents(
        chunks,
        _embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )
    _VECTOR_STORE = store
    MANIFEST_PATH.write_text(json.dumps(manifest))

    return {
        "documents": len(manifest),
        "chunks": len(chunks),
        "index_path": str(CHROMA_DIR),
        "status": "rebuilt",
    }


def ensure_lore_index() -> dict:
    store = _get_or_build_vector_store()
    return {
        "documents": len(_current_manifest()),
        "chunks": store._collection.count(),
        "index_path": str(CHROMA_DIR),
        "status": "ready",
    }


def warm_lore_index() -> dict:
    """Preload the Chroma index so the first lore query is fast."""
    return ensure_lore_index()


def load_lore_index() -> dict:
    """Compatibility shim — warms the vector store and returns a summary dict."""
    store = _get_or_build_vector_store()
    return {
        "manifest": _current_manifest(),
        "chunks": [{"id": str(i)} for i in range(store._collection.count())],
    }


def _doc_to_chunk(doc: Document) -> dict:
    meta = doc.metadata
    return {
        "id": f"{meta.get('source', 'unknown')}:p{meta.get('page', 0)}",
        "source": meta.get("source", ""),
        "source_kind": meta.get("source_kind", "fantasy_lore"),
        "title": meta.get("title", meta.get("source", "")),
        "url": meta.get("url", ""),
        "page": meta.get("page"),
        "score": meta.get("score", 0.0),
        "text": doc.page_content[:900],
    }


def _trace_retrieval_inputs(inputs: dict) -> dict:
    return {"query": inputs.get("query"), "location": inputs.get("location"), "k": inputs.get("k")}


def _trace_retrieval_outputs(output: list[dict]) -> dict:
    return {
        "count": len(output),
        "matches": [
            {
                "source": item.get("source"),
                "source_kind": item.get("source_kind"),
                "title": item.get("title"),
                "page": item.get("page"),
                "url": item.get("url"),
                "score": item.get("score"),
                "snippet": item.get("text", "")[:MAX_TRACE_CHARS],
            }
            for item in output
        ],
    }


@trace_ai_operation(
    name="rag.lore_retrieve",
    tags=["rag", "retrieval"],
    process_inputs=_trace_retrieval_inputs,
    process_outputs=_trace_retrieval_outputs,
)
def retrieve_lore(query: str, location: str = "", k: int = 4) -> list[dict]:
    """Retrieve top lore chunks via LangChain FAISS vector store + LoreRetriever."""
    store = _get_or_build_vector_store()
    retriever = LoreRetriever(vector_store=store, k=k)
    combined_query = f"{query} {location}".strip() if location else query
    docs = retriever.invoke(combined_query)
    return [_doc_to_chunk(doc) for doc in docs]
