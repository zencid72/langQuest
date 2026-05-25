import uuid
import operator
from typing import TypedDict, Annotated

from state.player_profile import PlayerProfile, create_default_profile
from state.world_bible import WorldBible, default_fantasy_bible


class GameState(TypedDict):
    # Player identity
    player_name: str
    player_profile: dict          # PlayerProfile as dict

    # World
    world_id: str
    world_bible: dict             # WorldBible as dict
    current_location: str
    current_encounter: str
    current_concept: str          # which LangChain concept is active

    # Session
    session_id: str
    session_events: Annotated[list, operator.add]   # appends across nodes
    messages: Annotated[list, operator.add]          # conversation history
    raw_player_input: str
    last_player_input: str
    retrieved_context: list
    legal_outcomes: list
    current_event_significance: float

    # Token economy
    token_budget: int
    tokens_spent_session: int
    tokens_earned_session: int
    token_budget_discovered: bool

    # UI
    xray_mode: bool
    last_xray_data: dict

    # Progression
    current_level: int                # 1 = Kyläaukio, 2 = Kirjasto, …
    completed_objectives: list        # list of objective keys earned so far
    level_just_completed: bool        # flag to trigger completion message once

    # Game flow
    quit: bool
    game_over: bool
    narrative_response: str
    action_result: str
    dm_heard: str                  # what the DM interpreted (shown when different from raw input)
    dm_reason: str
    dm_clarification: str
    question_topic: str
    question_answered: bool
    question_answer_source: str
    question_lore_chunks_used: int
    free_action: str
    free_action_resolved: bool


# Objectives that must be completed to finish each level
LEVEL_OBJECTIVES = {
    1: ["talked_to_mira", "visited_kaivo", "used_xray"],
    2: ["found_key", "opened_chest"],
}


def level_complete(level: int, completed: list) -> bool:
    return all(obj in completed for obj in LEVEL_OBJECTIVES.get(level, []))


def create_initial_state(player_name: str) -> GameState:
    world_id = str(uuid.uuid4())[:8]
    world_bible = default_fantasy_bible(world_id)
    profile = create_default_profile()

    return GameState(
        player_name=player_name,
        player_profile=dict(profile),
        world_id=world_id,
        world_bible=world_bible.model_dump(),
        current_location="village_square",
        current_encounter="",
        current_concept="tila",
        session_id=str(uuid.uuid4()),
        session_events=[],
        messages=[],
        raw_player_input="",
        last_player_input="",
        retrieved_context=[],
        legal_outcomes=[],
        current_event_significance=0.0,
        token_budget=5000,
        tokens_spent_session=0,
        tokens_earned_session=0,
        token_budget_discovered=True,
        xray_mode=False,
        last_xray_data={},
        current_level=1,
        completed_objectives=[],
        level_just_completed=False,
        quit=False,
        game_over=False,
        narrative_response="",
        action_result="",
        dm_heard="",
        dm_reason="",
        dm_clarification="",
        question_topic="",
        question_answered=False,
        question_answer_source="",
        question_lore_chunks_used=0,
        free_action="",
        free_action_resolved=False,
    )
