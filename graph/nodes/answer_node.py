"""Answer node — traced AI responses for questions and harmless free actions."""
import os

from ai.tracing import trace_ai_operation
from state.game_state import GameState
from world.locations import LOCATIONS

_llm = None
_provider = None

_ANSWER_SYSTEM = """\
You are the Dungeon Master answering an in-world question in LangQuest.

Use the current scene first. Retrieved context may include fantasy lore,
LangQuest concept notes, and LangChain/LangSmith product documentation. When
the player asks about AI concepts, answer accurately from the product docs and
translate the idea into the fantasy scene. If the player asks about LangQuest,
treat that as a question about the LangChain/LangGraph/LangSmith learning
universe as expressed through the game world. When the player asks about myth or
the world, use the lore and optionally tie it back to AI concepts. If retrieved
context does not answer the question, say so naturally and answer from the
immediate scene instead.

For LangChain/LangGraph/LangSmith/LangQuest questions:
- Use at least one concrete retrieved detail, such as nodes as Python functions,
  edges as routing decisions, state as the carried player record, RAG as
  retrieval, or LangSmith as traces/evaluation.
- Weave that detail into the current NPC or place; do not answer as a detached
  textbook.
- When fantasy/D&D-style lore is retrieved, braid it with the product detail;
  otherwise use the current room, NPC, or quest as the fantasy side of the metaphor.
- Prefer the local LangQuest concept notes over generic explanation when they
  are present.

You may add harmless local color, but do not grant items, reveal hidden
objectives, move the player, or change game state.

Write in second person or through present NPC behavior when appropriate.
Keep the answer concise: 2-5 sentences.
Plain text only."""

_FREE_ACTION_SYSTEM = """\
You are the Dungeon Master narrating a harmless free-form action in LangQuest.

Use the current scene first. Use retrieved lore only as flavor if relevant.
Resolve the action with a small, immediate consequence. You may be lightly
funny, but keep it grounded in the scene. Do not move the player, grant items,
complete objectives, reveal secrets, damage important objects, or change
inventory. If the action is aggressive, make the consequence minor and mostly
self-directed.

Write in second person, present tense. Keep it concise: 2-4 sentences.
Plain text only."""


def _init_llm():
    global _llm, _provider
    if _llm is not None:
        return _llm
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            _llm = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=220, temperature=0.5)
            _provider = "claude"
            return _llm
        except Exception:
            pass
    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            _llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=220, temperature=0.5)
            _provider = "openai"
            return _llm
        except Exception:
            pass
    return None


def _message_payload(messages: list) -> list[dict]:
    return [{"type": message.__class__.__name__, "content": message.content} for message in messages]


def _trace_inputs(inputs: dict) -> dict:
    return {
        "provider": inputs.get("provider"),
        "model": inputs.get("model"),
        "question": inputs.get("question"),
        "free_action": inputs.get("free_action"),
        "location": inputs.get("location"),
        "retrieved_lore": inputs.get("retrieved_lore"),
        "messages": _message_payload(inputs.get("messages", [])),
    }


def _trace_outputs(output: dict) -> dict:
    return output


@trace_ai_operation(
    name="ai.in_world_answer",
    tags=["dm", "answer", "rag"],
    process_inputs=_trace_inputs,
    process_outputs=_trace_outputs,
)
def _answer_with_ai(
    *,
    llm,
    messages: list,
    provider: str | None,
    model: str,
    question: str,
    location: str,
    retrieved_lore: list,
) -> dict:
    response = llm.invoke(
        messages,
        config={
            "run_name": "in_world_answer_llm",
            "tags": ["ai", "dm", "answer", provider or "unknown"],
            "metadata": {
                "location": location,
                "question": question,
                "retrieved_lore_count": len(retrieved_lore),
                "model": model,
            },
        },
    )
    usage = getattr(response, "usage_metadata", None)
    return {"answer": response.content.strip(), "usage_metadata": usage or {}}


@trace_ai_operation(
    name="ai.free_action",
    tags=["dm", "free-action", "rag"],
    process_inputs=_trace_inputs,
    process_outputs=_trace_outputs,
)
def _free_action_with_ai(
    *,
    llm,
    messages: list,
    provider: str | None,
    model: str,
    free_action: str,
    location: str,
    retrieved_lore: list,
) -> dict:
    response = llm.invoke(
        messages,
        config={
            "run_name": "free_action_llm",
            "tags": ["ai", "dm", "free-action", provider or "unknown"],
            "metadata": {
                "location": location,
                "free_action": free_action,
                "retrieved_lore_count": len(retrieved_lore),
                "model": model,
            },
        },
    )
    usage = getattr(response, "usage_metadata", None)
    return {"answer": response.content.strip(), "usage_metadata": usage or {}}


