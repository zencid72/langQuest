"""Location definitions and narration for LangQuest V1."""

LOCATIONS = {
    "village_square": {
        "name": "Thornhaven — Kyläaukio",
        "concept": "tila",
        "description": (
            "You stand in the heart of [bold]Thornhaven[/bold] as morning mist curls between the cobblestones.\n\n"
            "To your [bold]WEST[/bold]: an ancient stone [bold cyan]KAIVO[/bold cyan] (well), wrapped in ivy. "
            "A rope vanishes into darkness below.\n"
            "Ahead: the [bold cyan]VAELTAVA SOLMU[/bold cyan] — the Wandering Node — warm light "
            "spilling through leaded windows. Smoke curls from the chimney.\n"
            "To the [bold]NORTH[/bold]: a dirt [bold cyan]ROAD[/bold cyan] that disappears into the dark edge of Thornwood.\n\n"
            "[dim]Somewhere nearby, a rooster crows. You are the tila. Today, the graph begins.[/dim]"
        ),
        "exits": {
            "tavern": ["tavern", "go tavern", "enter tavern", "wandering node", "inn", "enter inn", "go inn"],
            "well": [
                "well", "go well", "go to well", "go to the well", "approach well",
                "approach the well", "examine well", "look well", "look in well",
                "look in the well", "old well", "look at well", "look at the well",
                "west", "go west", "go to west", "head west", "walk west",
            ],
            "north": ["north", "go north", "road", "thornwood", "forest", "go road", "north road"],
        },
        "actions": {
            "look": ["look", "examine", "l", "survey", "observe", "where am i", "look around", "describe", "scene", "search"],
            "help": ["help", "h", "?", "commands", "what can i do", "options"],
        },
    },

    "tavern": {
        "name": "Vaeltava Solmu",
        "concept": "solmu",
        "description": (
            "The [bold]Vaeltava Solmu[/bold] — the Wandering Node — is warm and dim. "
            "Three round tables. A fireplace that pops and crackles. "
            "The smell of pine smoke and something herbal.\n\n"
            "[bold cyan]MIRA[/bold cyan] — stout, sharp-eyed innkeeper — polishes a glass behind the bar without looking up.\n\n"
            "[dim]\"New face,\" she says. \"Good. The last one ran north before they were ready. "
            "Never came back.\"[/dim]\n\n"
            "You can: [bold]talk to MIRA[/bold]  ·  sit at a [bold]TABLE[/bold]  ·  [bold]LEAVE[/bold]"
        ),
        "exits": {
            "village_square": ["leave", "go back", "exit", "back", "outside", "square", "village", "go outside", "go village"],
        },
        "actions": {
            "look": ["look", "examine", "l", "look around", "survey", "describe"],
            "talk_mira": [
                "talk mira", "speak mira", "mira", "innkeeper", "talk to mira",
                "ask mira", "bartender", "bar tender", "barkeep", "bar keep",
                "talk bartender", "talk to bartender", "talk to the bartender",
                "talk bar tender", "talk to bar tender", "talk to the bar tender",
                "talk barkeep", "talk to barkeep", "talk to the barkeep",
                "talk innkeeper", "talk to innkeeper", "talk to the innkeeper",
                "talk inn keeper", "talk to inn keeper", "talk to the inn keeper",
                "speak bartender", "speak to bartender", "speak with bartender",
                "speak barkeep", "speak to barkeep", "speak with barkeep",
                "speak innkeeper", "speak to innkeeper", "speak with innkeeper",
                "speak to mira", "speak with mira", "greet mira", "hello mira", "hi mira",
            ],
            "sit": ["sit", "sit down", "table", "chair", "sit at table", "take a seat", "have a seat"],
            "mira_tokens": [
                "ask tokens", "tokens", "ask about tokens", "ask mira tokens",
                "token economy", "token budget", "budget", "what are tokens",
                "how do tokens work", "tell me about tokens", "explain tokens",
                "conserve", "save tokens", "token", "kehote", "prompt cost",
            ],
            "help": ["help", "h", "?", "commands", "options"],
        },
    },

    "well": {
        "name": "Kaivo — The Old Well",
        "concept": "haku",
        "description": (
            "You lean over the edge of the [bold]kaivo[/bold] — the well. Cold air rises from below.\n\n"
            "Your reflection stares back at you — slightly confused. Which is fair.\n\n"
            "At the bottom, catching the light... [italic]is that a note?[/italic]\n\n"
            "You fish it out with the rope. The paper is damp but legible:\n\n"
            "  [bold]\"Token reserve: +45,000. Spend wisely, Tila.[/bold]\n"
            "  [bold]The Goblin watches every word.[/bold]\n"
            "  [bold]                    — The Analyst\"[/bold]\n\n"
            "[dim]Haku: retrieval. You queried the kaivo. It searched. It returned context.\n"
            "That is exactly what RAG does — in a much deeper well.[/dim]"
        ),
        "description_before_mira": (
            "You lean over the edge of the [bold]kaivo[/bold] — the well. Cold air rises from below.\n\n"
            "Your reflection stares back at you — slightly confused. Which is fair.\n\n"
            "At the bottom, catching the light... [italic]is that a note?[/italic]\n\n"
            "You fish it out with the rope. The paper is damp but legible:\n\n"
            "  [bold]\"Token reserve: +45,000. Spend wisely, Tila.[/bold]\n"
            "  [bold]The Goblin watches every word.[/bold]\n"
            "  [bold]                    — The Analyst\"[/bold]\n\n"
            "Forty-five thousand of something. Spend wisely. But what are tokens, exactly?\n\n"
            "[dim]The innkeeper at the [bold]Vaeltava Solmu[/bold] — the tavern — "
            "looks like someone who would know.[/dim]"
        ),
        "exits": {
            "village_square": ["back", "leave", "go back", "square", "village", "return", "go village", "step back"],
        },
        "actions": {
            "look": ["look", "examine", "l", "peer", "look down", "look in", "gaze", "look into"],
            "drop": ["drop", "throw", "toss", "throw something", "throw rock", "drop rock", "toss rock", "drop stone"],
            "help": ["help", "h", "?", "commands", "options"],
        },
    },
}

