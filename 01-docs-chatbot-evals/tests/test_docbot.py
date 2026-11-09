import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docbot import BM25Retriever, fixed_chunks, heading_chunks  # noqa: E402

SAMPLE = """# Guide

## Leave

### Annual leave
You get 24 days per year.

### Sick leave
You get 12 days per year.

## Travel
Book flights 7 days ahead.
"""


def test_heading_chunks_keep_heading_path():
    chunks = heading_chunks(SAMPLE, "s.md")
    assert len(chunks) == 3
    assert chunks[0].heading == "Guide > Leave > Annual leave"
    assert chunks[0].text.startswith("Guide > Leave > Annual leave")
    assert chunks[2].heading == "Guide > Travel"


def test_heading_chunks_split_long_sections():
    long_body = "\n\n".join(f"Paragraph {i} " + "word " * 40 for i in range(10))
    chunks = heading_chunks(f"# T\n\n{long_body}", "s.md", max_chars=400)
    assert len(chunks) > 1
    assert all(c.text.startswith("T") for c in chunks)


def test_fixed_chunks_cover_text():
    chunks = fixed_chunks("a" * 1000, "s.md", size=300, overlap=50)
    assert len(chunks) == 4
    assert all(len(c.text) <= 300 for c in chunks)


def test_bm25_finds_right_section():
    retriever = BM25Retriever(heading_chunks(SAMPLE, "s.md"))
    top, _ = retriever.search("how many sick days", k=1)[0]
    assert "Sick leave" in top.heading


def test_api_retrieval_only(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    from docbot.api import app

    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    data = client.post("/ask", json={"question": "What is the notice period?"}).json()
    assert data["mode"] == "retrieval-only"
    assert "60 days" in data["answer"]
