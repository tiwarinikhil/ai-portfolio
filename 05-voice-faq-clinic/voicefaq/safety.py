"""Decide when the bot must NOT answer from the FAQ.

urgent:  signs of an emergency. Tell the caller to call 108 and transfer to staff now.
handoff: medical advice, test results, or anything the FAQ does not cover.
         A person should take the call.

These checks run before search, so an emergency never gets an FAQ answer.
"""

import re

URGENT_PATTERNS = [
    r"chest pain", r"cant breathe", r"can not breathe", r"not breathing", r"breathing problem",
    r"not waking up", r"unconscious", r"collapsed", r"fainted",
    r"stroke", r"bleeding", r"heart attack", r"seizure", r"\bfit\b",
    r"poison", r"swallowed", r"suicid", r"overdose",
]

ADVICE_PATTERNS = [
    r"what medicine", r"which medicine", r"what dose", r"dosage",
    r"is (this|it) serious", r"should i be worried", r"is it normal", r"result of my",
    r"what does my report", r"diagnos",
]


def check(text: str) -> str | None:
    t = text.lower().replace("'", "")
    if any(re.search(p, t) for p in URGENT_PATTERNS):
        return "urgent"
    if any(re.search(p, t) for p in ADVICE_PATTERNS):
        return "handoff"
    return None
