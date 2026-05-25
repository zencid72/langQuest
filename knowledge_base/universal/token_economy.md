# Token Economy

## What tokens actually are

When you call a language model API, you pay in **tokens** — fragments of text, roughly 3-4 characters each. The word "token" has 5 characters, so it's about 1-2 tokens. A full sentence might be 20-30 tokens.

Every call to an AI costs tokens. Claude Sonnet charges ~$3 per million input tokens and ~$15 per million output tokens. A detailed conversation can run 10,000-50,000 tokens easily.

## Why this matters for prompting

**Vague input → AI asks clarifying questions → more tokens spent.**  
**Precise input → AI answers directly → fewer tokens spent.**

If you type "do something with the thing", the model must:
1. Guess what "something" means
2. Guess what "thing" refers to
3. Generate a response covering multiple possibilities

That rambling costs tokens. You pay for every word the model generates trying to figure out what you meant.

## The Prompt Goblin

In LangQuest, the Prompt Goblin is the boss that feeds on this waste. Every vague prompt makes it stronger. Every specific, precise prompt deals damage.

**This is not metaphor. This is how it works.**

## Token budget mechanics

- Starting budget: 5,000 tokens
- The Kaivo can reveal a 45,000-token reserve
- Every AI call costs real tokens, deducted from your budget
- Budget runs out → game gets harder (the Goblin grows)
- Earn tokens back through efficient play and learning moments

## What good prompting looks like

Bad: "do something about the door"  
Good: "pick the lock on the north door using the hairpin I found in the library"

Bad: "I want to talk to someone"  
Good: "ask Mira about the Thornwood and what waits at level 3"

The specific version is clearer, faster to process, and cheaper to respond to.
