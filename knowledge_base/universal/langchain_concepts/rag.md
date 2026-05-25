# RAG — Retrieval Augmented Generation

## What RAG is

RAG stands for **Retrieve, Augment, Generate**:

1. **Retrieve** — search a vector store for documents relevant to the current query
2. **Augment** — add those documents to the prompt as context
3. **Generate** — let the model answer using that context

Without RAG, the model only knows what was in its training data. With RAG, it can access specific, up-to-date, private information — like the history of your game world.

## Why vectors

Text is often converted to **embedding vectors** — lists of numbers that represent meaning. Similar text → similar vectors. LangQuest starts with a local persisted lore index of PDF chunks, and can move to ChromaDB embeddings later.

When you search, your query is also embedded, and we find the stored vectors closest to it using cosine similarity.

```python
# Store a memory
collection.add(
    documents=["The player freed Sable in the east wing — session 1"],
    embeddings=[embed("The player freed Sable in the east wing — session 1")],
    ids=["memory_001"]
)

# Retrieve relevant memories
results = collection.query(
    query_embeddings=[embed("the east wing")],
    n_results=3
)
```

## In LangQuest

The **Lore RAG Node** runs every turn. It:
1. Takes the current situation as a query
2. Searches the local PDF lore index for relevant chunks
3. Returns the top matches with similarity scores
4. Passes them to the DM as context

This is why the DM can speak from lore it was not directly prompted with by hand. Not because the AI remembered — because the RAG system retrieved it.

**The well is a RAG system.** You queried it (looked in). It retrieved (the note). It returned relevant context (the budget warning).

## X-Ray shows you this

When X-Ray mode is on and RAG is active, you see:
```
RAG RETRIEVED:
  Lore 1: "Odin is the All-Father..."  [source: Legends & Lore, p.176]
  Lore 2: "Thor carries Mjolnir..."    [source: Legends & Lore, p.177]
```

This is the information the AI had when it decided what happened to you.
