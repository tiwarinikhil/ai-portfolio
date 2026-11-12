import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from meetbot.agent import check, run, to_markdown
from meetbot.dates import resolve_due
from meetbot.rules import extract_rules
from meetbot.transcript import parse_transcript

ROOT = Path(__file__).resolve().parents[1]
MON = date(2026, 11, 9)  # a Monday


def make(lines: str, d: str = "2026-11-09") -> str:
    return f"Meeting: Test\nDate: {d}\nAttendees: Asha, Ben, Chris\n\n{lines}"


def test_dates():
    assert resolve_due("by today", MON) == MON
    assert resolve_due("send it tomorrow", MON) == date(2026, 11, 10)
    assert resolve_due("by Wednesday", MON) == date(2026, 11, 11)
    assert resolve_due("by Monday", MON) == date(2026, 11, 16)
    assert resolve_due("next Monday", MON) == date(2026, 11, 16)
    assert resolve_due("by end of week", MON) == date(2026, 11, 13)
    assert resolve_due("sometime next week", MON) == date(2026, 11, 20)
    assert resolve_due("end of month", MON) == date(2026, 11, 30)
    assert resolve_due("by Nov 25", MON) == date(2026, 11, 25)
    assert resolve_due("by 3 January", MON) == date(2027, 1, 3)
    assert resolve_due("by the 20th", MON) == date(2026, 11, 20)
    assert resolve_due("by the 5th", MON) == date(2026, 12, 5)
    assert resolve_due("in two days", MON) == date(2026, 11, 11)
    assert resolve_due("no date here", MON) is None


def test_parse_transcript():
    tr = parse_transcript(make("Asha: Hello.\nDana: Hi."))
    assert tr.meeting_date == MON
    assert [t.n for t in tr.turns] == [1, 2]
    assert "Dana" in tr.attendees  # speakers are added


def test_named_request_and_reply_merge():
    tr = parse_transcript(make("Asha: Ben, can you fix the form by Friday?\nBen: Sure."))
    tasks = extract_rules(tr)
    assert len(tasks) == 1
    assert tasks[0]["owner"] == "Ben" and tasks[0]["due"] == date(2026, 11, 13)


def test_open_request_gets_owner_from_reply():
    tr = parse_transcript(make("Asha: Someone should update the FAQ.\nChris: I'll take that, by end of month."))
    (t,) = extract_rules(tr)
    assert t["turn"] == 1 and t["owner"] == "Chris" and t["due"] == date(2026, 11, 30)


def test_skips_questions_past_and_cancelled():
    tr = parse_transcript(make(
        "Ben: Will the list be ready?\n"
        "Chris: I already sent the brief.\n"
        "Asha: Let me call the bank next week.\n"
        "Asha: Scratch that, Ben did it.\n"
        "Ben: We should move the docs.\n"
        "Asha: Not now."
    ))
    assert extract_rules(tr) == []


def test_promise_belongs_to_speaker():
    tr = parse_transcript(make("Ben: Sales are up. I'll send the report today."))
    (t,) = extract_rules(tr)
    assert t["owner"] == "Ben" and t["due"] == MON and t["task"].startswith("Send the report")


def test_check_flags_and_cleans():
    tr = parse_transcript(make("Asha: Hi."))
    out = check([{"turn": 1, "task": "x", "owner": "Zed", "due": date(2026, 1, 1)}], tr)
    assert out[0]["owner"] is None and out[0]["due"] is None
    assert out[0]["needs_review"] == ["no owner", "no due date"]


def test_run_and_markdown():
    raw = (ROOT / "data" / "transcripts" / "dev-01-store-marketing.txt").read_text()
    result = run(raw, mode="rules")
    assert len(result["tasks"]) == 6
    md = to_markdown(result)
    assert "| Owner |" in md and "Needs a human check" in md


def test_rules_beat_baseline_on_holdout():
    sys.path.insert(0, str(ROOT / "eval"))
    from run_eval import score

    rows = [json.loads(x) for x in (ROOT / "eval" / "gold.jsonl").read_text().splitlines() if x.strip()]
    full = {"baseline": 0, "rules": 0}
    for row in rows:
        if row["split"] != "holdout":
            continue
        raw = (ROOT / "data" / "transcripts" / row["file"]).read_text()
        for mode in full:
            full[mode] += score(row["tasks"], run(raw, mode=mode)["tasks"])["full"]
    assert full["rules"] > full["baseline"]


def test_cli(tmp_path):
    src = ROOT / "data" / "transcripts" / "holdout-02-grocery-ops.txt"
    j, m = tmp_path / "t.json", tmp_path / "t.md"
    subprocess.run([sys.executable, "-m", "meetbot", str(src), "--mode", "rules", "--json", str(j), "--md", str(m)],
                   cwd=ROOT, check=True)
    data = json.loads(j.read_text())
    assert data["mode"] == "rules" and data["tasks"]
    assert m.read_text().startswith("# Operations weekly")