LOCATION_RESPONSES = {
    "village_square": {
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]look[/cyan]    — survey the village square\n"
            "  [cyan]well[/cyan]    — examine the old well to the west\n"
            "  [cyan]tavern[/cyan]  — enter The Wandering Node\n"
            "  [cyan]north[/cyan]   — look toward the road into Thornwood\n"
            "  [cyan]xray[/cyan]    — toggle X-Ray mode (see the state object)\n"
            "  [cyan]help[/cyan]    — show this list\n"
            "  [cyan]quit[/cyan]    — leave the game"
        ),
    },
    "tavern": {
        "look": (
            "The Vaeltava Solmu. Warm, dim, and full of things left unsaid.\n"
            "Mira knows things. The fire knows nothing, but it's warm.\n\n"
            "[dim]Try [cyan]mira[/cyan] to talk to the innkeeper, "
            "or [cyan]ask tokens[/cyan] to ask her about your budget.[/dim]"
        ),
        # talk_mira has two variants — assembled in rules_node based on state
        "talk_mira_intro": (
            "Mira sets down the glass and looks at you properly for the first time.\n\n"
            "\"Seven levels,\" she says. \"Seven [italic]solmut[/italic] — nodes — in the Thornwood. "
            "Each one does one job. No more.\"\n\n"
            "She slides a small card across the bar:\n"
            "  [dim]tila · solmu · kaari · haku · jäljitys · kehotteet · Goblin[/dim]\n"
            "  [dim]state · node · edge · retrieval · tracing · prompts · The Goblin[/dim]\n\n"
            "\"You're standing in level one. This village is a [italic]solmu[/italic]. "
            "You are the [italic]tila[/italic] — the state. "
            "Every choice you make updates what the world knows about you.\"\n\n"
            "She pauses. Refills a glass that didn't need refilling.\n\n"
            "\"One more thing. [bold]Tokens.[/bold]\" She sets the glass down precisely. "
            "\"Every word you send to the AI costs them. Every word it sends back costs them. "
            "The vaguer your question, the more expensive the answer — "
            "'What do I do?' might cost four hundred. "
            "'Ask the blacksmith if the north gate opens after dark' costs sixty.\""
        ),
        "talk_mira_hint_kaivo": (
            "\n\nShe nods toward the west-facing window. "
            "\"There's an old [italic]kaivo[/italic] — a well — just outside. "
            "The Analyst left a note there with your starting budget. "
            "Worth a look before you spend anything.\"\n\n"
            "[dim](Tip: try [cyan]ask tokens[/cyan] for more. "
            "The DM read your state: kaivo not yet visited — hint added.)[/dim]"
        ),
        "talk_mira_knows_kaivo": (
            "\n\nShe glances toward the door, then back. "
            "\"You've already been out to the kaivo.\" Not a question. "
            "\"Then you know your budget. Fifty thousand. "
            "The Goblin at level six will try to drain every last one.\"\n\n"
            "[dim](Tip: try [cyan]ask tokens[/cyan] for more. "
            "The DM read your state: kaivo already visited — hint omitted.)[/dim]"
        ),
        # mira_tokens also has two variants
        "mira_tokens_intro": (
            "Mira leans against the bar and considers where to start.\n\n"
            "\"Think of a language model like a very fast reader who charges by the word. "
            "Input tokens: what you say to it. "
            "Output tokens: what it says back. "
            "Both cost. Both count against your budget.\"\n\n"
            "She picks up a piece of chalk and writes on the back of a menu:\n\n"
            "  [dim]BAD:  'help me figure out the thing with the door'[/dim]\n"
            "  [dim]      → model guesses, hedges, asks clarifying questions[/dim]\n"
            "  [dim]      → you pay for all of that uncertainty[/dim]\n\n"
            "  [dim]GOOD: 'pick the lock on the east door using the iron pin'[/dim]\n"
            "  [dim]      → model answers directly, no guessing needed[/dim]\n"
            "  [dim]      → costs a fraction[/dim]\n\n"
            "\"Specificity is efficiency. Efficiency is survival.\"\n\n"
            "She slides the chalk away. "
            "\"The Goblin at the end of the Thornwood gets stronger every time you're vague. "
            "It feeds on wasted tokens. "
            "I've watched travelers go in with fifty thousand and come out owing.\""
        ),
        "mira_tokens_hint_kaivo": (
            "\n\n\"The kaivo outside shows your running total. "
            "The Analyst updates it every turn — go check it.\"\n\n"
            "[dim](Concept: kehote — prompt efficiency. "
            "The DM read your state: kaivo not yet visited — directed you there.)[/dim]"
        ),
        "mira_tokens_knows_kaivo": (
            "\n\n\"You've seen the kaivo — so you know the number. "
            "Fifty thousand. The meter runs every time the AI speaks.\"\n\n"
            "[dim](Concept: kehote — prompt efficiency. "
            "The DM read your state: kaivo visited — skipped the redirect.)[/dim]"
        ),
        "sit": (
            "You pull out a chair. The fire crackles. The table is worn smooth "
            "by a thousand travelers before you.\n\n"
            "Someone has carved into the wood:\n"
            "  [italic]'Be specific or be lost.'[/italic]\n\n"
            "[dim]Good advice. In here, and everywhere beyond.[/dim]"
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]mira[/cyan]         — talk to the innkeeper\n"
            "  [cyan]ask tokens[/cyan]   — ask Mira about the token economy\n"
            "  [cyan]sit[/cyan]          — sit at a table\n"
            "  [cyan]leave[/cyan]        — step back outside\n"
            "  [cyan]xray[/cyan]         — toggle X-Ray mode\n"
            "  [cyan]help[/cyan]         — show this list"
        ),
    },
    "well": {
        "look": (
            "The kaivo is deep. Cold. Full of metaphor.\n\n"
            "Also: there was a note at the bottom. You already have it.\n"
            "The rope sways gently."
        ),
        "look_before_mira": (
            "The kaivo is deep. Cold.\n\n"
            "The note you found mentions a token reserve — 45,000 more tokens — "
            "but the number sits in your hand without much meaning.\n\n"
            "[dim]The innkeeper at the Vaeltava Solmu might know what tokens are "
            "and why this number matters. She seems like someone who would.[/dim]"
        ),
        "drop": (
            "You find a pebble and toss it in.\n\n"
            "One... two... three...\n\n"
            "[italic]plunk.[/italic]\n\n"
            "Deep. Very deep.\n\n"
            "[dim]In a world with full memory, dropping something here would create "
            "an event: 'Player dropped object in kaivo — session 1.'\n"
            "The world would remember. NPCs would notice. It would matter.[/dim]"
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]look[/cyan]    — peer into the kaivo\n"
            "  [cyan]drop[/cyan]    — throw something in\n"
            "  [cyan]back[/cyan]    — return to the Kyläaukio\n"
            "  [cyan]xray[/cyan]    — toggle X-Ray mode"
        ),
    },
}