def _fallback_answer(question: str, location: str) -> str:
    text = question.lower()
    if any(term in text for term in ("langchain", "langgraph", "langsmith", "langquest", "node", "edge", "state", "rag")):
        speaker = "Mira" if location == "tavern" else "The world"
        if "edge" in text:
            return (
                f"{speaker} explains that an edge is the path logic between nodes: after one function finishes, "
                "the graph uses an edge to decide where state goes next. In LangQuest terms, every road out of "
                "a room is an edge, but Python decides which roads are real."
            )
        if "node" in text:
            return (
                f"{speaker} explains that a node is a Python function with one job: read the current state and "
                "return the updates it made. In LangQuest terms, a room, a narrator, or a rules step can behave "
                "like a node: the world is the graph, and you are the state moving through it."
            )
        if "rag" in text or "retrieval" in text:
            return (
                f"{speaker} explains that RAG searches indexed lore before the DM answers, so the reply can use "
                "relevant documents instead of memory alone. In the game, that is the Kirjasto catalog becoming "
                "context for the next bit of narration."
            )
        return (
            f"{speaker} treats LangQuest as the LangChain universe wearing a cloak: LangGraph moves state through "
            "nodes and edges, LangChain supplies model and retrieval pieces, and LangSmith watches the traces."
        )
    if "goblin" in text:
        speaker = "Mira" if location == "tavern" else "The world"
        return (
            f"{speaker} lowers her voice. \"Around here, goblins are what vague intent turns into: "
            "noise, wasted tokens, and trouble with teeth. If you mean to face one, be specific. "
            "A clear plan cuts cleaner than a heroic speech.\""
        )
    if location == "tavern" and ("drink" in text or "ale" in text or "beer" in text):
        return (
            "Mira glances at the shelves behind her. There is small beer, pine-steeped tea, "
            "and a dark house cordial that smells faintly of smoke and juniper. "
            "\"Nothing fancy,\" she says, \"but it keeps travelers from mistaking courage for wisdom.\""
        )
    return (
        "The world can answer that better when the DM model is available. "
        "For now, try asking about a visible person, object, or bit of lore."
    )


def _fallback_free_action(action: str, location: str) -> str:
    text = action.lower()
    if "kick" in text and "tree" in text:
        return (
            "You kick the tree. The tree remains impressively tree-like, while your foot "
            "files a small complaint with the rest of your body. A few dry leaves drift down "
            "as if applauding your commitment to experimental input."
        )
    if "punch" in text and "tree" in text:
        return (
            "You punch the tree. The bark accepts your argument without changing its mind. "
            "Your knuckles sting, and the path remains exactly where it was."
        )
    return (
        f"You try to {action}. The world allows the experiment, but only as flavor: "
        "nothing important changes except your confidence in trying odd ideas."
    )


def _retrieved_lore(state: GameState) -> list:
    return [
        {
            "source": item.get("source"),
            "source_kind": item.get("source_kind"),
            "title": item.get("title"),
            "url": item.get("url"),
            "page": item.get("page"),
            "score": item.get("score"),
            "excerpt": item.get("excerpt") or item.get("text", "")[:1200],
        }
        for item in state.get("retrieved_context", [])[:6]
    ]


def _lore_text(retrieved_lore: list) -> str:
    return "\n".join(
        (
            f"- [{item.get('source_kind', 'context')}] "
            f"{item.get('title') or item.get('source', 'context')} "
            f"{'(p.' + str(item.get('page')) + ')' if item.get('page') else ''} "
            f"{item.get('url', '')}: {item.get('excerpt', '')}"
        )
        for item in retrieved_lore
        if item.get("excerpt")
    )


