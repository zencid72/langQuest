"""Export cached LangSmith docs parquet into project-local JSON.

This is an optional bridge for refreshing the local RAG index. LangQuest does
not require pandas/pyarrow at runtime; it only needs the exported JSON checked
into this project.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "langsmith_docs_export.json"


def _title_from_text(text: str, url: str) -> str:
    if url:
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if slug:
            return slug.replace("-", " ").title()
    first = re.split(r"[\n\r]", text.strip(), maxsplit=1)[0]
    first = re.sub(r"\s+", " ", first).strip()
    if first:
        return first[:140]
    return url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export LangSmith docs parquet into JSON")
    parser.add_argument("--parquet", type=Path, required=True, help="Path to an exported SKLearnVectorStore parquet")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    import pandas as pd

    if not args.parquet.exists():
        raise FileNotFoundError(f"Parquet file not found: {args.parquet}")

    df = pd.read_parquet(args.parquet)
    docs = []
    for row in df.to_dict(orient="records"):
        text = str(row.get("texts") or "").strip()
        if len(text) < 80:
            continue
        metadata = row.get("metadatas") or {}
        url = metadata.get("source") or metadata.get("loc") or ""
        docs.append({
            "id": row.get("ids"),
            "source": "LangSmith docs",
            "title": _title_from_text(text, url),
            "url": url,
            "lastmod": metadata.get("lastmod"),
            "text": re.sub(r"\s+", " ", text),
        })

    args.output.parent.mkdir(exist_ok=True)
    args.output.write_text(json.dumps({
        "source": args.parquet.name,
        "documents": docs,
    }, indent=2), encoding="utf-8")
    print(f"Exported {len(docs)} LangSmith doc chunks to {args.output}")


if __name__ == "__main__":
    main()