NORTH_ROAD_LOCKED = (
    "You walk to the edge of the village. The road stretches into the Thornwood.\n\n"
    "The air smells of pine and something electric — potential energy, unspent.\n\n"
    "A wooden sign has been hammered into the dirt:\n\n"
    "  [bold]╔═══════════════════════════════════╗[/bold]\n"
    "  [bold]║  THORNWOOD — LEVEL 2 LOCKED       ║[/bold]\n"
    "  [bold]║  Complete Level 1 to continue.    ║[/bold]\n"
    "  [bold]╚═══════════════════════════════════╝[/bold]\n\n"
    "[dim]The three tasks: talk to Mira · visit the Kaivo · toggle X-Ray[/dim]"
)

NORTH_ROAD_UNLOCKED = (
    "The road north is open.\n\n"
    "The Thornwood parts before you. Through the trees, a stone building rises — "
    "the [bold cyan]KIRJASTO[/bold cyan], the Archive.\n\n"
    "The air smells of old paper and something algorithmic.\n\n"
    "[dim]Level 2: haku — retrieval. The Kirjasto teaches RAG.[/dim]"
)

LEVEL_1_COMPLETE_TEXT = (
    "[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n"
    "[bold green]  LEVEL 1 COMPLETE — KYLÄAUKIO MASTERED    [/bold green]\n"
    "[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n\n"
    "Mira looks up from across the square. She nods once.\n\n"
    "[dim]\"You've seen the tila. You've touched the haku. "
    "You know a solmu does one job.\n"
    "The road north is open. The Kirjasto is waiting.\"[/dim]\n\n"
    "[bold]+500 tokens earned — Level 1 complete[/bold]"
)

