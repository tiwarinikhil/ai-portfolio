"""Optional LLM extractor. Works with any OpenAI-compatible chat API.

  LLM_API_KEY   your key (without it, the offline rules are used)
  LLM_BASE_URL  optional, for Gemini, Groq, OpenRouter or a local server
  LLM_MODEL     optional, default gpt-4o-mini
"""

import json
import os
from datetime import date

from .transcript import Transcript

SYSTEM = (
    "You extract action items from a meeting transcript. An action item is something a person agreed "
    "to do after the meeting. Skip questions, things already done, ideas that were rejected and tasks "
    "that were cancelled. If a reply like 'Sure' or 'I'll take that' accepts a request, the task belongs "
    "to the request turn and the owner is the person who accepted. Owner must be one of the attendees or "
    "null. Due is an ISO date (YYYY-MM-DD) worked out from the meeting date, or null if no deadline was "
    "said. 'next week' means Friday of next week. 'this week' means Friday of this week. "
    'Return JSON: {"tasks": [{"turn": int, "task": "short imperative", "owner": str|null, "due": str|null}]}'
)


def llm_enabled() -> bool:
    return bool(os.getenv("LLM_API_KEY"))


def extract_llm(tr: Transcript) -> list[dict]:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
    lines = "\n".join(f"[{t.n}] {t.speaker}: {t.text}" for t in tr.turns)
    user = (f"Meeting date: {tr.meeting_date.isoformat()} ({tr.meeting_date.strftime('%A')})\n"
            f"Attendees: {', '.join(tr.attendees)}\n\nTranscript:\n{lines}")
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    )
    data = json.loads(resp.choices[0].message.content)
    by_turn = {t.n: t for t in tr.turns}
    out = []
    for item in data.get("tasks", []):
        n = int(item.get("turn", 0))
        due = item.get("due")
        try:
            due = date.fromisoformat(due) if due else None
        except ValueError:
            due = None
        turn = by_turn.get(n)
        out.append({
            "turn": n,
            "task": str(item.get("task", "")).strip(),
            "owner": item.get("owner"),
            "due": due,
            "quote": f"{turn.speaker}: {turn.text}" if turn else "",
        })
    return out
