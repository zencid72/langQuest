"""
Golden answer tests for the LangQuest DM decision node.

Run locally:
  python tests/test_dm_decisions.py
  python tests/test_dm_decisions.py -v
  python tests/test_dm_decisions.py -v floor

Upload as a LangSmith experiment:
  python tests/test_dm_decisions.py --langsmith
"""
import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from ai.tracing import configure_scoped_tracing
from graph.nodes import dm_node as dm
from state.game_state import create_initial_state

configure_scoped_tracing()

GOLDEN_FILE = Path(__file__).parent / "golden_dm_decisions.json"
LANGSMITH_DATASET_NAME = "langquest-dm-decisions"


# ---------------------------------------------------------------------------
# Target function
# ---------------------------------------------------------------------------

def _run_dm_case(inputs: dict) -> dict:
    """Run a single DM decision case through dm_node and return the chosen action."""
    state = create_initial_state("Evaluator")
    state["current_location"] = inputs["location"]
    state["legal_outcomes"] = inputs["legal_outcomes"]
    state["raw_player_input"] = inputs["input"]
    state["last_player_input"] = inputs["input"].lower()

    result = dm.dm_node(state)
    if result.get("dm_clarification"):
        chosen = "clarify"
    else:
        chosen = result.get("last_player_input", "")
    return {
        "chosen_action": chosen,
        "dm_reason": result.get("dm_reason", ""),
        "dm_clarification": result.get("dm_clarification", ""),
    }


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def evaluate_dm_decision(outputs: dict, reference_outputs: dict) -> dict:
    """Exact-match check: chosen_action must equal expected_action."""
    got = outputs.get("chosen_action", "")
    expected = reference_outputs.get("expected_action", "")
    score = 1.0 if got == expected else 0.0
    return {
        "key": "dm_exact_match",
        "score": score,
        "comment": "Correct." if score == 1.0 else f"expected {expected!r}, got {got!r}",
        "metadata": {"expected": expected, "got": got},
    }


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------

def _case_inputs(case: dict) -> dict:
    return {
        "description": case["description"],
        "location": case["location"],
        "input": case["input"],
        "legal_outcomes": case["legal_outcomes"],
    }


def _case_outputs(case: dict) -> dict:
    return {"expected_action": case["expected_action"]}


def _case_id(case: dict) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"langquest-dm-decisions/{case['description']}")


def _ensure_langsmith_dataset(client: Any, cases: list[dict]) -> str:
    if client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        dataset = client.read_dataset(dataset_name=LANGSMITH_DATASET_NAME)
    else:
        dataset = client.create_dataset(
            LANGSMITH_DATASET_NAME,
            description="Golden DM routing decision cases for LangQuest.",
            metadata={"source_file": str(GOLDEN_FILE)},
        )

    existing_ids = {
        ex.id
        for ex in client.list_examples(dataset_id=dataset.id)
    }

    for case in cases:
        example_id = _case_id(case)
        kwargs = dict(
            dataset_id=dataset.id,
            inputs=_case_inputs(case),
            outputs=_case_outputs(case),
            metadata={"description": case["description"], "source_file": str(GOLDEN_FILE)},
            split="golden",
        )
        if example_id in existing_ids:
            client.update_example(example_id, **kwargs)
        else:
            client.create_example(example_id=example_id, **kwargs)

    return LANGSMITH_DATASET_NAME


# ---------------------------------------------------------------------------
# Local runner
# ---------------------------------------------------------------------------

def run_local(cases: list[dict], verbose: bool = False) -> int:
    if not dm._init_llm():
        print("ERROR: No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        return 1

    print("\nDM Decision Test Suite")
    print("─" * 60)

    passed = 0
    failed = 0
    errors = []

    for i, case in enumerate(cases, 1):
        try:
            outputs = _run_dm_case(_case_inputs(case))
            result = evaluate_dm_decision(outputs, _case_outputs(case))
            ok = result["score"] == 1.0

            if ok:
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
                errors.append((case, outputs))

            if verbose or not ok:
                print(f"  {status} [{i:02d}] {case['description']}")
                print(f"        input:    \"{case['input']}\"")
                print(f"        expected: {case['expected_action']}")
                print(f"        got:      {outputs['chosen_action']}")
                if verbose:
                    print(f"        reason:   {outputs.get('dm_reason', '')}")
                print()

            time.sleep(0.1)
        except Exception as e:
            failed += 1
            print(f"  ! [{i:02d}] ERROR — {case['description']}: {e}")

    total = passed + failed
    pct = int(100 * passed / total) if total else 0
    print("─" * 60)
    print(f"  Result: {passed}/{total} passed  ({pct}%)")

    if errors and not verbose:
        print("\n  Failures:")
        for case, outputs in errors:
            print(f"    ✗ \"{case['input']}\"")
            print(f"      expected: {case['expected_action']}  got: {outputs['chosen_action']}")
            if outputs.get("dm_reason"):
                print(f"      reason: {outputs['dm_reason']}")

    print()
    return 1 if failed else 0


# ---------------------------------------------------------------------------
# LangSmith runner
# ---------------------------------------------------------------------------

def run_langsmith(cases: list[dict]) -> int:
    from langsmith import Client

    client = Client()
    dataset_name = _ensure_langsmith_dataset(client, cases)
    examples = list(
        client.list_examples(
            dataset_name=dataset_name,
            example_ids=[_case_id(c) for c in cases],
        )
    )

    results = client.evaluate(
        _run_dm_case,
        data=examples,
        evaluators=[evaluate_dm_decision],
        experiment_prefix="langquest-dm-decisions",
        description="LangQuest DM routing golden exact-match checks.",
        metadata={"evaluator": "evaluate_dm_decision"},
        max_concurrency=1,
        blocking=True,
    )
    print(f"LangSmith experiment: {results.experiment_name}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run DM decision golden answer tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all cases, not just failures")
    parser.add_argument(
        "--langsmith", action="store_true",
        help="Upload dataset + evaluator feedback to LangSmith",
    )
    parser.add_argument("filter", nargs="?", default="", help="Filter tests by keyword")
    args = parser.parse_args()

    cases = json.loads(GOLDEN_FILE.read_text())
    if args.filter:
        needle = args.filter.lower()
        cases = [
            c for c in cases
            if needle in c["description"].lower() or needle in c["input"].lower()
        ]
        if not cases:
            print(f"No cases matched {args.filter!r}")
            sys.exit(1)

    if args.langsmith:
        if not (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")):
            print("ERROR: Set LANGSMITH_API_KEY to upload LangSmith evals.")
            sys.exit(2)
        sys.exit(run_langsmith(cases))

    sys.exit(run_local(cases, verbose=args.verbose))


if __name__ == "__main__":
    main()
