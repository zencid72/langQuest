"""Narrative node — AI scene painter for Level 2 tree/tunnel locations.

Runs after rules_node. For tree/tunnel locations it takes the plain-text
skeleton produced by rules_node and calls the DM (Claude Haiku or GPT-4o-mini)
to paint a richer, atmospheric description. Costs tokens — that is the point.

For all other locations it returns {} and the rules_node narrative is shown as-is.
"""
import os

from ai.tracing import trace_ai_operation
from state.game_state import GameState

_llm = None
_dm_provider = None

_AI_LOCATIONS = {"archive_approach", "tree_exterior", "tree_interior", "tunnel_right", "tunnel_left"}
_AI_ACTIONS = {
    "look",
    "move_archive_approach",
    "move_tree",
    "enter_tree",
    "exit_tree",
    "move_tunnel_right",
    "move_tunnel_left",
    "move_tree_interior",
}

_SYSTEM = """\
You are the Dungeon Master narrating LangQuest — a text adventure where LangGraph \
concepts are woven into a fantasy world. Nodes, edges, state, and branching paths exist \
as real things in Thornhaven.

Your task: take a plain scene description and enhance it with atmosphere and sensory detail.

Rules:
- Keep ALL facts from the input exactly as stated — do not add or remove interactive options
- Write in second person ("You see...", "You feel..."), present tense
- Weave in graph/AI metaphors when they fit naturally: paths as edges, choices as branches, \
what you carry as state, memory as context
- Add 2-3 sentences of sensory detail that creates tension and wonder
- Plain text only — no markdown, no formatting, no special characters
- Total output: 4-6 sentences, no more"""


def _init_llm():
    global _llm, _dm_provider
    if _llm is not None:
        return _llm
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            _llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=220, temperature=0.7)
            _dm_provider = "claude"
            return _llm
        except Exception:
            pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            _llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=220, temperature=0.7)
            _dm_provider = "openai"
            return _llm
        except Exception:
            pass
    return None


def _message_payload(messages: list) -> list[dict]:
    return [
        {
            "type": message.__class__.__name__,
            "content": message.content,
        }
        for message in messages
    ]


def _trace_inputs(inputs: dict) -> dict:
    return {
        "provider": inputs.get("provider"),
        "model": inputs.get("model"),
        "location": inputs.get("location"),
        "scene_context": inputs.get("scene_context"),
        "messages": _message_payload(inputs.get("messages", [])),
    }


def _trace_outputs(output: dict) -> dict:
    return output


@trace_ai_operation(
    name="ai.narrative_scene_painter",
    tags=["narrative", "prompt"],
    process_inputs=_trace_inputs,
    process_outputs=_trace_outputs,
)
def _enhance_scene_with_ai(
    *,
    llm,
    messages: list,
    provider: str | None,
    model: str,
    location: str,
    scene_context: dict,
) -> dict:
    response = llm.invoke(
        messages,
        config={
            "run_name": "narrative_scene_painter_llm",
            "tags": ["ai", "narrative", provider or "unknown"],
            "metadata": {
                "location": location,
                "scene_context": scene_context,
                "model": model,
            },
        },
    )
    usage = getattr(response, "usage_metadata", None)
    return {
        "enhanced": response.content.strip(),
        "content": response.content,
        "usage_metadata": usage or {},
    }


def narrative_node(state: GameState) -> dict:
    location = state.get("current_location", "")
    if location not in _AI_LOCATIONS:
        return {}

    if state.get("action_result", "") not in _AI_ACTIONS:
        return {}

    skeleton = state.get("narrative_response", "")
    if not skeleton:
        return {}

    llm = _init_llm()
    if not llm:
        return {}

    has_key = "found_key" in state.get("completed_objectives", [])
    chest_opened = "opened_chest" in state.get("completed_objectives", [])
    retrieved = state.get("retrieved_context", [])[:3]
    lore_context = "\n".join(
        f"- {chunk.get('source', 'lore')} p.{chunk.get('page', '?')}: {chunk.get('excerpt', '')[:700]}"
        for chunk in retrieved
        if chunk.get("excerpt")
    )
    ctx = (
        f"Location: {location}. Player has key: {has_key}. Chest opened: {chest_opened}."
        + (f"\nRetrieved lore to color the scene without changing facts:\n{lore_context}" if lore_context else "")
    )

    prompt = f"{ctx}\n\nScene to enhance:\n{skeleton}\n\nEnhanced description:"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=prompt),
        ]
        model = getattr(llm, "model", None) or getattr(llm, "model_name", None) or llm.__class__.__name__
        scene_context = {
            "has_key": has_key,
            "chest_opened": chest_opened,
            "skeleton": skeleton,
            "retrieved_lore_count": len(retrieved),
            "retrieved_lore": [
                {
                    "source": chunk.get("source"),
                    "page": chunk.get("page"),
                    "score": chunk.get("score"),
                    "excerpt": chunk.get("excerpt", "")[:700],
                }
                for chunk in retrieved
            ],
        }
        result = _enhance_scene_with_ai(
            llm=llm,
            messages=messages,
            provider=_dm_provider,
            model=model,
            location=location,
            scene_context=scene_context,
        )
        enhanced = result["enhanced"]

        usage = result.get("usage_metadata")
        if usage:
            tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        else:
            tokens_used = (len(prompt) + len(_SYSTEM) + len(enhanced)) // 4

        result = {"narrative_response": enhanced}
        if state.get("token_budget_discovered", False):
            result["tokens_spent_session"] = state.get("tokens_spent_session", 0) + tokens_used
        return result
    except Exception:
        return {}
