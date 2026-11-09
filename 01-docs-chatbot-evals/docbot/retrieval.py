"""Retrievers: BM25 (keyword), embeddings (meaning), and hybrid (both).

BM25 needs no API key, so the project runs fully offline.
Embeddings work with any OpenAI-compatible API (OpenAI, Gemini, Groq, local servers).
"""

import math
import os
import re
from collections import Counter

from .chunking import Chunk

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are", "be",
    "do", "does", "i", "my", "we", "our", "you", "your", "can", "what", "how", "when",
    "it", "at", "by", "with", "as", "if", "this", "that", "much", "many", "get",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out = []
    for t in tokens:
        if t in STOPWORDS:
            continue
        if len(t) > 3 and t.endswith("s"):
            t = t[:-1]
        out.append(t)
    return out


class BM25Retriever:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [tokenize(c.text) for c in chunks]
        self.doc_len = [len(d) for d in self.docs]
        self.avg_len = sum(self.doc_len) / max(len(self.docs), 1)
        self.tf = [Counter(d) for d in self.docs]
        df = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        q = tokenize(query)
        scores = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                denom = f + self.k1 * (1 - self.b + self.b * self.doc_len[i] / self.avg_len)
                s += self.idf[t] * f * (self.k1 + 1) / denom
            scores.append((self.chunks[i], s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class EmbeddingRetriever:
    """Uses an OpenAI-compatible embeddings endpoint. Set EMBED_API_KEY (or LLM_API_KEY)."""

    def __init__(self, chunks: list[Chunk], model: str | None = None):
        from openai import OpenAI

        self.client = OpenAI(
            api_key=os.getenv("EMBED_API_KEY") or os.getenv("LLM_API_KEY"),
            base_url=os.getenv("EMBED_BASE_URL") or os.getenv("LLM_BASE_URL"),
        )
        self.model = model or os.getenv("EMBED_MODEL", "text-embedding-3-small")
        self.chunks = chunks
        self.vectors = self._embed([c.text for c in chunks])

    def _embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for i in range(0, len(texts), 64):
            resp = self.client.embeddings.create(model=self.model, input=texts[i:i + 64])
            out.extend(d.embedding for d in resp.data)
        return out

    @staticmethod
    def _cos(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-9)

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        qv = self._embed([query])[0]
        scored = [(c, self._cos(qv, v)) for c, v in zip(self.chunks, self.vectors)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


class HybridRetriever:
    """Reciprocal rank fusion of several retrievers."""

    def __init__(self, retrievers: list, rrf_k: int = 60):
        self.retrievers = retrievers
        self.rrf_k = rrf_k

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        scores: dict[str, float] = {}
        by_id: dict[str, Chunk] = {}
        for r in self.retrievers:
            for rank, (chunk, _) in enumerate(r.search(query, k=20)):
                scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (self.rrf_k + rank + 1)
                by_id[chunk.id] = chunk
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]
        return [(by_id[cid], s) for cid, s in ranked]
