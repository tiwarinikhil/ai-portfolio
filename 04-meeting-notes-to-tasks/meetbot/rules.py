"""Offline task extractor. No API key needed.

It reads the meeting turn by turn and keeps a list of tasks:
1. A request to a named person ("Rahul, can you ...", "Neha to ...") -> owner is that person.
2. A promise ("I'll ...", "let me ...", "I'm going to ...")          -> owner is the speaker.
3. An open request ("can you ...", "someone should ...")              -> owner unknown for now.
4. A short reply right after a request ("Sure.", "I'll take that")   -> fills in owner and date,
   no new task.
5. "Scratch that" / "never mind" removes the last task.
   "Not now" / "let's not" right after a suggestion removes it.
Questions, past actions ("already sent", "paid it yesterday") are skipped.
At most one task per turn.
"""

import re

from .dates import resolve_due
from .transcript import Transcript

PROMISE = re.compile(r"\b(i'll|i will|i'm going to|i am going to|let me|i can(?!'t|not))\b", re.I)
OPEN_REQUEST = re.compile(r"\b(can you|could you|can someone|someone should|we need to|we should)\b", re.I)
PAST_OR_NO = re.compile(
    r"\b(already|yesterday|last (week|month|night)|was fixed|i did|i paid|let's not|not now|not this)\b", re.I
)
CANCEL = re.compile(r"\b(scratch that|never mind|forget that|cancel that)\b", re.I)
REJECT = re.compile(r"^(not now|no\b|let's not)", re.I)
ACCEPT = re.compile(
    r"^(sure( thing)?|yes|yeah|okay|ok|on it|will do|fine|i'll take (it|that|this)|i can do (it|that|this))\b[.,!]?\s*",
    re.I,
)
REQUEST_WORDS = re.compile(
    r"^(can you|could you|please|can someone|someone should|we need to|we should|to|will|is going to|"
    r"i'll|i will|i'm going to|i am going to|let me|also|actually,?|then)\s+",
    re.I,
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _named_owner(sentence: str, attendees: list[str]) -> str | None:
    for name in attendees:
        if re.match(rf"^{re.escape(name)},\s+", sentence) and not re.search(r"\b(did|have) you\b", sentence, re.I):
            return name
        if re.search(rf"\b{re.escape(name)} (will|to|is going to)\b", sentence):
            return name
    return None


def clean_task(sentence: str, owner: str | None) -> str:
    s = sentence.strip()
    if owner:
        s = re.sub(rf"^{re.escape(owner)}(,| will| to| is going to)\s*", "", s)
    for _ in range(3):
        s = REQUEST_WORDS.sub("", s)
    s = s.rstrip("?.! ")
    return s[:1].upper() + s[1:] if s else sentence


def extract_rules(tr: Transcript) -> list[dict]:
    tasks: list[dict] = []
    for i, turn in enumerate(tr.turns):
        text = turn.text
        last = tasks[-1] if tasks else None
        last_is_prev_turn = last is not None and last["turn"] == turn.n - 1

        if CANCEL.search(text) and tasks:
            tasks.pop()
            continue
        if REJECT.match(text) and last_is_prev_turn and last["owner"] is None:
            tasks.pop()
            continue

        acc = ACCEPT.match(text)
        if acc and last_is_prev_turn and last["owner"] in (None, turn.speaker):
            rest = text[acc.end():]
            if not re.search(r"\balso\b", rest, re.I):
                last["owner"] = last["owner"] or turn.speaker
                if last["due"] is None:
                    last["due"] = resolve_due(rest, tr.meeting_date)
                continue

        for s in _sentences(text):
            if PAST_OR_NO.search(s):
                continue
            owner = _named_owner(s, tr.attendees)
            is_question = s.endswith("?")
            if owner is None:
                if PROMISE.search(s) and not is_question:
                    owner = turn.speaker
                elif not OPEN_REQUEST.search(s):
                    continue
            elif is_question and not OPEN_REQUEST.search(s):
                continue
            tasks.append({
                "turn": turn.n,
                "task": clean_task(s, owner),
                "owner": owner,
                "due": resolve_due(s, tr.meeting_date),
                "quote": f"{turn.speaker}: {text}",
            })
            break
    return tasks


KEYWORDS = re.compile(r"\b(will|i'll|need to|should|can you|could you|please|let me|going to)\b", re.I)


def extract_baseline(tr: Transcript) -> list[dict]:
    """The quick way: any line with a task word is a task, the speaker owns it, no dates."""
    return [
        {"turn": t.n, "task": t.text, "owner": t.speaker, "due": None, "quote": f"{t.speaker}: {t.text}"}
        for t in tr.turns if KEYWORDS.search(t.text)
    ]
