"""Token reward definitions and earning logic."""

REWARDS = {
    "efficient_prompt": {
        "description": "Prompt under 100 tokens",
        "amount": 150,
    },
    "efficient_chain": {
        "description": "Three efficient prompts in a row",
        "amount": 300,
    },
    "concept_unlock": {
        "description": "Unlocked a LangChain concept",
        "amount": 500,
    },
    "room_complete": {
        "description": "Completed a room within budget",
        "amount": 800,
    },
    "help_npc": {
        "description": "Helped an NPC",
        "amount": 200,
    },
}


def check_rewards(action_result: str, state: dict) -> list[dict]:
    earned = []
    if action_result == "concept_unlock":
        earned.append(REWARDS["concept_unlock"])
    if action_result == "help_npc":
        earned.append(REWARDS["help_npc"])
    return earned
