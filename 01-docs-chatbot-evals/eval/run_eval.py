"""Compare chunking strategies on a fixed question set.

A question counts as a hit at rank r if the exact answer sentence appears
in the chunk at rank r. Metrics:
  hit@1  right chunk is first
  hit@3  right chunk is in the top 3
  MRR    mean of 1/rank of the first right chunk (top 5), 0 if missing

Usage:
  python eval/run_eval.py                 # BM25 only, no API key needed
  python eval/run_eval.py --embeddings    # also embeddings and hybrid (needs a key)
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docbot import BM25Retriever, EmbeddingRetriever, HybridRetriever, fixed_chunks, heading_chunks  # noqa: E402


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def load_questions(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(retriever, questions: list[dict], k: int = 5) -> dict:
    h1 = h3 = 0
    rr_total = 0.0
    misses = []
    for q in questions:
        results = retriever.search(q["question"], k=k)
        target = norm(q["answer_contains"])
        rank = next((i + 1 for i, (c, _) in enumerate(results) if target in norm(c.text)), None)
        if rank == 1:
            h1 += 1
        if rank and rank <= 3:
            h3 += 1
        if rank:
            rr_total += 1 / rank
        else:
            misses.append(q["question"])
    n = len(questions)
    return {"hit@1": h1 / n, "hit@3": h3 / n, "mrr": rr_total / n, "misses": misses}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--embeddings", action="store_true", help="also run embedding and hybrid retrieval")
    ap.add_argument("--out", default=str(ROOT / "eval" / "results.md"))
    args = ap.parse_args()

    doc_path = ROOT / "data" / "northwind_handbook.md"
    text = doc_path.read_text(encoding="utf-8")
    questions = load_questions(ROOT / "eval" / "questions.jsonl")

    strategies = {
        "fixed 300 chars": fixed_chunks(text, doc_path.name, size=300, overlap=30),
        "fixed 800 chars": fixed_chunks(text, doc_path.name, size=800, overlap=80),
        "heading-based": heading_chunks(text, doc_path.name),
    }

    rows = []
    for name, chunks in strategies.items():
        bm25 = BM25Retriever(chunks)
        rows.append((name, "BM25", len(chunks), evaluate(bm25, questions)))
        if args.embeddings:
            emb = EmbeddingRetriever(chunks)
            rows.append((name, "embeddings", len(chunks), evaluate(emb, questions)))
            rows.append((name, "hybrid", len(chunks), evaluate(HybridRetriever([bm25, emb]), questions)))

    lines = [
        f"Questions: {len(questions)}",
        "",
        "| Chunking | Retriever | Chunks | Hit@1 | Hit@3 | MRR |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, retr, n_chunks, m in rows:
        lines.append(f"| {name} | {retr} | {n_chunks} | {m['hit@1']:.0%} | {m['hit@3']:.0%} | {m['mrr']:.2f} |")
    lines.append("")
    for name, retr, _, m in rows:
        if m["misses"]:
            lines.append(f"Missed by {name} + {retr}: " + "; ".join(m["misses"]))
    report = "\n".join(lines)

    Path(args.out).write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
