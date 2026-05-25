"""Builds and compiles the LangQuest LangGraph.

 V1 graph:  input_node → analyst_node → rag_node → dm_node → rules_node → answer_node → narrative_node → display_node → END

analyst_node updates deterministic player signals such as attitude and
curiosity. rag_node retrieves lore chunks for the request. dm_node uses AI to
choose the legal action for the player's request. rules_node validates and
applies that action. answer_node responds to in-world questions. narrative_node
can then paint atmospheric scene descriptions for safe scene-setting actions.

V2 will add:  state_update_node
V4 will add:  memory_writer_node, bible_writer_node
"""
from langgraph.graph import StateGraph, END

from state.game_state import GameState
from graph.nodes.input_node import input_node
from graph.nodes.analyst_node import analyst_node
from graph.nodes.rag_node import rag_node
from graph.nodes.dm_node import dm_node
from graph.nodes.rules_node import rules_node
from graph.nodes.answer_node import answer_node
from graph.nodes.narrative_node import narrative_node
from graph.nodes.display_node import display_node


def build_graph():
    builder = StateGraph(GameState)

    builder.add_node("input", input_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("rag", rag_node)
    builder.add_node("dm", dm_node)
    builder.add_node("rules", rules_node)
    builder.add_node("answer", answer_node)
    builder.add_node("narrative", narrative_node)
    builder.add_node("display", display_node)

    builder.set_entry_point("input")
    builder.add_edge("input", "analyst")
    builder.add_edge("analyst", "rag")
    builder.add_edge("rag", "dm")
    builder.add_edge("dm", "rules")
    builder.add_edge("rules", "answer")
    builder.add_edge("answer", "narrative")
    builder.add_edge("narrative", "display")
    builder.add_edge("display", END)

    return builder.compile()
