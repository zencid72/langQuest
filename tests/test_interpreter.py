"""
Golden answer tests for the DM command interpreter.

Run locally:
  python tests/test_interpreter.py
  python tests/test_interpreter.py -v
  python tests/test_interpreter.py -v well

Upload as a LangSmith experiment:
  python tests/test_interpreter.py --langsmith

Each test feeds a natural language input + context to the same AI model used in
input_node and checks whether it returns the expected action keyword.
The suite measures pass rate so you can track interpreter quality over time.
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

from ai.tracing import configure_scoped_tracing, trace_ai_operation

configure_scoped_tracing()

GOLDEN_FILE = Path(__file__).parent / "golden_interpreter.json"
LANGSMITH_DATASET_NAME = "langquest-interpreter"

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

_llm = None
_llm_name = None


def _init_llm():
    global _llm, _llm_name
    if _llm is not None:
        return _llm, _llm_name
    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        _llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=20, temperature=0)
        _llm_name = "Claude Haiku"
    elif os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        _llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=20, temperature=0)
        _llm_name = "GPT-4o-mini"
    return _llm, _llm_name


def _message_payload(messages: list) -> list[dict]:
    return [{"type": m.__class__.__name__, "content": m.content} for m in messages]


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


# ---------------------------------------------------------------------------
# Target function
# ---------------------------------------------------------------------------

def _run_interpreter_case(inputs: dict) -> dict:
    """Interpret a single case through the AI command interpreter."""
    from langchain_core.messages import HumanMessage, SystemMessage

    llm, dm_name = _init_llm()
    if not llm:
        return {"result": "", "error": "No LLM available"}

    legal_str = ", ".join(inputs.get("legal_outcomes", []))
    prompt = (
        f"Location: {inputs['location']}\n"
        f"Legal actions: {legal_str}\n"
        f"Player says: \"{inputs['input'].lower()}\"\n"
        f"Action:"
    )
    messages = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]
    result = _interpret_with_ai(llm, messages, inputs, dm_name)
    return {"result": result["result"], "model": dm_name}


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

def evaluate_interpreter(outputs: dict, reference_outputs: dict) -> dict:
    """Exact-match check: interpreted result must equal expected."""
    got = outputs.get("result", "")
    expected = reference_outputs.get("expected", "")
    score = 1.0 if got == expected else 0.0
    return {
        "key": "interpreter_exact_match",
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
        "legal_outcomes": case.get("legal_outcomes", []),
    }


def _case_outputs(case: dict) -> dict:
    return {"expected": case["expected"]}


def _case_id(case: dict) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"langquest-interpreter/{case['description']}")


def _ensure_langsmith_dataset(client: Any, cases: list[dict]) -> str:
    if client.has_dataset(dataset_name=LANGSMITH_DATASET_NAME):
        dataset = client.read_dataset(dataset_name=LANGSMITH_DATASET_NAME)
    else:
        dataset = client.create_dataset(
            LANGSMITH_DATASET_NAME,
            description="Golden AI command-interpreter cases for LangQuest.",
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
    llm, dm_name = _init_llm()
    if not llm:
        print("ERROR: No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        return 1

    print(f"\nDM Interpreter Test Suite  [{dm_name}]")
    print("─" * 60)

    passed = 0
    failed = 0
    errors = []

    for i, case in enumerate(cases, 1):
        try:
            outputs = _run_interpreter_case(_case_inputs(case))
            result = evaluate_interpreter(outputs, _case_outputs(case))
            ok = result["score"] == 1.0

            if ok:
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗"
                errors.append((case, outputs["result"]))

            if verbose or not ok:
                print(f"  {status} [{i:02d}] {case['description']}")
                print(f"        input:    \"{case['input']}\"")
                print(f"        expected: {case['expected']}")
                if not ok:
                    print(f"        got:      {outputs['result']}")
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
        for case, got in errors:
            print(f"    ✗ \"{case['input']}\"")
            print(f"      expected: {case['expected']}  got: {got}")

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
        _run_interpreter_case,
        data=examples,
        evaluators=[evaluate_interpreter],
        experiment_prefix="langquest-interpreter",
        description="LangQuest AI command interpreter golden exact-match checks.",
        metadata={"evaluator": "evaluate_interpreter"},
        max_concurrency=1,
        blocking=True,
    )
    print(f"LangSmith experiment: {results.experiment_name}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run DM interpreter golden answer tests")
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
