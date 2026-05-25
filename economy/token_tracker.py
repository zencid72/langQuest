"""Token tracker — maps real Anthropic API usage to the game economy.

V1: Stub structure. All values are hardcoded placeholders.
V2: Will pull from actual API response.usage fields.
"""


class TokenTracker:
    def __init__(self, initial_budget: int = 5000):
        self.initial_budget = initial_budget
        self.spent = 0
        self.earned = 0

    def deduct(self, amount: int, reason: str = "") -> dict:
        self.spent += amount
        return {
            "spent": amount,
            "reason": reason,
            "remaining": self.initial_budget - self.spent,
        }

    def earn(self, amount: int, reason: str = "") -> dict:
        self.earned += amount
        return {"earned": amount, "reason": reason}

    def efficiency_rating(self, tokens_spent: int) -> tuple[str, str]:
        """Returns (label, icon) for the efficiency display."""
        if tokens_spent < 100:
            return "Excellent", "✓"
        elif tokens_spent < 200:
            return "Good", "✓"
        elif tokens_spent < 400:
            return "Fair", "⚠"
        else:
            return "Poor", "⚠⚠"

    def format_report(self, spent: int, reason: str, remaining: int) -> str:
        rating, icon = self.efficiency_rating(spent)
        return (
            f"\n[TOKEN REPORT]\n"
            f"  Spent this turn:     [red]-{spent}[/red] tokens\n"
            f"  Reason:              {reason}\n"
            f"  Budget remaining:    [cyan]{remaining:,}[/cyan] tokens\n"
            f"  Efficiency rating:   {icon}  {rating}\n"
        )
