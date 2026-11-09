"""FastAPI app: a chat page plus a JSON API.

Run:  uvicorn docbot.api:app --reload
Then open http://127.0.0.1:8000
Put your own .md or .txt files in data/ to chat with them.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .chunking import heading_chunks
from .llm import answer
from .retrieval import BM25Retriever, EmbeddingRetriever, HybridRetriever

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))


def build_retriever():
    chunks = []
    for path in sorted(DATA_DIR.glob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            chunks.extend(heading_chunks(path.read_text(encoding="utf-8"), path.name))
    bm25 = BM25Retriever(chunks)
    if os.getenv("USE_EMBEDDINGS") == "1":
        return HybridRetriever([bm25, EmbeddingRetriever(chunks)]), len(chunks)
    return bm25, len(chunks)


retriever, n_chunks = build_retriever()
app = FastAPI(title="Docs Chatbot")


class Ask(BaseModel):
    question: str
    k: int = 4


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "chunks": n_chunks}


@app.post("/ask")
def ask(body: Ask):
    hits = retriever.search(body.question, k=body.k)
    return answer(body.question, [c for c, _ in hits])
