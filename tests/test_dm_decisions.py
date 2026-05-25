"""
Golden answer tests for the LangQuest DM decision node.

Run:  python tests/test_dm_decisions.py
Run (verbose):  python tests/test_dm_decisions.py -v
Run (filter):   python tests/test_dm_decisions.py -v floor
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from ai.tracing import configure_scoped_tracing
from graph.nodes import dm_node as dm
from state.game_state import create_initial_state

configure_scoped_tracing()

GOLDEN_FILE = Path(__file__).parent / "golden_dm_decisions.json"


def run_case(case: dict) -> dict:
    state = create_initial_state("Tester")
    state["current_location"] = case["location"]
    state["legal_outcomes"] = case["legal_outcomes"]
    state["raw_player_input"] = case["input"]
    state["last_player_input"] = case["input"].lower()

    result = dm.dm_node(state)
    if result.get("dm_clarification"):
        chosen = "clarify"
    else:
        chosen = result.get("last_player_input", "")
    return {"chosen_action": chosen, "result": result}


def run(verbose: bool = False, filter_text: str = "") -> None:
    if not dm._init_llm():
        print("ERROR: No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        sys.exit(1)

    cases = json.loads(GOLDEN_FILE.read_text())
    if filter_text:
        needle = filter_text.lower()
        cases = [
            c for c in cases
            if needle in c["description"].lower() or needle in c["input"].lower()
        ]

    print("\nDM Decision Test Suite")
    print("─" * 60)

    passed = 0
    failed = 0
    errors = []

    for i, case in enumerate(cases, 1):
        try:
            output = run_case(case)
            got = output["chosen_action"]
            ok = got == case["expected_action"]
            if ok:
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
                errors.append((case, got, output["result"]))

            if verbose or not ok:
                print(f"  {status} [{i:02d}] {case['description']}")
                print(f"        input:    \"{case['input']}\"")
                print(f"        expected: {case['expected_action']}")
                print(f"        got:      {got}")
                if verbose:
                    print(f"        reason:   {output['result'].get('dm_reason', '')}")
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
        for case, got, result in errors:
            print(f"    ✗ \"{case['input']}\"")
            print(f"      expected: {case['expected_action']}  got: {got}")
            if result.get("dm_reason"):
                print(f"      reason: {result['dm_reason']}")

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DM decision golden answer tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all cases, not just failures")
    parser.add_argument("filter", nargs="?", default="", help="Filter tests by keyword")
    args = parser.parse_args()
    run(verbose=args.verbose, filter_text=args.filter)
