"""
Multi-turn scenario evaluation for LangQuest.

Each scenario in golden_scenarios.json is a sequence of player inputs played
through the full LangGraph pipeline.  After every turn, structured checks verify
location, objectives, level, action_result, and required narrative terms.

Run locally:
  python tests/test_scenarios.py

Run verbose (show every turn):
  python tests/test_scenarios.py -v

Run a single scenario by id or keyword:
  python tests/test_scenarios.py -v level_1

Upload as a LangSmith experiment:
  python tests/test_scenarios.py --langsmith
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import uuid
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

GOLDEN_FILE = Path(__file__).parent / "golden_scenarios.json"
LANGSMITH_DATASET_NAME = "langquest-scenario-evals"


# ---------------------------------------------------------------------------
# Scenario runner — produces a transcript the evaluator inspects
# ---------------------------------------------------------------------------

def _run_scenario(inputs: dict[str, Any]) -> dict:
    """Replay a full scenario through the LangGraph pipeline and return a transcript."""
    app = build_graph()
    state = create_initial_state("Evaluator")

    for key, value in inputs.get("initial_state", {}).items():
        state[key] = value  # type: ignore[literal-required]

    transcript: list[dict] = []

    for turn in inputs["turns"]:
        state["raw_player_input"] = turn["input"]
        state["last_player_input"] = turn["input"].lower()
        state["level_just_completed"] = False

        with contextlib.redirect_stdout(io.StringIO()):
            state = invoke_without_tracing(app.invoke, state)

        transcript.append({
            "input": turn["input"],
            "description": turn.get("description", ""),
            "location": state.get("current_location", ""),
            "action_result": state.get("action_result", ""),
            "objectives": list(state.get("completed_objectives", [])),
            "level": state.get("current_level", 1),
            "narrative": state.get("narrative_response", "")[:400],
        })

    return {
        "transcript": transcript,
        "final_location": state.get("current_location", ""),
        "final_level": state.get("current_level", 1),
        "final_objectives": list(state.get("completed_objectives", [])),
    }


# ---------------------------------------------------------------------------
# Evaluator — checks the transcript against per-turn expectations
# ---------------------------------------------------------------------------

def _check_turn(turn_result: dict, expect: dict) -> list[str]:
    """Return a list of failure strings (empty = all passed)."""
    failures: list[str] = []
    inp = turn_result["input"]

    if "location" in expect:
        if turn_result["location"] != expect["location"]:
            failures.append(
                f"location: expected {expect['location']!r}, got {turn_result['location']!r}"
            )

    for obj in expect.get("objectives_include", []):
        if obj not in turn_result["objectives"]:
            failures.append(f"objective {obj!r} missing (have {turn_result['objectives']})")

    if "level" in expect:
        if turn_result["level"] != expect["level"]:
            failures.append(f"level: expected {expect['level']}, got {turn_result['level']}")

    if "action_result_not" in expect:
        if turn_result["action_result"] == expect["action_result_not"]:
            failures.append(
                f"action_result was {turn_result['action_result']!r} (must not be)"
            )

    narrative_lower = turn_result["narrative"].lower()
    for term in expect.get("required_terms", []):
        if term.lower() not in narrative_lower:
            failures.append(f"required term {term!r} absent from narrative")

    return [f"turn {inp!r}: {f}" for f in failures]


def evaluate_scenario(outputs: dict, reference_outputs: dict) -> dict:
    """LangSmith-compatible evaluator: checks transcript against golden turn expectations."""
    transcript = outputs.get("transcript", [])
    turn_checks = reference_outputs.get("turn_checks", [])

    all_failures: list[str] = []
    checks_total = 0
    checks_passed = 0

    for turn_result, expect in zip(transcript, turn_checks):
        if not expect:
            continue
        failures = _check_turn(turn_result, expect)
        n_checks = (
            ("location" in expect)
            + len(expect.get("objectives_include", []))
            + ("level" in expect)
            + ("action_result_not" in expect)
            + len(expect.get("required_terms", []))
        )
        checks_total += n_checks
        checks_passed += n_checks - len(failures)
        all_failures.extend(failures)

    score = round(checks_passed / checks_total, 4) if checks_total else 1.0
    return {
        "key": "scenario_checks",
        "score": score,
        "comment": "; ".join(all_failures) if all_failures else "All checks passed.",
        "metadata": {
            "checks_total": checks_total,
            "checks_passed": checks_passed,
            "failures": all_failures,
        },
    }


# ---------------------------------------------------------------------------
# Dataset helpers
# ---------------------------------------------------------------------------

def _scenario_inputs(scenario: dict) -> dict:
    return {
        "id": scenario["id"],
        "description": scenario["description"],
        "initial_state": scenario.get("initial_state", {}),
        "turns": [
            {"input": t["input"], "description": t.get("description", "")}
            for t in scenario["turns"]
        ],
    }


def _scenario_outputs(scenario: dict) -> dict:
    return {
        "turn_checks": [t.get("expect", {}) for t in scenario["turns"]],
    }


def _scenario_id(scenario: dict) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"langquest-scenarios/{scenario['id']}")


def _ensure_langsmith_dataset(client: Any, scenarios: list[dict]) -> str:
    if client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        dataset = client.read_dataset(dataset_name=LANGSMITH_DATASET_NAME)
    else:
        dataset = client.create_dataset(
            LANGSMITH_DATASET_NAME,
            description="Multi-turn scenario golden checks for LangQuest.",
            metadata={"source_file": str(GOLDEN_FILE)},
        )

    existing_ids = {
        ex.id
        for ex in client.list_examples(dataset_id=dataset.id)
    }

    for scenario in scenarios:
        example_id = _scenario_id(scenario)
        kwargs = dict(
            dataset_id=dataset.id,
            inputs=_scenario_inputs(scenario),
            outputs=_scenario_outputs(scenario),
            metadata={"scenario_id": scenario["id"], "source_file": str(GOLDEN_FILE)},
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

def run_local(scenarios: list[dict], verbose: bool = False) -> int:
    print("\nScenario Eval")
    print("─" * 72)
    failures_total = 0

    for scenario in scenarios:
        inputs = _scenario_inputs(scenario)
        reference_outputs = _scenario_outputs(scenario)

        outputs = _run_scenario(inputs)
        result = evaluate_scenario(outputs, reference_outputs)
        score = result["score"]
        passed = score == 1.0
        failures_total += 0 if passed else 1

        status = "OK  " if passed else "FAIL"
        print(f"  {status}  {scenario['id']}  score={score:.3f}  ({scenario['description']})")

        if verbose or not passed:
            for turn_result, turn_spec in zip(outputs["transcript"], scenario["turns"]):
                expect = turn_spec.get("expect", {})
                turn_failures = _check_turn(turn_result, expect) if expect else []
                turn_ok = "✓" if not turn_failures else "✗"
                print(f"         {turn_ok} [{turn_result['input']!r:28}]  "
                      f"loc={turn_result['location']:18}  "
                      f"action={turn_result['action_result']:20}  "
                      f"lvl={turn_result['level']}  "
                      f"obj={turn_result['objectives']}")
                for f in turn_failures:
                    print(f"              ✗ {f}")
            if result["comment"] != "All checks passed.":
                print(f"         → {result['comment']}")
            print()

    print("─" * 72)
    total = len(scenarios)
    print(f"  Result: {total - failures_total}/{total} scenarios fully passed")
    return 1 if failures_total else 0


# ---------------------------------------------------------------------------
# LangSmith runner
# ---------------------------------------------------------------------------

def run_langsmith(scenarios: list[dict]) -> int:
    from langsmith import Client

    client = Client()
    dataset_name = _ensure_langsmith_dataset(client, scenarios)
    examples = list(
        client.list_examples(
            dataset_name=dataset_name,
            example_ids=[_scenario_id(s) for s in scenarios],
        )
    )

    results = client.evaluate(
        _run_scenario,
        data=examples,
        evaluators=[evaluate_scenario],
        experiment_prefix="langquest-scenarios",
        description="Multi-turn LangQuest scenario checks against golden expectations.",
        metadata={"evaluator": "evaluate_scenario"},
        max_concurrency=1,
        blocking=True,
    )
    print(f"LangSmith experiment: {results.experiment_name}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-turn scenario evals")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show every turn")
    parser.add_argument(
        "--langsmith", action="store_true",
        help="Upload dataset + evaluator feedback to LangSmith",
    )
    parser.add_argument("filter", nargs="?", default="", help="Filter by scenario id or keyword")
    args = parser.parse_args()

    scenarios = json.loads(GOLDEN_FILE.read_text())
    if args.filter:
        needle = args.filter.lower()
        scenarios = [
            s for s in scenarios
            if needle in s["id"].lower() or needle in s["description"].lower()
        ]
        if not scenarios:
            print(f"No scenarios matched {args.filter!r}")
            sys.exit(1)

    warm_lore_index()

    if args.langsmith:
        if not (os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")):
            print("ERROR: Set LANGSMITH_API_KEY to upload LangSmith evals.")
            sys.exit(2)
        sys.exit(run_langsmith(scenarios))

    sys.exit(run_local(scenarios, verbose=args.verbose))


if __name__ == "__main__":
    main()
