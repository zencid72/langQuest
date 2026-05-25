"""DM node — AI chooses the action to apply, Python validates the result."""
import json
import os
import re

from ai.tracing import trace_ai_operation
from state.game_state import GameState
from world.locations import LOCATIONS

_llm = None
_dm_provider = None

_META_COMMANDS = {"xray", "x", "/x", "/xray", "quit", "exit", "q", "bye", ":q", "help", "h", "?"}
_QUESTION_STARTERS = ("who ", "what ", "where ", "when ", "why ", "how ", "do ", "does ", "can ", "is ", "are ")
_FREE_ACTION_VERBS = {
    "kick", "punch", "tap", "touch", "push", "pull", "smell", "lick", "hug",
    "wave", "sing", "shout", "yell", "knock", "throw", "poke", "prod",
}
_DM_ROUTING_TOKEN_CAP = 75

_SYSTEM = """\
You are the Dungeon Master for LangQuest, an AI-native text adventure.

Your job is to interpret what the player is trying to do and choose the command
Python should apply next. Python owns the rules and state changes. You choose
only a safe command; you do not invent inventory, locations, rewards, or facts.
Use Retrieved lore to understand names, mythology, artifacts, and tone. Treat it
as reference material, not as permission to bypass Legal actions.

Reply as compact JSON only:
{
  "chosen_action": "exact command for Python, or clarify",
  "confidence": 0.0,
  "reason": "short reason",
  "clarification": "short in-world reply if the request cannot map to a command"
}

Rules:
- Prefer a command from Legal actions.
- You may include a query after a legal base action: "search rag" is valid when
  Legal actions contains "search".
- If the player asks an informational in-world question, choose "ask <topic>".
  This is valid when "ask" appears in Legal actions. Examples:
  "what do you have to drink?" -> "ask drinks";
  "who is Odin?" -> "ask odin";
  "what do I know about this tree?" -> "ask tree".
- If the player attempts a plausible physical action that is not a legal path,
  choose "free <action>". This is valid when "free" appears in Legal actions.
  Use it for harmless or silly actions like "kick the tree" or "sing to Mira".
  The free-action narrator may describe a small consequence, but it must not
  move the player, grant items, complete objectives, or change inventory.
- If the player refers to an obvious object/action in the current scene, choose
  that action even if their wording is natural.
- If nothing fits, use "clarify" and write a helpful in-world clarification.
- JSON only. No markdown."""


def _init_llm():
    global _llm, _dm_provider
    if _llm is not None:
        return _llm

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic

            _llm = ChatAnthropic(
                model="claude-haiku-4-5-20251001",
                max_tokens=180,
                temperature=0.2,
            )
            _dm_provider = "claude"
            return _llm
        except Exception:
            pass

    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI

            _llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=180, temperature=0.2)
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
        "player_input": inputs.get("player_input"),
        "location": inputs.get("location"),
        "legal_actions": inputs.get("legal_actions"),
        "world_context": inputs.get("world_context"),
        "messages": _message_payload(inputs.get("messages", [])),
    }


def _trace_outputs(output: dict) -> dict:
    return output


def _trace_local_inputs(inputs: dict) -> dict:
    return {
        "player_input": inputs.get("player_input"),
        "normalized": inputs.get("normalized"),
        "location": inputs.get("location"),
        "legal_actions": inputs.get("legal_actions"),
        "decision_kind": inputs.get("decision_kind"),
    }


@trace_ai_operation(
    name="ai.dm_decision",
    tags=["dm", "decision"],
    process_inputs=_trace_inputs,
    process_outputs=_trace_outputs,
)
def _choose_action_with_ai(
    *,
    llm,
    messages: list,
    provider: str | None,
    model: str,
    player_input: str,
    location: str,
    legal_actions: list,
    world_context: dict,
) -> dict:
    response = llm.invoke(
        messages,
        config={
            "run_name": "dm_decision_llm",
            "tags": ["ai", "dm", "decision", provider or "unknown"],
            "metadata": {
                "location": location,
                "legal_actions": legal_actions,
                "player_input": player_input,
                "model": model,
            },
        },
    )
    usage = getattr(response, "usage_metadata", None)
    return {
        "raw_response": response.content,
        "decision": _parse_decision(response.content),
        "usage_metadata": usage or {},
    }


