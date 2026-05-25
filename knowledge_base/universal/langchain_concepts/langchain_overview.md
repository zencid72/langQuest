# LangChain, LangGraph, and LangSmith

## What LangChain is

LangChain is a framework for building applications around language models. It provides common pieces for LLM apps: chat models, prompts, output parsers, retrievers, tools, and composable runnables.

In LangQuest terms, LangChain is the spellcraft library: the reusable set of incantations that lets the DM call models, retrieve context, parse answers, and connect steps together.

## What LangGraph is

LangGraph is for stateful, graph-based applications. You define a state object, add nodes that read and update that state, and connect those nodes with edges. The graph decides which node runs next.

In LangQuest terms, LangGraph is the dungeon map. The player is the state, each room is a node, and each legal path is an edge. When the player moves, the graph carries the state forward.

## What LangSmith is

LangSmith is the observability and evaluation layer. It records traces, model inputs and outputs, retrieved documents, metadata, feedback, datasets, and experiment results.

In LangQuest terms, LangSmith is the observatory above the dungeon. It lets you see why the DM chose an action, which lore chunks were retrieved, how many tokens were spent, and whether a run matched the expected golden behavior.

## How they work together in LangQuest

LangQuest uses LangGraph to move state through nodes. It uses LangChain integrations to call chat models, split documents, and retrieve context. It uses LangSmith tracing around AI and RAG operations so the important decisions are visible without globally tracing every Python function.

The fantasy layer and the product layer are meant to reinforce each other:

- A node is both a room in the world and a function in the graph.
- State is both the player record and the LangGraph state object.
- Retrieval is both the Kirjasto catalog and RAG.
- Tracing is both the LangSmith observatory and the record of what the AI saw.
- Golden datasets are both prophecy scrolls and test cases for expected behavior.
