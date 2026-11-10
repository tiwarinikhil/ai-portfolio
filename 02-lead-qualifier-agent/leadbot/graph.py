"""The lead agent as a LangGraph graph.

score -> draft -> human_review -> finish

The graph stops at human_review and waits. Nothing is "sent" until a person
approves, edits or rejects the draft. Cold leads skip the draft and go
straight to finish, so nobody wastes time reviewing them.
"""

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .llm import draft_reply
from .scoring import score_lead


class LeadState(TypedDict, total=False):
    lead: dict
    score: int
    tier: str
    reasons: list[str]
    draft: str
    draft_mode: str
    decision: str  # approved, edited, rejected, skipped
    final_reply: str


def score_node(state: LeadState) -> LeadState:
    s = score_lead(state["lead"])
    return {"score": s.total, "tier": s.tier, "reasons": s.reasons}


def route_after_score(state: LeadState) -> str:
    return "finish" if state["tier"] == "cold" else "draft"


def draft_node(state: LeadState) -> LeadState:
    text, mode = draft_reply(state["lead"], state["tier"], state["reasons"])
    return {"draft": text, "draft_mode": mode}


def human_review_node(state: LeadState) -> LeadState:
    # Pauses the graph. Resume with Command(resume={"action": "approve" | "edit" | "reject", "text": ...}).
    answer = interrupt(
        {
            "lead_id": state["lead"].get("id"),
            "tier": state["tier"],
            "score": state["score"],
            "reasons": state["reasons"],
            "draft": state["draft"],
        }
    )
    action = answer.get("action", "reject")
    if action == "approve":
        return {"decision": "approved", "final_reply": state["draft"]}
    if action == "edit":
        return {"decision": "edited", "final_reply": answer.get("text", state["draft"])}
    return {"decision": "rejected", "final_reply": ""}


def finish_node(state: LeadState) -> LeadState:
    if state.get("tier") == "cold" and not state.get("decision"):
        return {"decision": "skipped", "final_reply": ""}
    return {}


def build_graph(checkpointer=None):
    g = StateGraph(LeadState)
    g.add_node("score", score_node)
    g.add_node("draft", draft_node)
    g.add_node("human_review", human_review_node)
    g.add_node("finish", finish_node)
    g.add_edge(START, "score")
    g.add_conditional_edges("score", route_after_score, {"draft": "draft", "finish": "finish"})
    g.add_edge("draft", "human_review")
    g.add_edge("human_review", "finish")
    g.add_edge("finish", END)
    return g.compile(checkpointer=checkpointer or MemorySaver())
