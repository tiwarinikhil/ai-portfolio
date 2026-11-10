"""Before/after benchmark for the demo help center.

Chunks the demo docs the quick way (split on blank lines), audits them,
then measures each fix on its own and all fixes together.

  python eval/run_eval.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ragaudit import BM25Retriever, audit, fix_chunks  # noqa: E402
from ragaudit.chunks import chunk_folder  # noqa: E402

QUESTIONS = [json.loads(l) for l in (ROOT / "eval/questions.jsonl").read_text().splitlines() if l.strip()]


def row(name, chunks, stem=False):
    m = audit(chunks, BM25Retriever(chunks, use_stem=stem), QUESTIONS)["metrics"]
    return f"| {name} | {len(chunks)} | {m['hit@1']:.0%} | {m['hit@3']:.0%} | {m['mrr']:.2f} |"


def main():
    raw = chunk_folder(ROOT / "data/docs")
    lines = [f"{len(QUESTIONS)} questions, retriever BM25 (top 5).", "",
             "| Setup | Chunks | Hit@1 | Hit@3 | MRR |", "| --- | --- | --- | --- | --- |",
             row("Raw chunks (split on blank lines)", raw)]
    for step, name in [("stale", "Only drop the stale document"), ("dedupe", "Only remove duplicate footers"),
                       ("merge", "Only merge heading chunks")]:
        lines.append(row(name, fix_chunks(raw, steps=(step,))[0]))
    fixed = fix_chunks(raw)[0]
    lines.append(row("All three fixes", fixed))
    lines.append(row("All three fixes + simple stemming", fixed, stem=True))
    text = "\n".join(lines) + "\n"
    (ROOT / "eval/results.md").write_text("# Results\n\n" + text)
    print(text)


if __name__ == "__main__":
    main()