# ── Level 2: Kirjasto ──────────────────────────────────────────────────────────

LOCATIONS.update({
    "archive_approach": {
        "name": "The Archive Approach",
        "concept": "kaari",
        "description": (
            "The north road leaves Thornhaven and opens into a quiet clearing. "
            "Ahead stands the stone Kirjasto, its tall windows dark with shelves and old paper. "
            "To the east, an ancient black-barked tree leans over the grounds, roots lifting the path like a warning.\n\n"
            "The road has become a fork: enter the [bold cyan]BUILDING[/bold cyan] or approach the [bold cyan]TREE[/bold cyan]."
        ),
        "exits": {
            "kirjasto": [
                "archive", "building", "kirjasto", "enter archive", "enter building",
                "go archive", "go to archive", "go building", "go to building",
                "inside", "doors", "front door",
            ],
            "tree_exterior": [
                "tree", "threshold tree", "ancient tree", "black tree", "outside",
                "grounds", "go tree", "go to tree", "go to the tree",
                "approach tree", "approach the tree", "walk to tree",
                "walk to the tree", "head to tree", "head to the tree", "east",
            ],
            "village_square": ["south", "back", "village", "return", "go back", "go south"],
        },
        "actions": {
            "look": ["look", "examine", "l", "look around", "survey", "observe", "describe"],
            "help": ["help", "h", "?", "commands", "options"],
        },
    },
    "kirjasto": {
        "name": "Kirjasto — The Archive",
        "concept": "haku",
        "description": (
            "The Kirjasto is vast and quiet. Stone shelves rise to the vaulted ceiling, "
            "stacked with scrolls, tablets, and books that seem to rearrange themselves when you aren't looking.\n\n"
            "At the centre: a brass [bold cyan]CATALOG[/bold cyan] — a wheel of indexed cards, "
            "spinning slowly on its own.\n\n"
            "[bold cyan]AINO[/bold cyan] — the Archivist — stands behind the reference desk. "
            "She watches you enter with the calm expression of someone who has already "
            "retrieved this moment from memory.\n\n"
            "[dim]\"Welcome, \" she says. \"Tell me what you're looking for. "
            "The Kirjasto will find what's close.\"[/dim]\n\n"
            "Beyond the east-facing window, an unusual tree dominates the grounds — "
            "its bark near-black, roots lifting the cobblestones.\n\n"
            "You can: talk to [bold]AINO[/bold]  ·  use the [bold]CATALOG[/bold]  ·  "
            "[bold]SEARCH[/bold] for a topic  ·  go [bold]OUTSIDE[/bold]  ·  go [bold]SOUTH[/bold]"
        ),
        "exits": {
            "village_square": ["south", "go south", "leave", "back", "village", "go back", "exit"],
            "tree_exterior": ["outside", "tree", "go outside", "grounds", "east", "mysterious tree", "strange tree", "explore outside"],
        },
        "actions": {
            "look": ["look", "examine", "l", "look around", "survey", "describe"],
            "talk_aino": [
                "aino", "talk aino", "speak aino", "talk to aino", "archivist",
                "librarian", "ask aino", "hello aino", "hi aino", "speak to aino",
            ],
            "catalog": [
                "catalog", "catalogue", "look catalog", "examine catalog",
                "index", "card catalog", "browse", "browse catalog",
            ],
            "search": [
                "search", "query", "find", "look for", "search for",
                "retrieve", "fetch", "haku",
            ],
            "read": [
                "read", "open", "open book", "read book", "study",
            ],
            "help": ["help", "h", "?", "commands", "options"],
        },
    },
})