@trace_ai_operation(
    name="ai.dm_local_decision",
    tags=["dm", "decision", "local"],
    process_inputs=_trace_local_inputs,
    process_outputs=_trace_outputs,
)
def _choose_action_locally(
    *,
    player_input: str,
    normalized: str,
    location: str,
    legal_actions: list,
    decision_kind: str,
    chosen_action: str,
    reason: str,
) -> dict:
    """Traceable local DM routing for no-model or deterministic decisions."""
    return {
        "decision": {
            "chosen_action": chosen_action,
            "confidence": 1.0 if decision_kind == "direct_scene_alias" else 0.65,
            "reason": reason,
            "clarification": "",
        },
        "player_input": player_input,
        "normalized": normalized,
        "location": location,
        "legal_actions": legal_actions,
        "decision_kind": decision_kind,
    }


def _parse_decision(content: str) -> dict:
    text = content.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "chosen_action": "clarify",
        "confidence": 0,
        "reason": "The DM response was not valid JSON.",
        "clarification": "The world hesitates. Try saying that a little more plainly.",
    }


def _is_allowed(chosen: str, legal_actions: list[str]) -> bool:
    if not legal_actions:
        return True
    return any(chosen == action or chosen.startswith(action + " ") for action in legal_actions)


def _matches(text: str, patterns: list) -> bool:
    return any(text == pattern or text.startswith(pattern + " ") for pattern in patterns)


