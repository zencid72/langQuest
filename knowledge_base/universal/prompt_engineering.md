# Prompt Engineering

## The core principle

A prompt is an instruction to a language model. Like any instruction, clarity beats length.

The model doesn't think. It predicts. It generates the most statistically likely continuation of your text. A vague prompt has many likely continuations — the model picks one, possibly the wrong one, and generates more tokens explaining itself.

## The five dimensions of a good prompt

**1. Specificity** — Who, what, where, when, how.  
Not: "help with the quest"  
But: "help me find the hidden entrance to the library's restricted section"

**2. Context** — What does the model need to know to answer well?  
Not: "what should I do?"  
But: "I have 15 health, I'm at the crossroads, and I have a rope and a key"

**3. Format** — Tell the model how to respond.  
Not: "explain RAG"  
But: "explain RAG in one sentence, using the library as an example"

**4. Role** — Who is the model being?  
A DM speaks differently than an analyst. Be explicit.

**5. Constraints** — What are the limits?  
"In under 50 words." "Only choose from these three options." "Do not repeat my input."

## Prompt efficiency scoring

In LangQuest, your prompts are scored on:
- Token cost (lower is better)
- Specificity (how much context you gave)
- Outcome accuracy (did the model do what you wanted?)

The Prompt Efficiency Score is the ratio of outcome quality to tokens spent.

## The single best habit

Before sending a prompt, ask: *Does the model have everything it needs to answer without guessing?*

If the answer is no — add what's missing. Three extra words of context can save 200 tokens of confusion.
