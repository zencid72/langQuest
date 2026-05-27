"""Rules node — pure Python logic. No AI. Sets legal outcomes and narrative per turn."""
from state.game_state import GameState, level_complete, LEVEL_OBJECTIVES
from world.locations import (
    LOCATIONS, LOCATION_RESPONSES,
    NORTH_ROAD_LOCKED, NORTH_ROAD_UNLOCKED,
    KIRJASTO_BOOKS, NO_RESULTS_TEXT,
    UNKNOWN_ACTION_TEXT,
)


def _matches(user_input: str, patterns: list) -> bool:
    return any(user_input == p or user_input.startswith(p + " ") for p in patterns)


def _add_objective(state: GameState, key: str) -> list:
    """Return the updated objectives list, adding key if not already present."""
    current = list(state.get("completed_objectives", []))
    if key not in current:
        current.append(key)
    return current


def rules_node(state: GameState) -> dict:
    raw = state.get("last_player_input", "").strip()
    location = state.get("current_location", "village_square")
    xray_mode = state.get("xray_mode", False)

    base = {
        "legal_outcomes": [],
        "narrative_response": "",
        "action_result": "",
        "level_just_completed": False,
        "dm_heard": state.get("dm_heard", ""),  # carry forward from input_node
        "dm_clarification": "",
        "question_answered": False,
        "question_answer_source": "",
        "question_lore_chunks_used": 0,
        "free_action": "",
        "free_action_resolved": False,
    }

    if state.get("dm_clarification"):
        return {
            **base,
            "narrative_response": state["dm_clarification"],
            "action_result": "dm_clarify",
            "legal_outcomes": state.get("legal_outcomes", []),
        }

    if raw == "ask" or raw.startswith("ask "):
        topic = raw[4:].strip() if raw.startswith("ask ") else state.get("raw_player_input", "").strip()
        return {
            **base,
            "narrative_response": "You ask, and the world leans closer to answer.",
            "action_result": "ask_question",
            "question_topic": topic or state.get("raw_player_input", "").strip(),
            "legal_outcomes": state.get("legal_outcomes", []),
        }

    if raw == "free" or raw.startswith("free "):
        action = raw[5:].strip() if raw.startswith("free ") else state.get("raw_player_input", "").strip()
        return {
            **base,
            "narrative_response": "You try something outside the obvious paths.",
            "action_result": "free_action",
            "free_action": action or state.get("raw_player_input", "").strip(),
            "legal_outcomes": state.get("legal_outcomes", []),
        }

    # ── Meta commands (work everywhere) ──────────────────────────────────────
    if raw in ("xray", "x", "/x", "/xray"):
        toggled = not xray_mode
        objectives = _add_objective(state, "used_xray") if toggled else list(state.get("completed_objectives", []))
        result = {
            **base,
            "xray_mode": toggled,
            "completed_objectives": objectives,
            "narrative_response": (
                "[bold cyan]X-Ray mode ENABLED.[/bold cyan] "
                "You can see the machinery beneath the world."
                if toggled else
                "[dim]X-Ray mode disabled.[/dim]"
            ),
            "action_result": "xray_toggle",
        }
        # Check level completion after adding objective
        if toggled and level_complete(1, objectives) and state.get("current_level", 1) == 1:
            result["current_level"] = 2
            result["level_just_completed"] = True
            result["tokens_earned_session"] = state.get("tokens_earned_session", 0) + 500
            result["token_budget"] = state.get("token_budget", 5000) + 500
        return result

    if raw in ("quit", "exit", "q", "bye", ":q"):
        return {
            **base,
            "quit": True,
            "narrative_response": (
                "[bold magenta]Farewell, traveler.[/bold magenta]\n\n"
                "The world holds your shape. Return anytime."
            ),
            "action_result": "quit",
        }

    # ── Route to location handler ─────────────────────────────────────────────
    handlers = {
        "village_square": _village_square,
        "tavern": _tavern,
        "well": _well,
        "archive_approach": _archive_approach,
        "kirjasto": _kirjasto,
        "tree_exterior": _tree_exterior,
        "tree_interior": _tree_interior,
        "tunnel_right": _tunnel_right,
        "tunnel_left": _tunnel_left,
    }
    handler = handlers.get(location)
    if handler:
        result = {**base, **handler(raw, state)}
        # Objective completion check after every action
        result = _check_objectives(result, state)
        return result

    return {**base, "narrative_response": "You are lost. Type [cyan]help[/cyan]."}


