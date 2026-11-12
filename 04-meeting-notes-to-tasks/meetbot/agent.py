"""The pipeline: extract -> check -> write JSON and a markdown summary.

The check step never trusts the extractor (rules or LLM):
- owner must be someone in the meeting, else it is set to null
- due date cannot be before the meeting
- every task with no owner or no due date is flagged for a person to fix
"""

from datetime import date

from .llm import extract_llm, llm_enabled
from .rules import extract_baseline, extract_rules
from .transcript import Transcript, parse_transcript


def check(tasks: list[dict], tr: Transcript) -> list[dict]:
    out = []
    for i, t in enumerate(sorted(tasks, key=lambda x: x["turn"]), start=1):
        owner = t.get("owner") if t.get("owner") in tr.attendees else None
        due = t.get("due")
        if isinstance(due, date) and due < tr.meeting_date:
            due = None
        flags = []
        if owner is None:
            flags.append("no owner")
        if due is None:
            flags.append("no due date")
        out.append({
            "id": i,
            "task": t["task"],
            "owner": owner,
            "due": due.isoformat() if isinstance(due, date) else None,
            "turn": t["turn"],
            "quote": t.get("quote", ""),
            "needs_review": flags,
        })
    return out


def run(raw: str, mode: str = "auto") -> dict:
    tr = parse_transcript(raw)
    if mode == "auto":
        mode = "llm" if llm_enabled() else "rules"
    extractor = {"rules": extract_rules, "baseline": extract_baseline, "llm": extract_llm}[mode]
    tasks = check(extractor(tr), tr)
    return {
        "meeting": tr.title,
        "date": tr.meeting_date.isoformat(),
        "attendees": tr.attendees,
        "mode": mode,
        "tasks": tasks,
    }


def to_markdown(result: dict) -> str:
    lines = [f"# {result['meeting']} ({result['date']})", "",
             f"Attendees: {', '.join(result['attendees'])}", "", "## Tasks", "",
             "| # | Task | Owner | Due |", "| --- | --- | --- | --- |"]
    for t in result["tasks"]:
        lines.append(f"| {t['id']} | {t['task']} | {t['owner'] or '?'} | {t['due'] or '?'} |")
    by_owner: dict[str, list[dict]] = {}
    for t in result["tasks"]:
        by_owner.setdefault(t["owner"] or "Unassigned", []).append(t)
    lines += ["", "## By person", ""]
    for owner, items in by_owner.items():
        lines.append(f"**{owner}**: " + "; ".join(f"{t['task']} ({t['due'] or 'no date'})" for t in items))
        lines.append("")
    review = [t for t in result["tasks"] if t["needs_review"]]
    lines += ["## Needs a human check", ""]
    if review:
        for t in review:
            lines.append(f"- Task {t['id']}: {', '.join(t['needs_review'])}. Said as: \"{t['quote']}\"")
    else:
        lines.append("- Nothing. Every task has an owner and a date.")
    return "\n".join(lines) + "\n"
