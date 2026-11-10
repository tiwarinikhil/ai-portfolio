import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from langgraph.types import Command  # noqa: E402

from leadbot import budget_only_tier, build_graph, score_lead  # noqa: E402

HOT = {
    "id": "T1", "name": "Asha Rao", "company": "Brightcart", "role": "Founder",
    "company_size": "12", "budget_usd": "6000", "timeline": "this month",
    "message": "We get 200 support emails a day. Want a chatbot that answers from our help docs.",
}
COLD = {
    "id": "T2", "name": "Rohit Sen", "company": "", "role": "Student", "company_size": "1",
    "budget_usd": "", "timeline": "", "message": "Can you help with my assignment for free?",
}


def test_clear_founder_lead_is_hot():
    s = score_lead(HOT)
    assert s.tier == "hot"
    assert s.total >= 70
    assert any("can decide" in r for r in s.reasons)


def test_student_asking_for_free_help_is_cold():
    assert score_lead(COLD).tier == "cold"


def test_slow_timeline_caps_at_warm():
    lead = {**HOT, "timeline": "next quarter", "budget_usd": "25000"}
    s = score_lead(lead)
    assert s.tier == "warm"
    assert "not hot yet" in s.reasons[-1]


def test_needing_approval_lowers_score():
    with_approval = {**HOT, "message": HOT["message"] + " I need approval from my manager."}
    assert score_lead(with_approval).total == score_lead(HOT).total - 10


def test_budget_only_baseline_ignores_role():
    rich_student = {**COLD, "budget_usd": "5000"}
    assert budget_only_tier(rich_student) == "hot"
    assert score_lead(rich_student).tier != "hot"


def test_graph_pauses_for_human_before_any_reply(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    graph = build_graph()
    config = {"configurable": {"thread_id": "t-hot"}}
    state = graph.invoke({"lead": HOT}, config)
    assert "__interrupt__" in state
    payload = state["__interrupt__"][0].value
    assert payload["tier"] == "hot"
    assert "Asha" in payload["draft"]
    assert not state.get("final_reply")

    state = graph.invoke(Command(resume={"action": "approve"}), config)
    assert state["decision"] == "approved"
    assert state["final_reply"] == payload["draft"]


def test_graph_edit_and_reject(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    graph = build_graph()
    c1 = {"configurable": {"thread_id": "t-edit"}}
    graph.invoke({"lead": HOT}, c1)
    state = graph.invoke(Command(resume={"action": "edit", "text": "Hi Asha, call on Friday?"}), c1)
    assert state["decision"] == "edited"
    assert state["final_reply"] == "Hi Asha, call on Friday?"

    c2 = {"configurable": {"thread_id": "t-reject"}}
    graph.invoke({"lead": HOT}, c2)
    state = graph.invoke(Command(resume={"action": "reject"}), c2)
    assert state["decision"] == "rejected"
    assert state["final_reply"] == ""


def test_cold_lead_skips_review():
    graph = build_graph()
    state = graph.invoke({"lead": COLD}, {"configurable": {"thread_id": "t-cold"}})
    assert "__interrupt__" not in state
    assert state["decision"] == "skipped"