LOCATION_RESPONSES.update({
    "archive_approach": {
        "look": (
            "The clearing holds two strong pulls. The Kirjasto waits ahead, built for retrieval: "
            "questions, catalogs, context. The black-barked tree waits to the east, built for branching: "
            "doors, tunnels, consequences.\n\n"
            "[dim]Choose the [cyan]building[/cyan] to learn haku/RAG, or the [cyan]tree[/cyan] to follow the kaari/edge.[/dim]"
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]building[/cyan] — enter the Kirjasto archive\n"
            "  [cyan]tree[/cyan]     — approach the Threshold Tree\n"
            "  [cyan]south[/cyan]    — return to Thornhaven\n"
            "  [cyan]look[/cyan]     — study the fork\n"
            "  [cyan]xray[/cyan]     — toggle X-Ray mode"
        ),
    },
    "kirjasto": {
        "look": (
            "The Kirjasto breathes with the quiet authority of indexed knowledge.\n\n"
            "Every book here is embedded — not just physically, but semantically. "
            "The catalog doesn't search by title. It searches by [italic]meaning[/italic].\n\n"
            "[dim]This is a RAG system. You are inside the retrieval node.[/dim]"
        ),
        "talk_aino": (
            "Aino folds her hands on the desk.\n\n"
            "\"RAG — haku — works in three steps. Retrieve. Augment. Generate.\n\n"
            "First: your query becomes a vector. A list of numbers representing meaning.\n"
            "Second: we compare it against everything in the Kirjasto using similarity. "
            "Not keyword matching — [italic]meaning[/italic] matching.\n"
            "Third: the closest documents become context. The AI answers using that context.\"\n\n"
            "She gestures at the spinning catalog. "
            "\"Without haku, the AI only knows what it learned in training. "
            "With haku, it can access anything indexed here — "
            "your world's history, its lore, what you did last session.\"\n\n"
            "She slides a card across the desk:\n"
            "  [dim]similarity score · embedding · vector store · context window[/dim]\n\n"
            "[dim](Aino's relationship score: 0 → neutral. Concept: haku/RAG explained.)[/dim]"
        ),
        "catalog": (
            "You spin the brass catalog wheel. The cards blur past — "
            "thousands of entries, each with a small number beside it.\n\n"
            "  [dim]\"solmu ja tehtävät\"          similarity: —[/dim]\n"
            "  [dim]\"kaari-reititys ehdollinen\"   similarity: —[/dim]\n"
            "  [dim]\"tila pysyvyys\"               similarity: —[/dim]\n"
            "  [dim]\"tokenien talous\"              similarity: —[/dim]\n"
            "  [dim]\"haku-arkkitehtuuri\"           similarity: —[/dim]\n\n"
            "The numbers beside each entry are similarity scores. "
            "When you search, they fill in. The highest score rises to the top.\n\n"
            "[dim]This is the index of a vector store. "
            "In V4, this catalog will search real ChromaDB embeddings.[/dim]\n\n"
            "[dim]Try [cyan]search[/cyan] followed by a topic to see retrieval in action.[/dim]"
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]aino[/cyan]    — talk to the Archivist about RAG\n"
            "  [cyan]catalog[/cyan] — examine the index\n"
            "  [cyan]search[/cyan]  — query the Kirjasto (try: search tokens, search nodes)\n"
            "  [cyan]read[/cyan]    — read the last retrieved book\n"
            "  [cyan]south[/cyan]   — return to Kyläaukio\n"
            "  [cyan]xray[/cyan]    — toggle X-Ray mode"
        ),
    },
})

