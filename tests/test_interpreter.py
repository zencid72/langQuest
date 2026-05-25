"""
Golden answer tests for the DM command interpreter.

Run:  python tests/test_interpreter.py
Run (verbose):  python tests/test_interpreter.py -v
Run (filter):   python tests/test_interpreter.py -v well

Each test feeds a natural language input + context to the same AI model used in
input_node and checks whether it returns the expected action keyword.
The suite measures pass rate so you can track interpreter quality over time.
"""
import json
import os
import sys
import time
import argparse
from pathlib import Path

# Allow running from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()
from ai.tracing import configure_scoped_tracing, trace_ai_operation

configure_scoped_tracing()

GOLDEN_FILE = Path(__file__).parent / "golden_interpreter.json"

_SYSTEM = """\
You are the command interpreter for a text adventure game. Extract what the player wants to DO.

Rules:
- Reply with ONLY the action keyword(s) — nothing else, no punctuation, no extra words
- Match by intent: "I walk to the well" → "well", "chat with innkeeper" → "mira"
- Prefer the shortest exact keyword from the legal actions list
- Special commands that work anywhere — always recognize these:
    xray → "xray"
    quit / exit / stop playing / leave game → "quit"
    help / what can I do → "help"
- For library/archive search queries only: reply "search <core topic word>" (1 word topic, no filler)
  Example: "find books about RAG" → "search rag", "look for nodes" → "search node"
  Only use "search" when the legal actions list contains "search"
- Asking about tokens / budget / spending → "ask tokens"
- Lowercase only, 1–4 words max"""


def build_llm():
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=20, temperature=0), "Claude Haiku"
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", max_tokens=20, temperature=0), "GPT-4o-mini"
    return None, "none"


def _message_payload(messages: list) -> list[dict]:
    return [
        {
            "type": message.__class__.__name__,
            "content": message.content,
        }
        for message in messages
    ]


def _trace_inputs(inputs: dict) -> dict:
    case = inputs.get("case", {})
    return {
        "model": inputs.get("dm_name"),
        "description": case.get("description"),
        "location": case.get("location"),
        "legal_actions": case.get("legal_outcomes", []),
        "player_input": case.get("input"),
        "expected": case.get("expected"),
        "messages": _message_payload(inputs.get("messages", [])),
    }


def _trace_outputs(output: dict) -> dict:
    return output


@trace_ai_operation(
    name="ai.command_interpreter_golden_test",
    tags=["command-interpreter", "golden-test"],
    process_inputs=_trace_inputs,
    process_outputs=_trace_outputs,
)
def _interpret_with_ai(llm, messages: list, case: dict, dm_name: str) -> dict:
    response = llm.invoke(
        messages,
        config={
            "run_name": "command_interpreter_golden_test_llm",
            "tags": ["ai", "command-interpreter", "golden-test"],
            "metadata": {
                "model": dm_name,
                "description": case.get("description"),
                "expected": case.get("expected"),
            },
        },
    )
    return {"result": response.content.strip().lower().rstrip(".")}


def interpret(llm, case: dict) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage
    legal_str = ", ".join(case.get("legal_outcomes", []))
    prompt = (
        f"Location: {case['location']}\n"
        f"Legal actions: {legal_str}\n"
        f"Player says: \"{case['input'].lower()}\"\n"
        f"Action:"
    )
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=prompt),
    ]
    model = getattr(llm, "model", None) or getattr(llm, "model_name", None) or llm.__class__.__name__
    return _interpret_with_ai(llm, messages, case, model)["result"]


def run(verbose: bool = False, filter_text: str = "") -> None:
    cases = json.loads(GOLDEN_FILE.read_text())
    if filter_text:
        cases = [c for c in cases if filter_text.lower() in c["description"].lower()
                 or filter_text.lower() in c["input"].lower()]

    llm, dm_name = build_llm()
    if not llm:
        print("ERROR: No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        sys.exit(1)

    print(f"\nDM Interpreter Test Suite  [{dm_name}]")
    print(f"{'─' * 60}")

    passed = 0
    failed = 0
    errors = []

    for i, case in enumerate(cases, 1):
        try:
            result = interpret(llm, case)
            ok = result == case["expected"]

            if ok:
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
                errors.append((case, result))

            if verbose or not ok:
                print(f"  {status} [{i:02d}] {case['description']}")
                print(f"        input:    \"{case['input']}\"")
                print(f"        expected: {case['expected']}")
                if not ok:
                    print(f"        got:      {result}")
                print()

            time.sleep(0.1)  # avoid rate limits

        except Exception as e:
            failed += 1
            print(f"  ! [{i:02d}] ERROR — {case['description']}: {e}")

    total = passed + failed
    pct = int(100 * passed / total) if total else 0
    print(f"{'─' * 60}")
    print(f"  Result: {passed}/{total} passed  ({pct}%)")

    if errors and not verbose:
        print(f"\n  Failures:")
        for case, got in errors:
            print(f"    ✗ \"{case['input']}\"")
            print(f"      expected: {case['expected']}  got: {got}")

    print()
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run DM interpreter golden answer tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show all cases, not just failures")
    parser.add_argument("filter", nargs="?", default="", help="Filter tests by keyword")
    args = parser.parse_args()
    run(verbose=args.verbose, filter_text=args.filter)
