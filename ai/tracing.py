"""LangSmith tracing helpers.

The app keeps global LangChain/LangGraph tracing off so ordinary game nodes do
not become traces. AI work opts in explicitly with traceable wrappers.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any, TypeVar

from langsmith import traceable
from langsmith.run_helpers import tracing_context

T = TypeVar("T")

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def configure_scoped_tracing() -> None:
    """Disable ambient tracing while preserving LangSmith auth/project env vars."""
    if os.getenv("LANGADVENTURE_GLOBAL_TRACING", "").strip().lower() in _TRUTHY:
        return

    for key in (
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING",
        "LANGCHAIN_TRACING_V2",
    ):
        if os.getenv(key):
            os.environ[key] = "false"


def invoke_without_tracing(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run non-AI code with LangSmith disabled, even if env tracing was set."""
    with tracing_context(enabled=False):
        return func(*args, **kwargs)


def trace_ai_operation(
    *,
    name: str,
    tags: list[str],
    process_inputs: Callable[[dict], dict] | None = None,
    process_outputs: Callable[..., dict] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Create an explicit LangSmith trace for AI-facing work."""
    trace_setting = os.getenv("LANGADVENTURE_TRACE_AI", "").strip().lower()
    enabled = trace_setting not in _FALSY and bool(
        os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    )
    return traceable(
        run_type="chain",
        name=name,
        tags=["ai", *tags],
        project_name=os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT"),
        enabled=enabled,
        process_inputs=process_inputs,
        process_outputs=process_outputs,
    )