# ── Simulated RAG: hardcoded "retrieved" results by topic ──────────────────────
KIRJASTO_BOOKS = {
    "token": {
        "title": "Tokenien Talous",
        "score": 0.94,
        "excerpt": (
            "Tokens are the atomic unit of language models. A word is typically 1-3 tokens. "
            "A paragraph is 100-300 tokens. Every call to the model costs tokens — "
            "input tokens to read your prompt, output tokens to generate the response. "
            "Precision reduces output tokens. Vagueness multiplies them."
        ),
    },
    "node": {
        "title": "Solmurakenteen Periaatteet",
        "score": 0.91,
        "excerpt": (
            "A node (solmu) is a function. It receives the current state (tila) "
            "and returns a dict of updates. One job. The input_node reads text. "
            "The rules_node applies logic. The display_node renders output. "
            "Nodes communicate only through state — never directly."
        ),
    },
    "solmu": {
        "title": "Solmurakenteen Periaatteet",
        "score": 0.91,
        "excerpt": (
            "A node (solmu) is a function. It receives the current state (tila) "
            "and returns a dict of updates. One job. The input_node reads text. "
            "The rules_node applies logic. The display_node renders output. "
            "Nodes communicate only through state — never directly."
        ),
    },
    "edge": {
        "title": "Kaari-reititys ja Ehdolliset Polut",
        "score": 0.89,
        "excerpt": (
            "An edge (kaari) connects two nodes (solmut). A conditional edge "
            "reads the state and routes to different nodes based on what it finds. "
            "If health < 20, route to death_node. If prompt efficient, route to reward_node. "
            "The path through the graph IS the decision."
        ),
    },
    "kaari": {
        "title": "Kaari-reititys ja Ehdolliset Polut",
        "score": 0.89,
        "excerpt": (
            "An edge (kaari) connects two nodes (solmut). A conditional edge "
            "reads the state and routes to different nodes based on what it finds. "
            "If health < 20, route to death_node. If prompt efficient, route to reward_node. "
            "The path through the graph IS the decision."
        ),
    },
    "state": {
        "title": "Tila — Mitä Maailma Muistaa",
        "score": 0.96,
        "excerpt": (
            "State (tila) is the data object flowing through the graph. "
            "Every node reads it. Every node can update it. "
            "It is the only memory the system has between nodes. "
            "Fields with reducers (like session_events) accumulate. "
            "Fields without reducers are overwritten. You are the tila."
        ),
    },
    "tila": {
        "title": "Tila — Mitä Maailma Muistaa",
        "score": 0.96,
        "excerpt": (
            "State (tila) is the data object flowing through the graph. "
            "Every node reads it. Every node can update it. "
            "It is the only memory the system has between nodes. "
            "Fields with reducers (like session_events) accumulate. "
            "Fields without reducers are overwritten. You are the tila."
        ),
    },
    "rag": {
        "title": "Haku-arkkitehtuuri — Retrieve, Augment, Generate",
        "score": 0.98,
        "excerpt": (
            "RAG (haku) retrieves relevant documents from a vector store, "
            "adds them to the prompt as context, then generates a response using that context. "
            "Without RAG, the model only knows training data. "
            "With RAG, it knows your world's history. Every session. Every event. "
            "The Kirjasto IS a RAG system. You are inside the retrieval node."
        ),
    },
    "haku": {
        "title": "Haku-arkkitehtuuri — Retrieve, Augment, Generate",
        "score": 0.98,
        "excerpt": (
            "RAG (haku) retrieves relevant documents from a vector store, "
            "adds them to the prompt as context, then generates a response using that context. "
            "Without RAG, the model only knows training data. "
            "With RAG, it knows your world's history. Every session. Every event. "
            "The Kirjasto IS a RAG system. You are inside the retrieval node."
        ),
    },
    "prompt": {
        "title": "Kehotteen Tarkkuus",
        "score": 0.87,
        "excerpt": (
            "A prompt (kehote) is an instruction to the model. "
            "Vague prompts cost more — the model rambles, guesses, hedges. "
            "Specific prompts cost less — the model responds directly. "
            "The difference between 'do something' and 'pick the lock with the hairpin' "
            "is the difference between 400 tokens and 80."
        ),
    },
}