def _answer_question(state: GameState) -> dict:
    question = state.get("raw_player_input") or state.get("question_topic", "")
    location = state.get("current_location", "village_square")
    location_data = LOCATIONS.get(location, {})
    retrieved_lore = _retrieved_lore(state)

    llm = _init_llm()
    if not llm:
        source = "scene_fallback"
        if retrieved_lore:
            source = "scene_fallback_with_lore_available"
        return {
            "narrative_response": _fallback_answer(question, location),
            "dm_heard": state.get("last_player_input", ""),
            "question_answered": True,
            "question_answer_source": source,
            "question_lore_chunks_used": len(retrieved_lore),
            "current_event_significance": 0.25 if retrieved_lore else 0.1,
            "session_events": [f"Answered question via {source}: {question}"],
        }

    lore_text = _lore_text(retrieved_lore)
    prompt = (
        f"Current location: {location}\n"
        f"Location name: {location_data.get('name', location)}\n"
        f"Scene description: {location_data.get('description', '')}\n"
        f"Player question: {question}\n"
        f"Retrieved lore:\n{lore_text or '(none)'}\n\n"
        "Answer in-world."
    )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [SystemMessage(content=_ANSWER_SYSTEM), HumanMessage(content=prompt)]
        model = getattr(llm, "model", None) or getattr(llm, "model_name", None) or llm.__class__.__name__
        result = _answer_with_ai(
            llm=llm,
            messages=messages,
            provider=_provider,
            model=model,
            question=question,
            location=location,
            retrieved_lore=retrieved_lore,
        )
        answer = result["answer"]
        usage = result.get("usage_metadata")
        if usage:
            tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        else:
            tokens_used = (len(prompt) + len(_ANSWER_SYSTEM) + len(answer)) // 4
        return {
            "narrative_response": answer,
            "dm_heard": state.get("last_player_input", ""),
            "question_answered": True,
            "question_answer_source": "ai_rag" if retrieved_lore else "ai_scene",
            "question_lore_chunks_used": len(retrieved_lore),
            "current_event_significance": 0.45 if retrieved_lore else 0.25,
            "tokens_spent_session": state.get("tokens_spent_session", 0) + tokens_used,
            "session_events": [
                f"Answered question via {'AI + RAG' if retrieved_lore else 'AI scene context'}: {question}"
            ],
            "messages": [f"Player asked: {question}", f"DM answered: {answer}"],
        }
    except Exception:
        source = "scene_fallback_after_ai_error"
        return {
            "narrative_response": _fallback_answer(question, location),
            "dm_heard": state.get("last_player_input", ""),
            "question_answered": True,
            "question_answer_source": source,
            "question_lore_chunks_used": len(retrieved_lore),
            "current_event_significance": 0.2 if retrieved_lore else 0.1,
            "session_events": [f"Answered question via {source}: {question}"],
        }


def _resolve_free_action(state: GameState) -> dict:
    action = state.get("free_action") or state.get("raw_player_input", "")
    location = state.get("current_location", "village_square")
    location_data = LOCATIONS.get(location, {})
    retrieved_lore = _retrieved_lore(state)

    llm = _init_llm()
    if not llm:
        return {
            "narrative_response": _fallback_free_action(action, location),
            "dm_heard": state.get("last_player_input", ""),
            "free_action_resolved": True,
            "question_answer_source": "free_action_fallback_with_lore" if retrieved_lore else "free_action_fallback",
            "question_lore_chunks_used": len(retrieved_lore),
            "current_event_significance": 0.15,
            "session_events": [f"Resolved free action: {action}"],
        }

    lore_text = _lore_text(retrieved_lore)
    prompt = (
        f"Current location: {location}\n"
        f"Location name: {location_data.get('name', location)}\n"
        f"Scene description: {location_data.get('description', '')}\n"
        f"Player free action: {action}\n"
        f"Retrieved lore:\n{lore_text or '(none)'}\n\n"
        "Resolve the free action safely."
    )

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [SystemMessage(content=_FREE_ACTION_SYSTEM), HumanMessage(content=prompt)]
        model = getattr(llm, "model", None) or getattr(llm, "model_name", None) or llm.__class__.__name__
        result = _free_action_with_ai(
            llm=llm,
            messages=messages,
            provider=_provider,
            model=model,
            free_action=action,
            location=location,
            retrieved_lore=retrieved_lore,
        )
        answer = result["answer"]
        usage = result.get("usage_metadata")
        if usage:
            tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        else:
            tokens_used = (len(prompt) + len(_FREE_ACTION_SYSTEM) + len(answer)) // 4
        return {
            "narrative_response": answer,
            "dm_heard": state.get("last_player_input", ""),
            "free_action_resolved": True,
            "question_answer_source": "free_action_ai_rag" if retrieved_lore else "free_action_ai_scene",
            "question_lore_chunks_used": len(retrieved_lore),
            "current_event_significance": 0.3 if retrieved_lore else 0.2,
            "tokens_spent_session": state.get("tokens_spent_session", 0) + tokens_used,
            "session_events": [f"Resolved free action via AI: {action}"],
            "messages": [f"Player tried: {action}", f"DM resolved: {answer}"],
        }
    except Exception:
        return {
            "narrative_response": _fallback_free_action(action, location),
            "dm_heard": state.get("last_player_input", ""),
            "free_action_resolved": True,
            "question_answer_source": "free_action_fallback_after_ai_error",
            "question_lore_chunks_used": len(retrieved_lore),
            "current_event_significance": 0.15,
            "session_events": [f"Resolved free action after AI error: {action}"],
        }


def answer_node(state: GameState) -> dict:
    if state.get("action_result") == "free_action":
        return _resolve_free_action(state)
    if state.get("action_result") == "ask_question":
        return _answer_question(state)
    return {}
