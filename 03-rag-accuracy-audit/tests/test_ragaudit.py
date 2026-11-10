import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ragaudit import BM25Retriever, Chunk, audit, find_bad_chunks, fix_chunks, load_retriever, paragraph_chunks  # noqa: E402
from ragaudit.chunks import chunk_folder, load_chunks, save_chunks  # noqa: E402
from ragaudit.cli import main  # noqa: E402

DOC = """---
updated: 2025-01-01
---
# Guide

## Leave
You get 24 days of paid leave every calendar year.
"""

FOOTER = "Questions? Email the help desk about leave, travel, payroll and laptops any time."


def c(cid, text, doc="a.md", updated="2025-01-01"):
    return Chunk(id=cid, doc=doc, text=text, updated=updated)


def test_paragraph_chunks_split_headings_and_read_date():
    chunks = paragraph_chunks(DOC, "g.md")
    assert [x.text for x in chunks] == ["# Guide", "## Leave", "You get 24 days of paid leave every calendar year."]
    assert chunks[0].updated == "2025-01-01"


def test_flags_tiny_boilerplate_and_stale():
    chunks = [
        c("a#0", "## Leave"),
        c("a#1", "You get 24 days of paid leave every calendar year."),
        c("b#0", "## Leave", doc="b.md", updated="2022-01-01"),
        c("b#1", "You get 12 days of paid leave every calendar year.", doc="b.md", updated="2022-01-01"),
        c("x#0", FOOTER, doc="x.md"), c("y#0", FOOTER, doc="y.md"), c("z#0", FOOTER, doc="z.md"),
    ]
    bad = find_bad_chunks(chunks)
    assert "tiny" in bad["a#0"]
    assert "boilerplate" in bad["x#0"]
    assert "conflict" in bad["a#1"]  # same sentence, different number
    assert any(i.startswith("stale") for i in bad["b#1"])
    assert "a#1" in bad and not any(i.startswith("stale") for i in bad["a#1"])


def test_fix_drops_stale_dedupes_and_merges():
    chunks = [
        c("a#0", "## Leave"), c("a#1", "You get 24 days of paid leave every calendar year."),
        c("b#0", "## Leave", doc="b.md", updated="2022-01-01"),
        c("b#1", "You get 12 days of paid leave every calendar year.", doc="b.md", updated="2022-01-01"),
        c("x#0", FOOTER, doc="x.md"), c("y#0", FOOTER, doc="y.md"), c("z#0", FOOTER, doc="z.md"),
    ]
    fixed, log = fix_chunks(chunks)
    texts = [x.text for x in fixed]
    assert "## Leave\nYou get 24 days of paid leave every calendar year." in texts
    assert not any("12 days" in t for t in texts)
    assert texts.count(FOOTER) == 1
    assert any("stale" in line for line in log)


def test_audit_metrics_and_misses():
    chunks = [c("1", "## Refunds"), c("2", "Refunds reach your card within 5 business days.")]
    q = [{"question": "refunds", "answer": "5 business days"}]
    result = audit(chunks, BM25Retriever(chunks), q)
    assert result["metrics"]["hit@1"] == 0.0  # the heading-only chunk wins
    assert result["metrics"]["hit@3"] == 1.0
    assert result["metrics"]["mrr"] == 0.5
    assert result["crowders"][0]["id"] == "1"
    fixed, _ = fix_chunks(chunks)
    assert audit(fixed, BM25Retriever(fixed), q)["metrics"]["hit@1"] == 1.0


def test_stemming_matches_plural():
    chunks = [c("1", "Sofas come by van."), c("2", "Lamps ship by courier.")]
    assert BM25Retriever(chunks).search("sofa", 1) == []
    assert BM25Retriever(chunks, use_stem=True).search("sofa", 1) == ["1"]


def test_custom_retriever_loads_from_module_path():
    r = load_retriever("tests.fake_retriever:build", [c("1", "hello world")])
    assert r.search("anything", 3) == ["1"]


def test_demo_fix_beats_raw(tmp_path):
    q = [json.loads(l) for l in (ROOT / "eval/questions.jsonl").read_text().splitlines() if l.strip()]
    raw = chunk_folder(ROOT / "data/docs")
    fixed, _ = fix_chunks(raw)
    before = audit(raw, BM25Retriever(raw), q)["metrics"]["hit@1"]
    after = audit(fixed, BM25Retriever(fixed), q)["metrics"]["hit@1"]
    assert after > before


def test_cli_roundtrip(tmp_path, capsys):
    chunks_path, fixed_path, report = tmp_path / "c.jsonl", tmp_path / "f.jsonl", tmp_path / "r.md"
    main(["chunk", str(ROOT / "data/docs"), str(chunks_path)])
    main(["fix", str(chunks_path), str(fixed_path)])
    main(["audit", "--chunks", str(fixed_path), "--questions", str(ROOT / "eval/questions.jsonl"),
          "--report", str(report)])
    assert "Hit@1" in report.read_text()
    assert len(load_chunks(fixed_path)) < len(load_chunks(chunks_path))
    save_chunks(load_chunks(fixed_path), tmp_path / "again.jsonl")


def test_llm_explain_uses_openai_compatible_client(monkeypatch):
    import types

    import openai

    from ragaudit import llm

    class FakeClient:
        def __init__(self, api_key, base_url):
            assert api_key == "test-key"
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self.create))

        def create(self, **kw):
            msg = types.SimpleNamespace(content=" The heading chunk has the same words but no answer. ")
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setattr(openai, "OpenAI", FakeClient)
    assert llm.llm_enabled()
    assert llm.explain_miss("q", "a", "## Refunds") == "The heading chunk has the same words but no answer."
