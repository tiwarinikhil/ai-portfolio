"""One caller turn: transcript in, action and reply out.

    safety check -> clean transcript -> search FAQ -> confident? answer : hand off

The reply is short and spoken-style, because it will be read out by text to speech.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from .faq import FaqSearch, load_faq
from .normalize import normalize
from .safety import check

URGENT_REPLY = (
    "This sounds like an emergency. Please call 108 now for an ambulance. "
    "I am also connecting you to our staff right away."
)
HANDOFF_REPLY = (
    "I can't answer that safely on the phone. Let me connect you to our front desk, "
    "and a doctor or staff member will help you."
)

DEFAULT_FAQ = Path(__file__).resolve().parents[1] / "data" / "faq.md"


@dataclass
class Result:
    action: str  # "answer", "urgent" or "handoff"
    faq_id: str | None
    reply: str
    cleaned: str
    score: float


class ClinicAgent:
    def __init__(self, faq_path: str | Path = DEFAULT_FAQ, min_score: float = 4.0, min_margin: float = 0.5,
                 min_coverage: float = 0.2):
        self.entries = load_faq(faq_path)
        self.search = FaqSearch(self.entries)
        self.min_score = min_score
        self.min_margin = min_margin
        self.min_coverage = min_coverage

    def handle(self, transcript: str) -> Result:
        flag = check(transcript)
        if flag == "urgent":
            return Result("urgent", None, URGENT_REPLY, transcript, 0.0)
        if flag == "handoff":
            return Result("handoff", None, HANDOFF_REPLY, transcript, 0.0)

        cleaned = normalize(transcript, self.search.vocab)
        hits = self.search.search(cleaned, k=2)
        top, score = hits[0]
        second = hits[1][1] if len(hits) > 1 else 0.0
        # Only answer when the best match is strong, clearly ahead of the next one,
        # and covers enough of what the caller asked about.
        coverage = self.search.coverage(cleaned, self.entries.index(top))
        if score < self.min_score or score - second < self.min_margin or coverage < self.min_coverage:
            return Result("handoff", None, HANDOFF_REPLY, cleaned, score)
        return Result("answer", top.id, self.spoken_answer(transcript, top.answer), cleaned, score)

    def spoken_answer(self, transcript: str, answer: str) -> str:
        if not os.getenv("LLM_API_KEY"):
            return answer
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.getenv("LLM_BASE_URL"))
        resp = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=0,
            messages=[
                {"role": "system", "content": (
                    "You are a clinic phone assistant. Rewrite the FAQ answer as one or two short "
                    "spoken sentences that answer the caller. Use only facts from the FAQ answer. "
                    "Never give medical advice."
                )},
                {"role": "user", "content": f"Caller said: {transcript}\nFAQ answer: {answer}"},
            ],
        )
        return resp.choices[0].message.content.strip()


def baseline(search: FaqSearch, transcript: str) -> str:
    """What a quick FAQ bot does: search the raw transcript and always answer with the top hit."""
    return search.search(transcript, k=1)[0][0].id