def _normalized_alias_text(text: str) -> str:
    replacements = {
        "bar tender": "bartender",
        "bar keep": "barkeep",
        "inn keeper": "innkeeper",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _matches_scene_alias(normalized: str, location: str) -> bool:
    alias_normalized = _normalized_alias_text(normalized)
    location_data = LOCATIONS.get(location, {})
    for aliases in location_data.get("exits", {}).values():
        if _matches(normalized, aliases) or _matches(alias_normalized, aliases):
            return True
    for aliases in location_data.get("actions", {}).values():
        if _matches(normalized, aliases) or _matches(alias_normalized, aliases):
            return True
    return False


def _looks_like_question(normalized: str) -> bool:
    return normalized.endswith("?") or normalized.startswith(_QUESTION_STARTERS)


def _looks_like_free_action(normalized: str) -> bool:
    first = normalized.split(maxsplit=1)[0] if normalized else ""
    return first in _FREE_ACTION_VERBS


def _fallback_action(normalized: str, legal_actions: list[str]) -> str:
    if "ask" in legal_actions and _looks_like_question(normalized):
        topic = normalized.rstrip("?")
        for prefix in (
            "ask aino if she has any books on ",
            "ask aino if she has books on ",
            "ask aino about ",
            "ask aino ",
            "what do you have to ",
            "what do you have ",
            "who is ",
            "what is ",
            "tell me about ",
        ):
            if topic.startswith(prefix):
                topic = topic[len(prefix):]
                break
        return f"ask {topic}".strip()
    if "free" in legal_actions and _looks_like_free_action(normalized):
        return f"free {normalized}"
    # Let rules_node's richer alias tables validate natural phrases when the
    # model is unavailable. It can return "unknown" safely if nothing matches.
    return normalized


def dm_node(state: GameState) -> dict:
    normalized = state.get("last_player_input", "").strip().lower()
    raw = state.get("raw_player_input", normalized).strip()

    if not normalized or normalized in _META_COMMANDS:
        return {}

    legal_actions = list(state.get("legal_outcomes", []))
    location = state.get("current_location", "village_square")
    can_answer_question = _looks_like_question(normalized)
    if not can_answer_question and _matches_scene_alias(normalized, location):
        local = _choose_action_locally(
            player_input=raw,
            normalized=normalized,
            location=location,
            legal_actions=legal_actions,
            decision_kind="direct_scene_alias",
            chosen_action=normalized,
            reason="Player input matched a local scene alias.",
        )
        decision = local["decision"]
        return {
            "last_player_input": decision["chosen_action"],
            "dm_heard": normalized if normalized != state.get("last_player_input", "") else state.get("dm_heard", ""),
            "dm_reason": decision["reason"],
            "dm_clarification": "",
        }

    can_free_action = _looks_like_free_action(normalized)
    effective_legal_actions = (
        legal_actions if "ask" in legal_actions or not can_answer_question
        else legal_actions + ["ask"]
    )
    if can_free_action and "free" not in effective_legal_actions:
        effective_legal_actions = effective_legal_actions + ["free"]
    location_data = LOCATIONS.get(location, {})
    world_context = {
        "location_name": location_data.get("name", location),
        "location_description": location_data.get("description", ""),
        "current_concept": state.get("current_concept", ""),
        "completed_objectives": state.get("completed_objectives", []),
        "retrieved_context": state.get("retrieved_context", []),
    }

    llm = _init_llm()
    if not llm or not effective_legal_actions:
        chosen = _fallback_action(normalized, effective_legal_actions)
        local = _choose_action_locally(
            player_input=raw,
            normalized=normalized,
            location=location,
            legal_actions=effective_legal_actions,
            decision_kind="local_fallback",
            chosen_action=chosen,
            reason="No DM model available; local routing chose the safest command.",
        )
        decision = local["decision"]
        return {
            "last_player_input": decision["chosen_action"],
            "dm_heard": decision["chosen_action"] if decision["chosen_action"] != normalized else state.get("dm_heard", ""),
            "dm_reason": decision["reason"],
            "dm_clarification": "",
        }

    retrieved_context = [
        {
            "source": item.get("source"),
            "page": item.get("page"),
            "score": item.get("score"),
            "text": item.get("text", ""),
        }
        for item in state.get("retrieved_context", [])
    ]

    prompt = (
        f"Current location: {location}\n"
        f"Location description: {world_context['location_description']}\n"
        f"Current concept: {world_context['current_concept']}\n"
        f"Completed objectives: {world_context['completed_objectives']}\n"
        f"Retrieved lore: {json.dumps(retrieved_context, ensure_ascii=True)}\n"
        f"Legal actions: {', '.join(effective_legal_actions)}\n"
        f"Player says: {raw!r}\n"
        f"Normalized input: {normalized!r}\n"
        "Choose the next command."
    )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=prompt),
        ]
        model = getattr(llm, "model", None) or getattr(llm, "model_name", None) or llm.__class__.__name__
        result = _choose_action_with_ai(
            llm=llm,
            messages=messages,
            provider=_dm_provider,
            model=model,
            player_input=raw,
            location=location,
            legal_actions=effective_legal_actions,
            world_context=world_context,
        )
        decision = result["decision"]
        chosen = str(decision.get("chosen_action", "")).strip().lower().rstrip(".")
        reason = str(decision.get("reason", "")).strip()

        usage = result.get("usage_metadata")
        if usage:
            tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        else:
            tokens_used = (len(prompt) + len(_SYSTEM) + len(result.get("raw_response", ""))) // 4
        accounted_tokens = min(tokens_used, _DM_ROUTING_TOKEN_CAP)
        token_update = (
            {"tokens_spent_session": state.get("tokens_spent_session", 0) + accounted_tokens}
            if state.get("token_budget_discovered", False)
            else {}
        )

        if chosen == "clarify" or not _is_allowed(chosen, effective_legal_actions):
            clarification = str(decision.get("clarification", "")).strip()
            if not clarification:
                clarification = "The world does not quite understand that. Try one of the visible paths or objects."
            return {
                "dm_heard": "",
                "dm_reason": reason or "clarification",
                "dm_clarification": clarification,
                "messages": [f"Player: {raw}", f"DM clarified: {clarification}"],
                **token_update,
            }

        return {
            "last_player_input": chosen,
            "dm_heard": chosen if chosen != normalized else state.get("dm_heard", ""),
            "dm_reason": reason,
            "dm_clarification": "",
            "messages": [f"Player: {raw}", f"DM chose: {chosen}"],
            **token_update,
        }
    except Exception:
        chosen = _fallback_action(normalized, legal_actions)
        return {
            "last_player_input": chosen,
            "dm_heard": chosen if chosen != normalized else state.get("dm_heard", ""),
            "dm_reason": "fallback after DM error",
            "dm_clarification": "",
        }