NO_RESULTS_TEXT = (
    "The catalog wheel spins. The similarity scores all read: [dim]0.00[/dim]\n\n"
    "[italic]No strong match found.[/italic]\n\n"
    "[dim]The Kirjasto knows: tila · solmu · kaari · haku · rag · token · prompt · state · node · edge[/dim]\n"
    "[dim]Try one of those.[/dim]"
)

# ── Level 2: The Threshold Tree and Tunnels ───────────────────────────────────
# Descriptions here are plain-text skeletons — narrative_node enhances them with AI.

LOCATIONS.update({
    "tree_exterior": {
        "name": "The Threshold Tree",
        "concept": "kaari",
        "description": (
            "A massive ancient tree stands at the edge of the Kirjasto grounds. "
            "Its bark is near-black and cold to touch. The roots have lifted the cobblestones around it. "
            "Set into the trunk at chest height: a small wooden door, iron-bound and ajar by an inch."
        ),
        "exits": {
            "archive_approach": ["back", "south", "approach", "fork", "return", "go back", "leave"],
            "tree_interior": ["open door", "door", "enter", "go in", "enter tree", "inside", "open", "through"],
        },
        "actions": {
            "look": ["look", "examine", "examine tree", "l", "look around", "observe", "inspect", "describe"],
            "help": ["help", "h", "?", "commands"],
        },
    },
    "tree_interior": {
        "name": "Inside the Threshold Tree",
        "concept": "kaari",
        "description": (
            "The inside of the tree opens into a space far larger than the trunk should allow. "
            "The wood walls are warm and faintly luminescent — the grain runs in circuit-like patterns. "
            "Two tunnels lead from the far wall — one going right, one going left. Both slope gently down."
        ),
        "exits": {
            "tree_exterior": ["back", "outside", "exit", "leave", "go back", "go outside", "out"],
            "tunnel_right": ["right", "go right", "right tunnel", "take right", "east"],
            "tunnel_left": ["left", "go left", "left tunnel", "take left", "west"],
        },
        "actions": {
            "look": ["look", "examine", "l", "look around", "survey", "describe"],
            "help": ["help", "h", "?"],
        },
    },
    "tunnel_right": {
        "name": "The Chest Chamber",
        "concept": "kaari",
        "description": (
            "The right tunnel opens into a stone chamber. "
            "At the center sits a heavy iron-bound chest. "
            "Three padlocks hang from the clasp, green with age but solid."
        ),
        "exits": {
            "tree_interior": ["back", "return", "leave", "go back", "junction", "tunnel", "go back to junction"],
        },
        "actions": {
            "look": ["look", "examine", "l", "examine chest", "inspect chest", "look around", "chest", "inspect"],
            "open_chest": [
                "open", "open chest", "try chest", "pry", "force chest",
                "unlock", "try to open", "use key", "key", "insert key",
                "unlock chest", "try key", "use the key", "unlock with key", "use key on chest",
            ],
            "help": ["help", "h", "?"],
        },
    },
    "tunnel_left": {
        "name": "The Stone Floor Passage",
        "concept": "kaari",
        "description": (
            "The left tunnel curves around a mossy corner. "
            "The floor is old stone flags, some unevenly set. "
            "One slab near the left wall sits slightly raised, its edges clean of moss — moved before."
        ),
        "exits": {
            "tree_interior": ["back", "return", "leave", "go back", "junction", "tunnel"],
        },
        "actions": {
            "look": ["look", "examine", "l", "look around", "survey", "describe"],
            "examine_floor": [
                "examine floor", "floor", "loose stone", "stone", "examine stone",
                "lift stone", "look down", "check floor", "move stone", "pry stone",
                "push stone", "pull stone", "inspect floor", "look at floor", "stones",
                "investigate floor", "check stone", "loose slab", "raised stone",
                "examine the floor", "inspect the floor", "check the floor",
                "look at the floor",
            ],
            "take_key": ["take key", "pick up key", "grab key", "get key", "take the key", "pick key"],
            "help": ["help", "h", "?"],
        },
    },
})

