"""Retrievers. Built in: BM25. Bring your own with --retriever module:factory.

A factory takes the list of chunks and returns an object with
search(query: str, k: int) -> list[str]  (chunk ids, best first).
"""

import importlib
import math
import re
from collections import Counter

from .chunks import Chunk

STOP = set(
    "a an the and or of to in on for is are was be it i my me you your we our do does did can how what when "
    "which who is if with at by from this that there their have has so not as up any".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP]


def stem(word: str) -> str:
    """Tiny suffix stripper: sofas -> sofa, tracking -> track, delivered -> deliver."""
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


class BM25Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75, use_stem: bool = False):
        self.use_stem = use_stem
        self.ids = [c.id for c in chunks]
        self.docs = [self._tokens(c.text) for c in chunks]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = sum(len(d) for d in self.docs) / max(len(self.docs), 1)
        df = Counter(t for d in self.docs for t in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.k1, self.b = k1, b

    def _tokens(self, text: str) -> list[str]:
        toks = tokenize(text)
        return [stem(t) for t in toks] if self.use_stem else toks

    def score(self, query: str) -> list[float]:
        q = self._tokens(query)
        scores = []
        for tf, d in zip(self.tf, self.docs):
            s = 0.0
            norm = self.k1 * (1 - self.b + self.b * len(d) / self.avgdl)
            for t in q:
                if t in tf:
                    s += self.idf[t] * tf[t] * (self.k1 + 1) / (tf[t] + norm)
            scores.append(s)
        return scores

    def search(self, query: str, k: int = 5) -> list[str]:
        scores = self.score(query)
        order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
        return [self.ids[i] for i in order[:k] if scores[i] > 0]


def load_retriever(spec: str, chunks: list[Chunk]):
    if spec == "bm25":
        return BM25Retriever(chunks)
    if spec == "bm25-stem":
        return BM25Retriever(chunks, use_stem=True)
    module, _, name = spec.partition(":")
    factory = getattr(importlib.import_module(module), name or "build")
    return factory(chunks)
