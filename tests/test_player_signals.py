"""
Golden tests for deterministic player-profile signals.

Run:  python tests/test_player_signals.py
Run (verbose):  python tests/test_player_signals.py -v
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from graph.nodes.analyst_node import analyst_node, analyze_player_input
from state.game_state import create_initial_state

GOLDEN_FILE = Path(__file__).parent / "golden_player_signals.json"


def run_case(case: dict) -> tuple[bool, dict]:
    signal = analyze_player_input(case["input"])
    state = create_initial_state("Tester")
    state["raw_player_input"] = case["input"]
    state["last_player_input"] = case["input"].lower()
    state["token_budget"] = 5000
    state["token_budget_discovered"] = True
    updates = analyst_node(state)

    ok = True
    if "min_attitude_delta" in case:
        ok = ok and signal["attitude_delta"] >= case["min_attitude_delta"]
    if "max_attitude_delta" in case:
        ok = ok and signal["attitude_delta"] <= case["max_attitude_delta"]
    if "min_curiosity_delta" in case:
        ok = ok and signal["curiosity_delta"] >= case["min_curiosity_delta"]
    ok = ok and signal["token_penalty"] == case["expected_penalty"]

    if case["expected_penalty"]:
        ok = ok and updates.get("tokens_spent_session") == case["expected_penalty"]
    else:
        ok = ok and "tokens_spent_session" not in updates

    return ok, {"signal": signal, "updates": updates}


def run(verbose: bool = False) -> None:
    cases = json.loads(GOLDEN_FILE.read_text())
    passed = 0
    failed = 0

    print("\nPlayer Signal Test Suite")
    print("-" * 60)

    for i, case in enumerate(cases, 1):
        ok, output = run_case(case)
        passed += 1 if ok else 0
        failed += 0 if ok else 1
        if verbose or not ok:
            status = "OK" if ok else "FAIL"
            signal = output["signal"]
            print(f"  {status} [{i:02d}] {case['description']}")
            print(f"        input:       {case['input']}")
            print(f"        attitude:    {signal['attitude_delta']}")
            print(f"        curiosity:   {signal['curiosity_delta']}")
            print(f"        penalty:     {signal['token_penalty']}")
            print()

    total = passed + failed
    pct = int(100 * passed / total) if total else 0
    print("-" * 60)
    print(f"  Result: {passed}/{total} passed ({pct}%)")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run player signal golden tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all cases")
    args = parser.parse_args()
    run(verbose=args.verbose)