LOCATION_RESPONSES.update({
    "tree_exterior": {
        "look": (
            "A massive ancient tree stands at the edge of the Kirjasto grounds. "
            "Its bark is near-black and cold to touch. The roots have lifted the cobblestones. "
            "Set into the trunk at chest height: a small wooden door, iron-bound and ajar by an inch."
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]look[/cyan]       — examine the tree\n"
            "  [cyan]open door[/cyan]  — push through the door\n"
            "  [cyan]back[/cyan]       — return to the Archive approach\n"
            "  [cyan]xray[/cyan]       — toggle X-Ray mode"
        ),
    },
    "tree_interior": {
        "look": (
            "The inside of the tree opens into a space far larger than the trunk should allow. "
            "The wood walls are warm and faintly luminescent — the grain runs in patterns like circuit diagrams. "
            "Two tunnels lead from the far wall — one going right, one going left. Both slope gently down."
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]look[/cyan]   — survey the interior\n"
            "  [cyan]right[/cyan]  — take the right tunnel\n"
            "  [cyan]left[/cyan]   — take the left tunnel\n"
            "  [cyan]back[/cyan]   — exit the tree\n"
            "  [cyan]xray[/cyan]   — toggle X-Ray mode"
        ),
    },
    "tunnel_right": {
        "look": (
            "The right tunnel opens into a stone chamber. "
            "At the center sits a heavy iron-bound chest. "
            "Three padlocks hang from the clasp, green with age but solid. "
            "The chest has not been opened."
        ),
        "look_opened": (
            "The chest stands open. The crystalline vial is gone — you already claimed the token essence."
        ),
        "locked": (
            "The chest does not move. Three iron padlocks hold the clasp shut. "
            "A key is needed."
        ),
        "opened": (
            "The key slides into the first lock. Then the second. Then the third. "
            "The padlocks fall away. The chest opens with the sound of a long exhale. "
            "Inside: a crystalline vial of amber light. Token essence. 10,000 units."
        ),
        "already_open": (
            "The chest is open. The crystalline vial is gone. You have already claimed the token essence."
        ),
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]look[/cyan]        — examine the chest\n"
            "  [cyan]open chest[/cyan]  — try to open it\n"
            "  [cyan]back[/cyan]        — return to the junction\n"
            "  [cyan]xray[/cyan]        — toggle X-Ray mode"
        ),
    },
    "tunnel_left": {
        "look": (
            "The left tunnel curves around a mossy corner. "
            "The floor is old stone flags. "
            "One slab near the left wall sits slightly raised, its edges clean of moss — it has been moved before."
        ),
        "examine_found": (
            "You kneel and work your fingers under the loose stone. It lifts with effort. "
            "Wrapped in oilskin beneath: a small iron key. Three notches cut into the bit. "
            "You take it."
        ),
        "examine_empty": (
            "You lift the stone again. The hollow beneath is empty. You already have the key."
        ),
        "take_have": "You already have the key.",
        "take_need_look": "There is no key visible here. Try examining the stone floor.",
        "help": (
            "[bold]What you can do here:[/bold]\n"
            "  [cyan]look[/cyan]          — examine the tunnel\n"
            "  [cyan]examine floor[/cyan] — investigate the stone floor\n"
            "  [cyan]back[/cyan]          — return to the junction\n"
            "  [cyan]xray[/cyan]          — toggle X-Ray mode"
        ),
    },
})

LEVEL_2_COMPLETE_TEXT = (
    "[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n"
    "[bold green]  LEVEL 2 COMPLETE — THE THRESHOLD TREE     [/bold green]\n"
    "[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n\n"
    "The token essence pulses once in your hand, then is absorbed.\n\n"
    "[dim]You followed two paths. You found the key. You opened the chest.\n"
    "That is what conditional edges do — the state told you which path was right.\n"
    "The path through the graph IS the decision.[/dim]\n\n"
    "[bold]+500 tokens — Level 2 complete. More of the Thornwood awaits.[/bold]"
)

UNKNOWN_ACTION_TEXT = (
    "You try: [italic]\"{action}\"[/italic]\n\n"
    "The world considers this. Carefully. Then tilts its head.\n\n"
    "[dim]Try [cyan]help[/cyan] for a list of what's possible here, "
    "or [cyan]look[/cyan] to get your bearings.[/dim]"
)
