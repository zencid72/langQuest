"""
Golden tests for deterministic player-profile signals.

Run locally:
  python tests/test_player_signals.py
  python tests/test_player_signals.py -v
  python tests/test_player_signals.py -v hostile

Upload as a LangSmith experiment:
  python tests/test_player_signals.py --langsmith
"""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from ai.tracing import configure_scoped_tracing

configure_scoped_tracing()

from graph.nodes.analyst_node import analyst_node, analyze_player_input
from state.game_state import create_initial_state

GOLDEN_FILE = Path(__file__).parent / "golden_player_signals.json"
LANGSMITH_DATASET_NAME = "langquest-player-signals"


# ---------------------------------------------------------------------------
# Target function
# ---------------------------------------------------------------------------

def _run_signal_case(inputs: dict) -> dict:
    """Run a single player signal case and return measured deltas and penalty."""
    signal = analyze_player_input(inputs["input"])
    state = create_initial_state("Evaluator")
    state["raw_player_input"] = inputs["input"]
    state["last_player_input"] = inputs["input"].lower()
    state["token_budget"] = 5000
    state["token_budget_discovered"] = True
    updates = analyst_node(state)

    return {
        "attitude_delta": signal["attitude_delta"],
        "curiosity_delta": signal["curiosity_delta"],
        "token_penalty": signal["token_penalty"],
        "tokens_spent_session": updates.get("tokens_spent_session"),
    }


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def evaluate_player_signal(outputs: dict, reference_outputs: dict) -> dict:
    """Constraint check: each bound that is present must pass."""
    checks = []
    notes = []

    attitude = outputs.get("attitude_delta", 0)
    curiosity = outputs.get("curiosity_delta", 0)
    penalty = outputs.get("token_penalty", 0)
    spent = outputs.get("tokens_spent_session")

    if "min_attitude_delta" in reference_outputs:
        bound = reference_outputs["min_attitude_delta"]
        ok = attitude >= bound
        checks.append(ok)
        if not ok:
            notes.append(f"attitude {attitude} < min {bound}")

    if "max_attitude_delta" in reference_outputs:
        bound = reference_outputs["max_attitude_delta"]
        ok = attitude <= bound
        checks.append(ok)
        if not ok:
            notes.append(f"attitude {attitude} > max {bound}")

    if "min_curiosity_delta" in reference_outputs:
        bound = reference_outputs["min_curiosity_delta"]
        ok = curiosity >= bound
        checks.append(ok)
        if not ok:
            notes.append(f"curiosity {curiosity} < min {bound}")

    expected_penalty = reference_outputs.get("expected_penalty", 0)
    ok = penalty == expected_penalty
    checks.append(ok)
    if not ok:
        notes.append(f"penalty {penalty} != expected {expected_penalty}")

    if expected_penalty:
        ok = spent == expected_penalty
        checks.append(ok)
        if not ok:
            notes.append(f"tokens_spent_session {spent} != {expected_penalty}")
    else:
        ok = spent is None
        checks.append(ok)
        if not ok:
            notes.append(f"tokens_spent_session should be absent, got {spent}")

    score = sum(checks) / len(checks) if checks else 0.0
    return {
        "key": "player_signal_constraints",
        "score": score,
        "comment": "All constraints passed." if not notes else "; ".join(notes),
        "metadata": {
            "attitude_delta": attitude,
            "curiosity_delta": curiosity,
            "token_penalty": penalty,
            "tokens_spent_session": spent,
        },
    }


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------

def _case_inputs(case: dict) -> dict:
    return {
        "description": case["description"],
        "input": case["input"],
    }


def _case_outputs(case: dict) -> dict:
    out = {"expected_penalty": case["expected_penalty"]}
    for key in ("min_attitude_delta", "max_attitude_delta", "min_curiosity_delta"):
        if key in case:
            out[key] = case[key]
    return out


def _case_id(case: dict) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"langquest-player-signals/{case['description']}")


def _ensure_langsmith_dataset(client: Any, cases: list[dict]) -> str:
    if client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        dataset = client.read_dataset(dataset_name=LANGSMITH_DATASET_NAME)
    else:
        dataset = client.create_dataset(
            LANGSMITH_DATASET_NAME,
            description="Golden player-profile signal cases for LangQuest.",
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
    print("\nPlayer Signal Test Suite")
    print("─" * 60)

    passed = 0
    failed = 0
    errors = []

    for i, case in enumerate(cases, 1):
        try:
            outputs = _run_signal_case(_case_inputs(case))
            result = evaluate_player_signal(outputs, _case_outputs(case))
            ok = result["score"] == 1.0

            if ok:
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
                errors.append((case, outputs, result["comment"]))

            if verbose or not ok:
                print(f"  {status} [{i:02d}] {case['description']}")
                print(f"        input:     \"{case['input']}\"")
                print(f"        attitude:  {outputs['attitude_delta']}")
                print(f"        curiosity: {outputs['curiosity_delta']}")
                print(f"        penalty:   {outputs['token_penalty']}")
                if not ok:
                    print(f"        failures:  {result['comment']}")
                print()

        except Exception as e:
            failed += 1
            print(f"  ! [{i:02d}] ERROR — {case['description']}: {e}")

    total = passed + failed
    pct = int(100 * passed / total) if total else 0
    print("─" * 60)
    print(f"  Result: {passed}/{total} passed  ({pct}%)")

    if errors and not verbose:
        print("\n  Failures:")
        for case, outputs, comment in errors:
            print(f"    ✗ \"{case['input']}\"")
            print(f"      {comment}")

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
        _run_signal_case,
        data=examples,
        evaluators=[evaluate_player_signal],
        experiment_prefix="langquest-player-signals",
        description="LangQuest player-profile signal golden constraint checks.",
        metadata={"evaluator": "evaluate_player_signal"},
        max_concurrency=1,
        blocking=True,
    )
    print(f"LangSmith experiment: {results.experiment_name}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run player signal golden tests")
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
