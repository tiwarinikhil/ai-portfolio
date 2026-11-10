"""Score a lead from 0 to 100 using four simple signals.

Budget, authority (can this person say yes?), need (is there a clear problem
we can solve?) and timeline. Each signal gives points, and the reasons are
kept so a human can see why a lead got its score.
"""

from dataclasses import dataclass, field

DECISION_MAKERS = ("founder", "co-founder", "ceo", "cto", "owner", "partner", "director", "vp", "head")
INFLUENCERS = ("manager", "lead", "coordinator", "consultant")
NOT_BUYERS = ("student", "job seeker", "retired", "researcher", "teacher")

# Words that point to a real problem we can build for.
NEED_WORDS = (
    "chatbot", "bot", "agent", "automate", "automatically", "pipeline", "support",
    "faq", "invoices", "pdf", "documents", "docs", "emails", "tickets", "whatsapp",
    "search", "answers from", "pull", "extract", "erp", "order system", "sources",
    "from our", "scores", "replies", "pricing", "quotes",
)
# Words that say there is no real project or no money yet.
WEAK_WORDS = (
    "free", "just exploring", "curious", "not sure", "maybe", "one day", "assignment",
    "thesis", "refer me", "liked your", "can't pay", "memoir",
)
APPROVAL_WORDS = ("check with", "approval", "my manager", "my head", "owner decides", "share with")

SLOW_TIMELINES = ("next quarter", "no rush", "someday")

TIMELINE_POINTS = {
    "asap": 20, "2 weeks": 20, "this month": 18, "next month": 12,
    "this quarter": 12, "next quarter": 6, "no rush": 0, "someday": 0, "": 2,
}


@dataclass
class Score:
    total: int
    tier: str
    reasons: list[str] = field(default_factory=list)


def _budget_points(budget: float | None, message: str) -> tuple[int, str]:
    if budget is None:
        if "budget is flexible" in message or "budget approved" in message:
            return 15, "budget not given but said to be available"
        return 8, "no budget given"
    if budget >= 5000:
        return 25, f"budget ${budget:,.0f}"
    if budget >= 2000:
        return 20, f"budget ${budget:,.0f}"
    if budget >= 1000:
        return 14, f"budget ${budget:,.0f}"
    return 3, f"low budget ${budget:,.0f}"


def _authority_points(role: str) -> tuple[int, str]:
    r = role.lower()
    if any(w in r for w in NOT_BUYERS):
        return 0, f"{role}: not a buyer"
    if any(w in r for w in DECISION_MAKERS):
        return 25, f"{role}: can decide"
    if "intern" in r:
        return 6, f"{role}: asking for someone else"
    if any(w in r for w in INFLUENCERS):
        return 14, f"{role}: can influence"
    return 8, f"{role or 'unknown role'}: unclear authority"


def _need_points(message: str) -> tuple[int, str]:
    m = message.lower()
    weak = [w for w in WEAK_WORDS if w in m]
    hits = [w for w in NEED_WORDS if w in m]
    if weak and len(hits) < 3:
        return 0, f"weak intent ({weak[0]})"
    if len(hits) >= 3:
        return 30, "clear problem: " + ", ".join(hits[:3])
    if len(hits) >= 1:
        return 18, "some need: " + ", ".join(hits)
    return 5, "no clear problem stated"


def score_lead(lead: dict) -> Score:
    message = (lead.get("message") or "").lower()
    budget_raw = str(lead.get("budget_usd") or "").strip()
    budget = float(budget_raw) if budget_raw else None
    timeline = (lead.get("timeline") or "").strip().lower()

    parts = [
        _budget_points(budget, message),
        _authority_points(lead.get("role") or ""),
        _need_points(message),
        (TIMELINE_POINTS.get(timeline, 6), f"timeline: {timeline or 'not given'}"),
    ]
    total = sum(p for p, _ in parts)
    reasons = [r for _, r in parts]

    if any(w in message for w in APPROVAL_WORDS):
        total -= 10
        reasons.append("needs someone else to approve")

    total = max(0, min(100, total))
    tier = "hot" if total >= 70 else "warm" if total >= 40 else "cold"
    if tier == "hot" and timeline in SLOW_TIMELINES:
        tier = "warm"
        reasons.append("not hot yet: project starts later")
    return Score(total=total, tier=tier, reasons=reasons)


def budget_only_tier(lead: dict) -> str:
    """The usual shortcut: sort leads by budget alone. Used as the baseline."""
    raw = str(lead.get("budget_usd") or "").strip()
    budget = float(raw) if raw else 0
    if budget >= 3000:
        return "hot"
    if budget >= 1000:
        return "warm"
    return "cold"
