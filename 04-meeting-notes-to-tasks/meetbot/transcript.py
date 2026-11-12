"""Read a plain text transcript.

Format:
    Meeting: Weekly sync
    Date: 2026-11-09
    Attendees: Priya, Rahul, Meera

    Priya: Let's start.
    Rahul: ...

Header lines are optional except Date. Each spoken line is "Name: text".
Turns are numbered from 1 in the order they appear.
"""

import re
from dataclasses import dataclass, field
from datetime import date

TURN_RE = re.compile(r"^([A-Z][\w .'-]{0,40}?):\s+(.+)$")
HEADER_KEYS = {"meeting", "company", "date", "attendees"}


@dataclass
class Turn:
    n: int
    speaker: str
    text: str


@dataclass
class Transcript:
    title: str
    meeting_date: date
    attendees: list[str]
    turns: list[Turn] = field(default_factory=list)


def parse_transcript(raw: str) -> Transcript:
    header: dict[str, str] = {}
    turns: list[Turn] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = TURN_RE.match(line)
        if not m:
            continue
        name, text = m.group(1).strip(), m.group(2).strip()
        if name.lower() in HEADER_KEYS and not turns:
            header[name.lower()] = text
            continue
        turns.append(Turn(len(turns) + 1, name, text))
    if "date" not in header:
        raise ValueError("Transcript needs a 'Date: YYYY-MM-DD' line at the top")
    attendees = [a.strip() for a in header.get("attendees", "").split(",") if a.strip()]
    for t in turns:  # anyone who spoke is an attendee too
        if t.speaker not in attendees:
            attendees.append(t.speaker)
    return Transcript(
        title=header.get("meeting", "Meeting"),
        meeting_date=date.fromisoformat(header["date"][:10]),
        attendees=attendees,
        turns=turns,
    )
