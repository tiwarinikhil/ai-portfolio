"""Load the clinic FAQ and search it with BM25.

Each FAQ entry is one section in data/faq.md:

    ## entry-id
    Q: question
    A: answer
"""

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are", "be", "am",
    "do", "does", "i", "my", "me", "we", "our", "you", "your", "can", "what", "how", "when",
    "it", "at", "by", "with", "as", "if", "this", "that", "there", "will", "should", "want",
    "need", "get", "any", "some", "someone", "please", "tell", "know", "which", "where", "who",
    "clinic", "exactly", "have", "wanted",
}


@dataclass
class Entry:
    id: str
    question: str
    answer: str


def load_faq(path: str | Path) -> list[Entry]:
    entries, current = [], None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            current = {"id": line[3:].strip(), "q": "", "a": ""}
            entries.append(current)
        elif current and line.startswith("Q:"):
            current["q"] = line[2:].strip()
        elif current and line.startswith("A:"):
            current["a"] = line[2:].strip()
    return [Entry(e["id"], e["q"], e["a"]) for e in entries]


def tokenize(text: str) -> list[str]:
    out = []
    for t in re.findall(r"[a-z0-9]+", text.lower()):
        if t in STOPWORDS:
            continue
        if len(t) > 3 and t.endswith("s"):
            t = t[:-1]
        out.append(t)
    return out


class FaqSearch:
    def __init__(self, entries: list[Entry], k1: float = 1.5, b: float = 0.75):
        self.entries = entries
        self.k1, self.b = k1, b
        # The id and question carry the topic. They are repeated so they count a bit more.
        self.docs = [tokenize(f"{e.id.replace('-', ' ')} {e.question} {e.question} {e.answer}") for e in entries]
        self.tf = [Counter(d) for d in self.docs]
        self.avg = sum(len(d) for d in self.docs) / max(len(self.docs), 1)
        df = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.vocab = set(df)

    def search(self, query: str, k: int = 3) -> list[tuple[Entry, float]]:
        q = tokenize(query)
        scored = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for t in q:
                if t in tf:
                    f = tf[t]
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(self.docs[i]) / self.avg))
            scored.append((self.entries[i], s))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def coverage(self, query: str, entry_index: int) -> float:
        """Share of the caller's words that the FAQ entry actually contains."""
        q = set(tokenize(query))
        return len(q & set(self.docs[entry_index])) / len(q) if q else 0.0
