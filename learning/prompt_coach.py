"""Prompt coach — efficiency tips after AI calls. V1 stub. Active in V2."""


def get_tip(tokens_spent: int, player_input: str) -> str | None:
    """Returns a coaching tip if the prompt was inefficient. None if fine."""
    if tokens_spent > 400:
        return (
            f"[dim]TIP: '{player_input[:40]}...' cost {tokens_spent} tokens — that's high.\n"
            f"Try being more specific. Instead of vague requests, name exactly what you want.[/dim]"
        )
    if tokens_spent > 200:
        return f"[dim]TIP: {tokens_spent} tokens spent. A tighter prompt might cost ~90.[/dim]"
    return None
