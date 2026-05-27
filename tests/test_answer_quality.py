"""
Semantic golden-answer checks for LangQuest in-world answers.

Run locally:
  python tests/test_answer_quality.py

Upload as a LangSmith experiment:
  python tests/test_answer_quality.py --langsmith
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
import uuid
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

if "--langsmith" not in sys.argv:
    os.environ["LANGADVENTURE_TRACE_AI"] = "false"
    os.environ["LANGADVENTURE_TRACE_STATE"] = "false"

from ai.tracing import configure_scoped_tracing, invoke_without_tracing
from graph.graph_builder import build_graph
from memory.lore_store import warm_lore_index
from state.game_state import create_initial_state

configure_scoped_tracing()

GOLDEN_FILE = Path(__file__).parent / "golden_answers.json"
DEFAULT_THRESHOLD = 0.27
LANGSMITH_DATASET_NAME = "langquest-answer-quality-golden"

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]{2,}")


def _tokens(text: str) -> list[str]:
    return [word.lower().strip("'-") for word in _WORD_RE.findall(text)]


def _token_f1(expected: str, actual: str) -> float:
    expected_counts = Counter(_tokens(expected))
    actual_counts = Counter(_tokens(actual))
    if not expected_counts or not actual_counts:
        return 0.0
    overlap = sum((expected_counts & actual_counts).values())
    precision = overlap / sum(actual_counts.values())
    recall = overlap / sum(expected_counts.values())
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _required_terms_present(actual: str, required_terms: list[str]) -> list[str]:
    actual_words = set(_tokens(actual))
    missing = []
    for term in required_terms:
        normalized = term.lower()
        variants = {normalized, f"{normalized}s", f"{normalized}es"}
        if not variants & actual_words:
            missing.append(term)
    return missing


def _semantic_score(expected: str, actual: str) -> float:
    lexical = _token_f1(expected, actual)
    sequence = SequenceMatcher(None, expected.lower(), actual.lower()).ratio()
    return round((0.72 * lexical) + (0.28 * sequence), 4)


def compare_semantic_similarity_v2(outputs: dict, reference_outputs: dict) -> dict:
    """Local automation fallback using the LangSmith feedback key we care about."""
    expected = reference_outputs.get("expected_response", "")
    actual = outputs.get("response", "")
    required_terms = reference_outputs.get("required_terms", [])
    missing_terms = _required_terms_present(actual, required_terms)
    score = _semantic_score(expected, actual)
    if missing_terms:
        score = round(score * 0.75, 4)
    elif required_terms:
        score = round(min(1.0, score + 0.1), 4)
    return {
        "key": "compare_semantic_similarity_v2",
        "score": score,
        "comment": (
            f"Missing required terms: {', '.join(missing_terms)}"
            if missing_terms else
            "Expected meaning and actual answer have sufficient lexical/semantic overlap."
        ),
        "metadata": {
            "missing_required_terms": missing_terms,
            "required_terms": required_terms,
            "local_fallback": True,
        },
    }


def _legal_outcomes(location: str) -> list[str]:
    if location == "tavern":
        return ["look", "mira", "sit", "leave", "ask tokens"]
    if location == "village_square":
        return ["well", "tavern", "north", "look"]
    if location == "kirjasto":
        return ["look", "aino", "catalog", "search", "outside", "south"]
    return ["look", "help"]


def _run_answer_case(inputs: dict[str, Any]) -> dict:
    app = build_graph()
    state = create_initial_state("Evaluator")
    state["current_location"] = inputs.get("location", "tavern")
    state["current_concept"] = inputs.get("current_concept", "")
    state["completed_objectives"] = inputs.get("completed_objectives", [])
    state["legal_outcomes"] = inputs.get("legal_outcomes") or _legal_outcomes(state["current_location"])
    state["last_player_input"] = inputs["input"]

    # Keep the CLI useful: suppress Rich rendering while preserving graph behavior.
    with contextlib.redirect_stdout(io.StringIO()):
        state = invoke_without_tracing(app.invoke, state)

    return {
        "response": state.get("narrative_response", ""),
        "action_result": state.get("action_result", ""),
        "dm_heard": state.get("dm_heard", ""),
        "question_answer_source": state.get("question_answer_source", ""),
        "question_lore_chunks_used": state.get("question_lore_chunks_used", 0),
        "retrieved_sources": [
            {
                "source": item.get("source"),
                "source_kind": item.get("source_kind"),
                "title": item.get("title"),
                "score": item.get("score"),
            }
            for item in state.get("retrieved_context", [])[:4]
        ],
    }


def _examples(cases: list[dict]) -> list[dict]:
    return [
        {
            "inputs": {
                "description": case["description"],
                "location": case["location"],
                "input": case["input"],
                "legal_outcomes": case.get("legal_outcomes"),
                "completed_objectives": case.get("completed_objectives", []),
            },
            "outputs": {
                "expected_response": case["expected_response"],
                "required_terms": case.get("required_terms", []),
            },
        }
        for case in cases
    ]


def _example_id(case: dict) -> uuid.UUID:
    stable_key = f"{case['description']}::{case['location']}::{case['input']}"
    return uuid.uuid5(uuid.NAMESPACE_URL, f"langquest-answer-quality/{stable_key}")


def _ensure_langsmith_dataset(client, cases: list[dict]) -> str:
    if client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        dataset = client.read_dataset(dataset_name=LANGSMITH_DATASET_NAME)
    else:
        dataset = client.create_dataset(
            LANGSMITH_DATASET_NAME,
            description="Golden semantic answer-quality cases for LangQuest.",
            metadata={"source_file": str(GOLDEN_FILE)},
        )

    existing_ids = {
        example.id
        for example in client.list_examples(dataset_id=dataset.id)
    }

    for case in cases:
        example_id = _example_id(case)
        inputs = {
            "description": case["description"],
            "location": case["location"],
            "input": case["input"],
            "legal_outcomes": case.get("legal_outcomes"),
            "completed_objectives": case.get("completed_objectives", []),
        }
        outputs = {
            "expected_response": case["expected_response"],
            "required_terms": case.get("required_terms", []),
        }
        metadata = {
            "description": case["description"],
            "source_file": str(GOLDEN_FILE),
        }
        if example_id in existing_ids:
            client.update_example(
                example_id,
                dataset_id=dataset.id,
                inputs=inputs,
                outputs=outputs,
                metadata=metadata,
                split="golden",
            )
        else:
            client.create_example(
                example_id=example_id,
                dataset_id=dataset.id,
                inputs=inputs,
                outputs=outputs,
                metadata=metadata,
                split="golden",
            )
    return LANGSMITH_DATASET_NAME


def run_local(cases: list[dict], threshold: float, verbose: bool = False) -> int:
    print("\nAnswer Quality Semantic Eval")
    print("-" * 72)
    failures = 0
    for i, example in enumerate(_examples(cases), start=1):
        outputs = _run_answer_case(example["inputs"])
        eval_result = compare_semantic_similarity_v2(outputs, example["outputs"])
        score = float(eval_result["score"])
        ok = score >= threshold
        failures += 0 if ok else 1
        status = "OK" if ok else "FAIL"
        print(f"  {status} [{i:02d}] {example['inputs']['description']}  score={score:.3f}")
        if verbose or not ok:
            print(f"        input:    {example['inputs']['input']}")
            print(f"        expected: {example['outputs']['expected_response']}")
            print(f"        actual:   {outputs['response']}")
            print(f"        source:   {outputs['question_answer_source']}  lore={outputs['question_lore_chunks_used']}")
            print(f"        comment:  {eval_result['comment']}")
            print()
    print("-" * 72)
    print(f"  Result: {len(cases) - failures}/{len(cases)} passed  threshold={threshold}")
    return 1 if failures else 0


def run_langsmith(cases: list[dict], threshold: float) -> int:
    from langsmith import Client

    client = Client()
    dataset_name = _ensure_langsmith_dataset(client, cases)
    examples = list(
        client.list_examples(
            dataset_name=dataset_name,
            example_ids=[_example_id(case) for case in cases],
        )
    )
    results = client.evaluate(
        _run_answer_case,
        data=examples,
        evaluators=[compare_semantic_similarity_v2],
        experiment_prefix="langquest-answer-quality",
        description="LangQuest semantic answer quality against golden meanings.",
        metadata={"threshold": threshold, "evaluator": "compare_semantic_similarity_v2"},
        max_concurrency=0,
        blocking=True,
    )
    print(f"LangSmith experiment: {results.experiment_name}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run semantic golden-answer quality evals")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--langsmith", action="store_true", help="Upload runs/evaluator feedback to LangSmith")
    args = parser.parse_args()

    warm_lore_index()
    cases = json.loads(GOLDEN_FILE.read_text())
    if args.langsmith:
        if not (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")):
            print("ERROR: Set LANGSMITH_API_KEY or LANGCHAIN_API_KEY to upload LangSmith evals.")
            sys.exit(2)
        sys.exit(run_langsmith(cases, args.threshold))
    sys.exit(run_local(cases, args.threshold, verbose=args.verbose))


if __name__ == "__main__":
    main()
