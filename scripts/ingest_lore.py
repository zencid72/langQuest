"""Build the local LangQuest RAG index from lore PDFs and product docs."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv()

from ai.tracing import configure_scoped_tracing
from memory.lore_store import build_lore_index

configure_scoped_tracing()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest lore PDFs and LangChain/LangSmith docs into the local RAG index")
    parser.add_argument("--force", action="store_true", help="Rebuild even if PDFs have not changed")
    args = parser.parse_args()

    result = build_lore_index(force=args.force)
    print(f"RAG index {result['status']}: {result['documents']} source files, {result['chunks']} chunks")
    print(result["index_path"])


if __name__ == "__main__":
    main()
