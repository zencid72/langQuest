"""Local lore and product documentation ingestion/retrieval.

This is a lightweight persistent index: PDFs, local concept docs, and exported
LangSmith documentation are split into RAG-sized chunks, scored locally, and
stored as JSON. It keeps the app usable without requiring a vector database.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ai.tracing import trace_ai_operation

ROOT = Path(__file__).resolve().parents[1]
LORE_DIR = ROOT / "lore"
KNOWLEDGE_DIR = ROOT / "knowledge_base" / "universal"
INDEX_DIR = ROOT / "data"
INDEX_PATH = INDEX_DIR / "lore_index.json"
LANGSMITH_DOCS_EXPORT = INDEX_DIR / "langsmith_docs_export.json"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 180
MAX_TRACE_CHARS = 700
_LORE_INDEX_CACHE: dict[str, Any] | None = None

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]{2,}")
_DOC_QUERY_TERMS = {
    "agent", "chain", "dataset", "docs", "document", "embedding", "evaluation",
    "graph", "langchain", "langgraph", "langquest", "langsmith", "llm", "node",
    "prompt", "rag", "retrieval", "retriever", "run", "runnable", "state",
    "trace", "tracing", "vector",
}


def _tokenize(text: str) -> list[str]:
    return [word.lower().strip("'-") for word in _WORD_RE.findall(text)]


def _fingerprint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.relative_to(ROOT)),
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
    }


def _current_manifest(lore_dir: Path = LORE_DIR) -> list[dict[str, Any]]:
    paths = list(sorted(Path(lore_dir).glob("*.pdf")))
    paths += list(sorted(KNOWLEDGE_DIR.rglob("*.md")))
    if LANGSMITH_DOCS_EXPORT.exists():
        paths.append(LANGSMITH_DOCS_EXPORT)
    return [_fingerprint(path) for path in paths if path.exists()]


def _load_pdf_text(path: Path) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to ingest PDF lore: pip install pypdf") from exc

    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append({"page": page_number, "text": text})
    return pages


def _load_markdown_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_text(text: str) -> list[str]:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)
    except ImportError:
        chunks = []
        step = CHUNK_SIZE - CHUNK_OVERLAP
        for start in range(0, len(text), step):
            chunk = text[start:start + CHUNK_SIZE].strip()
            if chunk:
                chunks.append(chunk)
        return chunks


def _chunk_terms(text: str) -> dict[str, int]:
    counts = Counter(_tokenize(text))
    return dict(counts)


def _navigation_penalty(text: str) -> float:
    lower = text.lower()
    dot_ratio = text.count(".") / max(len(text), 1)
    if lower.startswith("index ") or lower.startswith("contents ") or dot_ratio > 0.12:
        return 0.25
    return 1.0


def _title_overlap_bonus(chunk: dict[str, Any], query_terms: Counter) -> float:
    url_slug = str(chunk.get("url", "")).rstrip("/").rsplit("/", 1)[-1]
    title_terms = set(_tokenize(f"{chunk.get('title', '')} {url_slug} {chunk.get('source_kind', '')}"))
    if not title_terms:
        return 0.0
    return 0.12 * len(set(query_terms) & title_terms)


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
    """Extract docs, split them into chunks, and persist the local RAG index."""
    global _LORE_INDEX_CACHE
    lore_dir = Path(lore_dir)
    manifest = _current_manifest(lore_dir)
    if not manifest:
        raise FileNotFoundError(f"No lore or documentation files found under {ROOT}")

    if not force and INDEX_PATH.exists():
        existing = json.loads(INDEX_PATH.read_text())
        if existing.get("manifest") == manifest:
            return {
                "documents": len(manifest),
                "chunks": len(existing.get("chunks", [])),
                "index_path": str(INDEX_PATH),
                "status": "unchanged",
            }

    chunks: list[dict[str, Any]] = []
    for path in sorted(lore_dir.glob("*.pdf")):
        for page in _load_pdf_text(path):
            for chunk_index, chunk_text in enumerate(_split_text(page["text"])):
                if len(chunk_text) < 80:
                    continue
                chunk_id = f"{path.stem}:p{page['page']}:c{chunk_index}"
                chunks.append({
                    "id": chunk_id,
                    "source": path.name,
                    "source_kind": "fantasy_lore",
                    "title": path.stem,
                    "url": "",
                    "page": page["page"],
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "terms": _chunk_terms(f"{path.stem} {chunk_text}"),
                })

    for path in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        text = _load_markdown_text(path)
        if len(text) < 80:
            continue
        title = path.stem.replace("_", " ").replace("-", " ").title()
        for chunk_index, chunk_text in enumerate(_split_text(text)):
            if len(chunk_text) < 80:
                continue
            rel = path.relative_to(ROOT)
            chunk_id = f"{rel}:c{chunk_index}"
            chunks.append({
                "id": chunk_id,
                "source": str(rel),
                "source_kind": "langquest_concepts",
                "title": title,
                "url": "",
                "page": None,
                "chunk_index": chunk_index,
                "text": chunk_text,
                "terms": _chunk_terms(f"{title} {rel} {chunk_text}"),
            })

    if LANGSMITH_DOCS_EXPORT.exists():
        exported = json.loads(LANGSMITH_DOCS_EXPORT.read_text(encoding="utf-8"))
        for doc_index, doc in enumerate(exported.get("documents", [])):
            text = str(doc.get("text") or "").strip()
            if len(text) < 80:
                continue
            chunk_id = f"langsmith-docs:{doc.get('id') or doc_index}"
            chunks.append({
                "id": chunk_id,
                "source": doc.get("source") or "LangSmith docs",
                "source_kind": "langsmith_docs",
                "title": doc.get("title") or "LangSmith docs",
                "url": doc.get("url") or "",
                "page": None,
                "chunk_index": doc_index,
                "text": text,
                "terms": _chunk_terms(
                    f"{doc.get('title', '')} "
                    f"{str(doc.get('url', '')).rstrip('/').rsplit('/', 1)[-1]} "
                    f"{text}"
                ),
            })

    INDEX_DIR.mkdir(exist_ok=True)
    INDEX_PATH.write_text(json.dumps({
        "manifest": manifest,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "chunks": chunks,
    }, indent=2))
    _LORE_INDEX_CACHE = {
        "manifest": manifest,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "chunks": chunks,
    }

    return {
        "documents": len(manifest),
        "chunks": len(chunks),
        "index_path": str(INDEX_PATH),
        "status": "rebuilt",
    }


def ensure_lore_index() -> dict:
    index = load_lore_index()
    return {
        "documents": len(index.get("manifest", [])),
        "chunks": len(index.get("chunks", [])),
        "index_path": str(INDEX_PATH),
        "status": "ready",
    }


def load_lore_index() -> dict[str, Any]:
    """Return the parsed local RAG index, loading it once per process."""
    global _LORE_INDEX_CACHE
    if _LORE_INDEX_CACHE is not None:
        return _LORE_INDEX_CACHE
    if not INDEX_PATH.exists():
        build_lore_index()
        return _LORE_INDEX_CACHE or {}
    existing = json.loads(INDEX_PATH.read_text())
    if existing.get("manifest") != _current_manifest():
        build_lore_index(force=True)
        return _LORE_INDEX_CACHE or {}
    _LORE_INDEX_CACHE = existing
    return _LORE_INDEX_CACHE


def warm_lore_index() -> dict:
    """Preload the local RAG index so the first lore question is fast."""
    index = load_lore_index()
    return {
        "documents": len(index.get("manifest", [])),
        "chunks": len(index.get("chunks", [])),
        "index_path": str(INDEX_PATH),
        "status": "ready",
    }


def _trace_retrieval_inputs(inputs: dict) -> dict:
    return {
        "query": inputs.get("query"),
        "location": inputs.get("location"),
        "k": inputs.get("k"),
    }


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
    """Return top lore chunks for the query from the persisted local index."""
    index = load_lore_index()
    query_terms = Counter(_tokenize(f"{query} {location}"))
    if not query_terms:
        return []

    doc_query = bool(set(query_terms) & _DOC_QUERY_TERMS)
    results = []
    for chunk in index.get("chunks", []):
        terms = chunk.get("terms", {})
        overlap = 0.0
        for term, q_count in query_terms.items():
            overlap += min(q_count, terms.get(term, 0))
        if overlap <= 0:
            continue

        length_norm = math.sqrt(sum(count * count for count in terms.values())) or 1
        source_kind = chunk.get("source_kind", "fantasy_lore")
        source_boost = 1.0
        if doc_query and source_kind == "langquest_concepts":
            source_boost = 2.4
        elif doc_query and source_kind == "langsmith_docs":
            source_boost = 1.8 if {"langsmith", "trace", "tracing", "evaluation"} & set(query_terms) else 1.15
        base_score = (overlap / length_norm) * _navigation_penalty(chunk.get("text", "")) * source_boost
        score = round(base_score + _title_overlap_bonus(chunk, query_terms), 4)
        results.append({
            "id": chunk["id"],
            "source": chunk["source"],
            "source_kind": source_kind,
            "title": chunk.get("title", chunk["source"]),
            "url": chunk.get("url", ""),
            "page": chunk["page"],
            "score": score,
            "text": chunk["text"][:900],
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:k]