def _check_objectives(result: dict, state: GameState) -> dict:
    """After any action, check if a level was just completed."""
    objectives = result.get("completed_objectives", state.get("completed_objectives", []))
    current_level = state.get("current_level", 1)
    if level_complete(current_level, objectives) and not state.get("level_just_completed", False):
        if "current_level" not in result:  # don't double-promote
            result["current_level"] = current_level + 1
            result["level_just_completed"] = True
            # Read from result first — a handler may have already added tokens (e.g. chest reward)
            result["tokens_earned_session"] = result.get("tokens_earned_session", state.get("tokens_earned_session", 0)) + 500
            result["token_budget"] = result.get("token_budget", state.get("token_budget", 5000)) + 500
    return result


# ── Village Square ────────────────────────────────────────────────────────────

def _village_square(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["village_square"]["exits"]
    actions = LOCATIONS["village_square"]["actions"]
    current_level = state.get("current_level", 1)

    if _matches(inp, exits["tavern"]):
        return {
            "current_location": "tavern",
            "current_concept": "solmu",
            "narrative_response": LOCATIONS["tavern"]["description"],
            "action_result": "move_tavern",
            "session_events": ["Entered the Vaeltava Solmu tavern"],
            "legal_outcomes": ["look", "mira", "sit", "leave"],
        }

    if _matches(inp, exits["well"]):
        first_visit = "visited_kaivo" not in state.get("completed_objectives", [])
        objectives = _add_objective(state, "visited_kaivo")
        talked_to_mira = "talked_to_mira" in objectives
        description = (
            LOCATIONS["well"]["description"] if talked_to_mira
            else LOCATIONS["well"]["description_before_mira"]
        )
        result = {
            "current_location": "well",
            "current_concept": "haku",
            "narrative_response": description,
            "action_result": "move_well",
            "completed_objectives": objectives,
            "session_events": ["Approached the Kaivo"],
            "legal_outcomes": ["look", "drop", "back"],
        }
        if first_visit:
            result["token_budget"] = state.get("token_budget", 5000) + 45000
            result["token_budget_discovered"] = True
            result["tokens_earned_session"] = state.get("tokens_earned_session", 0) + 45000
            result["session_events"] = ["Approached the Kaivo", "Recovered the token reserve from the Kaivo"]
        return result

    if _matches(inp, exits["north"]):
        if current_level >= 2:
            return {
                "current_location": "archive_approach",
                "current_concept": "kaari",
                "narrative_response": NORTH_ROAD_UNLOCKED + "\n\n" + LOCATIONS["archive_approach"]["description"],
                "action_result": "move_archive_approach",
                "session_events": ["Reached the Archive approach"],
                "legal_outcomes": ["building", "archive", "tree", "look", "south"],
            }
        else:
            objectives = state.get("completed_objectives", [])
            remaining = [o for o in LEVEL_OBJECTIVES[1] if o not in objectives]
            hint = _level1_hint(remaining)
            return {
                "narrative_response": NORTH_ROAD_LOCKED + f"\n\n{hint}",
                "action_result": "look_north",
                "session_events": ["Looked toward the north road"],
                "legal_outcomes": ["tavern", "well"],
            }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATIONS["village_square"]["description"],
            "action_result": "look",
            "session_events": ["Surveyed the Kyläaukio"],
            "legal_outcomes": ["well", "tavern", "north"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["village_square"]["help"],
            "action_result": "help",
            "legal_outcomes": ["look", "well", "tavern", "north"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "help"],
    }


# ── Archive Approach ─────────────────────────────────────────────────────────

def _archive_approach(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["archive_approach"]["exits"]
    actions = LOCATIONS["archive_approach"]["actions"]

    if _matches(inp, exits["kirjasto"]):
        return {
            "current_location": "kirjasto",
            "current_concept": "haku",
            "narrative_response": LOCATIONS["kirjasto"]["description"],
            "action_result": "enter_archive",
            "session_events": ["Entered the Kirjasto"],
            "legal_outcomes": ["look", "aino", "catalog", "search", "outside", "south"],
        }

    if _matches(inp, exits["tree_exterior"]):
        return {
            "current_location": "tree_exterior",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tree_exterior"]["description"],
            "action_result": "move_tree",
            "session_events": ["Approached the Threshold Tree"],
            "legal_outcomes": ["look", "open door", "back"],
        }

    if _matches(inp, exits["village_square"]):
        return {
            "current_location": "village_square",
            "current_concept": "tila",
            "narrative_response": (
                "You follow the road south until Thornhaven gathers around you again.\n\n"
                + LOCATIONS["village_square"]["description"]
            ),
            "action_result": "move_village",
            "session_events": ["Returned from the Archive approach"],
            "legal_outcomes": ["look", "well", "tavern", "north"],
        }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATION_RESPONSES["archive_approach"]["look"],
            "action_result": "look",
            "legal_outcomes": ["building", "archive", "tree", "south"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["archive_approach"]["help"],
            "action_result": "help",
            "legal_outcomes": ["building", "archive", "tree", "south"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["building", "tree", "look", "help", "south"],
    }


def _level1_hint(remaining: list) -> str:
    hints = {
        "talked_to_mira": "  · Enter the [cyan]tavern[/cyan] and type [bold cyan]mira[/bold cyan] to speak with the innkeeper",
        "visited_kaivo":  "  · Type [bold cyan]well[/bold cyan] to visit the Kaivo to the west",
        "used_xray":      "  · Type [bold cyan]xray[/bold cyan] to toggle X-Ray mode and reveal the tila",
    }
    lines = ["[yellow]Remaining tasks:[/yellow]"] + [hints[r] for r in remaining if r in hints]
    return "\n".join(lines)


# ── Tavern ────────────────────────────────────────────────────────────────────

def _tavern(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["tavern"]["exits"]
    actions = LOCATIONS["tavern"]["actions"]

    if _matches(inp, exits["village_square"]):
        return {
            "current_location": "village_square",
            "current_concept": "tila",
            "narrative_response": (
                "You step back out into the morning air.\n\n"
                + LOCATIONS["village_square"]["description"]
            ),
            "action_result": "move_village",
            "session_events": ["Left the tavern"],
            "legal_outcomes": ["look", "well", "tavern", "north"],
        }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATIONS["tavern"]["description"],
            "action_result": "look",
            "legal_outcomes": ["mira", "sit", "leave"],
        }

    if _matches(inp, actions["talk_mira"]):
        objectives = _add_objective(state, "talked_to_mira")
        visited_kaivo = "visited_kaivo" in state.get("completed_objectives", [])
        narrative = (
            LOCATION_RESPONSES["tavern"]["talk_mira_intro"]
            + (LOCATION_RESPONSES["tavern"]["talk_mira_knows_kaivo"] if visited_kaivo
               else LOCATION_RESPONSES["tavern"]["talk_mira_hint_kaivo"])
        )
        return {
            "narrative_response": narrative,
            "action_result": "talk_mira",
            "completed_objectives": objectives,
            "session_events": ["Talked to Mira — solmu + token concepts introduced"],
            "legal_outcomes": ["ask tokens", "sit", "leave"],
        }

    if _matches(inp, actions["mira_tokens"]):
        objectives = _add_objective(state, "talked_to_mira")
        visited_kaivo = "visited_kaivo" in objectives
        narrative = (
            LOCATION_RESPONSES["tavern"]["mira_tokens_intro"]
            + (LOCATION_RESPONSES["tavern"]["mira_tokens_knows_kaivo"] if visited_kaivo
               else LOCATION_RESPONSES["tavern"]["mira_tokens_hint_kaivo"])
        )
        return {
            "narrative_response": narrative,
            "action_result": "mira_tokens",
            "completed_objectives": objectives,
            "session_events": ["Asked Mira about the token economy"],
            "legal_outcomes": ["sit", "leave", "well"],
        }

    if _matches(inp, actions["sit"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tavern"]["sit"],
            "action_result": "sit",
            "session_events": ["Sat at a table in the Vaeltava Solmu"],
            "legal_outcomes": ["mira", "leave", "look"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tavern"]["help"],
            "action_result": "help",
            "legal_outcomes": ["look", "mira", "sit", "leave"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "help"],
    }


# ── Well (Kaivo) ──────────────────────────────────────────────────────────────

def _well(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["well"]["exits"]
    actions = LOCATIONS["well"]["actions"]

    if _matches(inp, exits["village_square"]):
        return {
            "current_location": "village_square",
            "current_concept": "tila",
            "narrative_response": (
                "You step back from the kaivo.\n\n"
                + LOCATIONS["village_square"]["description"]
            ),
            "action_result": "move_village",
            "session_events": ["Left the Kaivo"],
            "legal_outcomes": ["look", "well", "tavern", "north"],
        }

    if _matches(inp, actions["look"]):
        talked_to_mira = "talked_to_mira" in state.get("completed_objectives", [])
        look_text = (
            LOCATION_RESPONSES["well"]["look"] if talked_to_mira
            else LOCATION_RESPONSES["well"]["look_before_mira"]
        )
        return {
            "narrative_response": look_text,
            "action_result": "look",
            "legal_outcomes": ["drop", "back"],
        }

    if _matches(inp, actions["drop"]):
        return {
            "narrative_response": LOCATION_RESPONSES["well"]["drop"],
            "action_result": "drop",
            "session_events": ["Dropped something in the Kaivo"],
            "legal_outcomes": ["back", "look"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["well"]["help"],
            "action_result": "help",
            "legal_outcomes": ["look", "drop", "back"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "help", "back"],
    }


# ── Kirjasto (Level 2) ────────────────────────────────────────────────────────

def _kirjasto(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["kirjasto"]["exits"]
    actions = LOCATIONS["kirjasto"]["actions"]

    if _matches(inp, exits["tree_exterior"]):
        return {
            "current_location": "tree_exterior",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tree_exterior"]["description"],
            "action_result": "move_tree",
            "session_events": ["Went outside to the Threshold Tree"],
            "legal_outcomes": ["look", "open door", "back"],
        }

    if _matches(inp, exits["village_square"]):
        return {
            "current_location": "village_square",
            "current_concept": "tila",
            "narrative_response": (
                "You step out of the Kirjasto into the cool forest air.\n\n"
                + LOCATIONS["village_square"]["description"]
            ),
            "action_result": "move_village",
            "session_events": ["Left the Kirjasto"],
            "legal_outcomes": ["look", "well", "tavern", "north"],
        }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATION_RESPONSES["kirjasto"]["look"],
            "action_result": "look",
            "legal_outcomes": ["aino", "catalog", "search", "outside", "south"],
        }

    if _matches(inp, actions["talk_aino"]):
        objectives = _add_objective(state, "talked_to_aino")
        return {
            "narrative_response": LOCATION_RESPONSES["kirjasto"]["talk_aino"],
            "action_result": "talk_aino",
            "completed_objectives": objectives,
            "session_events": ["Talked to Aino — haku/RAG concept learned"],
            "legal_outcomes": ["catalog", "search", "outside", "south"],
        }

    if _matches(inp, actions["catalog"]):
        objectives = _add_objective(state, "searched_catalog")
        return {
            "narrative_response": LOCATION_RESPONSES["kirjasto"]["catalog"],
            "action_result": "catalog",
            "completed_objectives": objectives,
            "session_events": ["Examined the Kirjasto catalog"],
            "legal_outcomes": ["search", "aino", "outside", "south"],
        }

    if _matches(inp, actions["search"]):
        # Extract the search term from the input
        parts = inp.split(None, 1)
        query = parts[1].strip() if len(parts) > 1 else ""
        return _kirjasto_search(query, state)

    if _matches(inp, actions["read"]):
        last_result = state.get("retrieved_context", [])
        if last_result:
            book = last_result[0] if last_result else {}
            objectives = _add_objective(state, "read_a_book")
            return {
                "narrative_response": (
                    f"You open [bold]{book.get('title', 'the book')}[/bold].\n\n"
                    f"{book.get('excerpt', 'The pages are blank.')}\n\n"
                    "[dim]Knowledge retrieved. Context added.[/dim]"
                ),
                "action_result": "read",
                "completed_objectives": objectives,
                "session_events": [f"Read '{book.get('title', 'a book')}' in the Kirjasto"],
                "legal_outcomes": ["search", "aino", "catalog", "outside", "south"],
            }
        return {
            "narrative_response": (
                "You reach for a book. But which one?\n\n"
                "[dim]Use [cyan]search[/cyan] first to retrieve something relevant, "
                "then [cyan]read[/cyan] what was found.[/dim]"
            ),
            "action_result": "read_empty",
            "legal_outcomes": ["search", "catalog", "aino"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["kirjasto"]["help"],
            "action_result": "help",
            "legal_outcomes": ["aino", "catalog", "search", "outside", "south"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "help", "outside", "south"],
    }


def _kirjasto_search(query: str, state: GameState) -> dict:
    """Simulate RAG retrieval with hardcoded results."""
    if not query:
        return {
            "narrative_response": (
                "The catalog wheel hovers, waiting.\n\n"
                "[dim]Try: [cyan]search rag[/cyan] · [cyan]search tila[/cyan] · "
                "[cyan]search solmu[/cyan] · [cyan]search token[/cyan][/dim]"
            ),
            "action_result": "search_empty",
            "legal_outcomes": ["search", "catalog", "aino"],
        }

    # Find matching book (simple keyword match simulating semantic search)
    key = query.lower().strip()
    book = KIRJASTO_BOOKS.get(key)

    # Try partial matches
    if not book:
        for k, v in KIRJASTO_BOOKS.items():
            if k in key or key in k:
                book = v
                break

    if not book:
        return {
            "narrative_response": NO_RESULTS_TEXT,
            "action_result": "search_no_result",
            "legal_outcomes": ["search", "catalog", "aino"],
        }

    objectives = _add_objective(state, "searched_catalog")
    return {
        "narrative_response": (
            f"The catalog wheel spins. Cards blur. It slows.\n\n"
            f"  [bold]Retrieved:[/bold] [cyan]{book['title']}[/cyan]\n"
            f"  [dim]similarity score: {book['score']}[/dim]\n\n"
            f"[italic]{book['excerpt'][:120]}...[/italic]\n\n"
            "[dim]Type [cyan]read[/cyan] to read the full entry.[/dim]"
        ),
        "action_result": "search_hit",
        "completed_objectives": objectives,
        "retrieved_context": [book],
        "session_events": [f"Searched Kirjasto for '{query}' — found '{book['title']}'"],
        "legal_outcomes": ["read", "search", "aino", "outside", "south"],
    }


# ── Threshold Tree ────────────────────────────────────────────────────────────

def _tree_exterior(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["tree_exterior"]["exits"]
    actions = LOCATIONS["tree_exterior"]["actions"]

    if _matches(inp, exits["archive_approach"]):
        return {
            "current_location": "archive_approach",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["archive_approach"]["description"],
            "action_result": "move_archive_approach",
            "legal_outcomes": ["building", "archive", "tree", "look", "south"],
        }

    if _matches(inp, exits["tree_interior"]):
        return {
            "current_location": "tree_interior",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tree_interior"]["description"],
            "action_result": "enter_tree",
            "session_events": ["Entered the Threshold Tree"],
            "legal_outcomes": ["look", "right", "left", "back"],
        }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tree_exterior"]["look"],
            "action_result": "look",
            "legal_outcomes": ["open door", "back"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tree_exterior"]["help"],
            "action_result": "help",
            "legal_outcomes": ["look", "open door", "back"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "open door", "back"],
    }


def _tree_interior(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["tree_interior"]["exits"]
    actions = LOCATIONS["tree_interior"]["actions"]

    if _matches(inp, exits["tree_exterior"]):
        return {
            "current_location": "tree_exterior",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tree_exterior"]["description"],
            "action_result": "exit_tree",
            "legal_outcomes": ["look", "open door", "back"],
        }

    if _matches(inp, exits["tunnel_right"]):
        return {
            "current_location": "tunnel_right",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tunnel_right"]["description"],
            "action_result": "move_tunnel_right",
            "session_events": ["Took the right tunnel"],
            "legal_outcomes": ["look", "open chest", "back"],
        }

    if _matches(inp, exits["tunnel_left"]):
        return {
            "current_location": "tunnel_left",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tunnel_left"]["description"],
            "action_result": "move_tunnel_left",
            "session_events": ["Took the left tunnel"],
            "legal_outcomes": ["look", "examine floor", "back"],
        }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tree_interior"]["look"],
            "action_result": "look",
            "legal_outcomes": ["right", "left", "back"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tree_interior"]["help"],
            "action_result": "help",
            "legal_outcomes": ["right", "left", "look", "back"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["right", "left", "look", "back"],
    }


# ── Tunnels ───────────────────────────────────────────────────────────────────

def _tunnel_right(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["tunnel_right"]["exits"]
    actions = LOCATIONS["tunnel_right"]["actions"]
    objectives = state.get("completed_objectives", [])
    has_key = "found_key" in objectives
    chest_opened = "opened_chest" in objectives

    if _matches(inp, exits["tree_interior"]):
        return {
            "current_location": "tree_interior",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tree_interior"]["description"],
            "action_result": "move_tree_interior",
            "legal_outcomes": ["look", "right", "left", "back"],
        }

    if _matches(inp, actions["look"]):
        narrative = (
            LOCATION_RESPONSES["tunnel_right"]["look_opened"] if chest_opened
            else LOCATION_RESPONSES["tunnel_right"]["look"]
        )
        return {
            "narrative_response": narrative,
            "action_result": "look",
            "legal_outcomes": ["back"] if chest_opened else ["open chest", "back"],
        }

    if _matches(inp, actions["open_chest"]):
        if chest_opened:
            return {
                "narrative_response": LOCATION_RESPONSES["tunnel_right"]["already_open"],
                "action_result": "chest_already_open",
                "legal_outcomes": ["back"],
            }
        if not has_key:
            return {
                "narrative_response": LOCATION_RESPONSES["tunnel_right"]["locked"],
                "action_result": "chest_locked",
                "session_events": ["Tried to open the chest — locked, needs a key"],
                "legal_outcomes": ["back", "look"],
            }
        new_objectives = _add_objective(state, "opened_chest")
        return {
            "narrative_response": LOCATION_RESPONSES["tunnel_right"]["opened"],
            "action_result": "chest_opened",
            "completed_objectives": new_objectives,
            "token_budget": state.get("token_budget", 5000) + 10000,
            "tokens_earned_session": state.get("tokens_earned_session", 0) + 10000,
            "session_events": ["Opened the Threshold chest — +10,000 tokens earned"],
            "legal_outcomes": ["back"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tunnel_right"]["help"],
            "action_result": "help",
            "legal_outcomes": ["look", "open chest", "back"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "open chest", "back"],
    }


def _tunnel_left(inp: str, state: GameState) -> dict:
    exits = LOCATIONS["tunnel_left"]["exits"]
    actions = LOCATIONS["tunnel_left"]["actions"]
    has_key = "found_key" in state.get("completed_objectives", [])

    if _matches(inp, exits["tree_interior"]):
        return {
            "current_location": "tree_interior",
            "current_concept": "kaari",
            "narrative_response": LOCATIONS["tree_interior"]["description"],
            "action_result": "move_tree_interior",
            "legal_outcomes": ["look", "right", "left", "back"],
        }

    # Specific floor/stone actions must run before generic "examine" -> look.
    if _matches(inp, actions["examine_floor"]):
        if has_key:
            return {
                "narrative_response": LOCATION_RESPONSES["tunnel_left"]["examine_empty"],
                "action_result": "examine_floor_empty",
                "legal_outcomes": ["back"],
            }
        new_objectives = _add_objective(state, "found_key")
        return {
            "narrative_response": LOCATION_RESPONSES["tunnel_left"]["examine_found"],
            "action_result": "found_key",
            "completed_objectives": new_objectives,
            "session_events": ["Found the iron key under the loose stone"],
            "legal_outcomes": ["back"],
        }

    if _matches(inp, actions["look"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tunnel_left"]["look"],
            "action_result": "look",
            "legal_outcomes": ["examine floor", "back"] if not has_key else ["back"],
        }

    if _matches(inp, actions["take_key"]):
        if has_key:
            return {
                "narrative_response": LOCATION_RESPONSES["tunnel_left"]["take_have"],
                "action_result": "take_key_have",
                "legal_outcomes": ["back"],
            }
        return {
            "narrative_response": LOCATION_RESPONSES["tunnel_left"]["take_need_look"],
            "action_result": "take_key_not_found",
            "legal_outcomes": ["examine floor"],
        }

    if _matches(inp, actions["help"]):
        return {
            "narrative_response": LOCATION_RESPONSES["tunnel_left"]["help"],
            "action_result": "help",
            "legal_outcomes": ["look", "examine floor", "back"],
        }

    return {
        "narrative_response": UNKNOWN_ACTION_TEXT.format(action=inp),
        "action_result": "unknown",
        "legal_outcomes": ["look", "examine floor", "back"],
    }
