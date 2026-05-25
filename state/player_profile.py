from typing import TypedDict


class PlayerProfile(TypedDict):
    # Hard stats
    health: int
    strength: int
    wisdom: int

    # Soft stats — how they play
    attitude_score: int       # -10 aggressive → +10 gentle
    caution_score: int        # -10 reckless → +10 careful
    curiosity_score: int      # how much they explore/ask

    # Prompt behavior
    avg_tokens_per_prompt: int
    best_prompt_cost: int
    worst_prompt_cost: int
    prompt_efficiency_score: float
    avg_prompt_length: int
    specificity_score: float

    # Word fingerprint
    words_used: list
    question_count: int

    # History
    last_5_actions: list
    concepts_mastered: list
    times_died: int
    times_asked_for_help: int

    # Token economy
    token_budget: int
    tokens_spent_total: int
    tokens_earned_total: int


def create_default_profile() -> PlayerProfile:
    return PlayerProfile(
        health=100,
        strength=10,
        wisdom=10,
        attitude_score=0,
        caution_score=0,
        curiosity_score=0,
        avg_tokens_per_prompt=0,
        best_prompt_cost=0,
        worst_prompt_cost=0,
        prompt_efficiency_score=1.0,
        avg_prompt_length=0,
        specificity_score=0.5,
        words_used=[],
        question_count=0,
        last_5_actions=[],
        concepts_mastered=[],
        times_died=0,
        times_asked_for_help=0,
        token_budget=5000,
        tokens_spent_total=0,
        tokens_earned_total=0,
    )
