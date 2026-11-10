"""Command line.

  python -m ragaudit chunk  data/docs  data/chunks.jsonl
  python -m ragaudit audit  --chunks data/chunks.jsonl --questions eval/questions.jsonl
  python -m ragaudit fix    data/chunks.jsonl data/chunks_fixed.jsonl
"""

import argparse
import json
from pathlib import Path

from .audit import audit
from .chunks import chunk_folder, load_chunks, save_chunks
from .fix import fix_chunks
from .llm import explain_miss, llm_enabled
from .retrievers import load_retriever


def load_questions(path) -> list[dict]:
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def render_report(result: dict, by_id: dict, explain: bool = False) -> str:
    m = result["metrics"]
    k_key = [key for key in m if key.startswith("hit@") and key not in ("hit@1", "hit@3")][0]
    out = ["# RAG accuracy audit", "",
           f"{m['questions']} questions, {m['chunks']} chunks.", "",
           f"| Hit@1 | Hit@3 | {k_key.title()} | MRR | Flagged chunks |", "| --- | --- | --- | --- | --- |",
           f"| {pct(m['hit@1'])} | {pct(m['hit@3'])} | {pct(m[k_key])} | {m['mrr']:.2f} | {result['flagged_chunks']} |",
           "", "## Misses (right passage not ranked first)", ""]
    misses = [r for r in result["rows"] if r["rank"] != 1]
    if not misses:
        out.append("None.")
    for r in misses:
        issues = ", ".join(r["top_issues"]) or "no flag"
        line = f"- **{r['question']}** right passage at rank {r['rank'] or 'not found'}; top was `{r['top']}` ({issues})"
        if explain and r["top"]:
            line += f"\n  - LLM: {explain_miss(r['question'], r['answer'], by_id[r['top']].text)}"
        out.append(line)
    out += ["", "## Chunks that push right answers down", "", "| Chunk | Wrong top-1 | Issues | Text |",
            "| --- | --- | --- | --- |"]
    for c in result["crowders"]:
        text = c["text"].replace("\n", " ").replace("|", "/")
        out.append(f"| `{c['id']}` | {c['wrong_top1']} | {', '.join(c['issues']) or '-'} | {text} |")
    out += ["", "## All flagged chunks", ""]
    counts = {}
    for issues in result["bad"].values():
        for i in issues:
            key = i.split(" ")[0]
            counts[key] = counts.get(key, 0) + 1
    out += [f"- {k}: {v}" for k, v in sorted(counts.items())] or ["None."]
    return "\n".join(out) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(prog="ragaudit")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chunk", help="split a folder of .md files into chunks.jsonl (paragraph split)")
    c.add_argument("folder")
    c.add_argument("out")
    a = sub.add_parser("audit", help="score a retriever and flag bad chunks")
    a.add_argument("--chunks", required=True)
    a.add_argument("--questions", required=True)
    a.add_argument("--retriever", default="bm25", help="bm25 or module:factory")
    a.add_argument("--k", type=int, default=5)
    a.add_argument("--report", help="write a markdown report here")
    a.add_argument("--explain", action="store_true", help="ask the LLM why each miss happened (needs LLM_API_KEY)")
    f = sub.add_parser("fix", help="apply safe fixes and write a new chunks file")
    f.add_argument("chunks")
    f.add_argument("out")
    args = p.parse_args(argv)

    if args.cmd == "chunk":
        chunks = chunk_folder(args.folder)
        save_chunks(chunks, args.out)
        print(f"wrote {len(chunks)} chunks to {args.out}")
    elif args.cmd == "audit":
        chunks = load_chunks(args.chunks)
        result = audit(chunks, load_retriever(args.retriever, chunks), load_questions(args.questions), args.k)
        explain = args.explain and llm_enabled()
        if args.explain and not explain:
            print("LLM_API_KEY not set, skipping LLM explanations.")
        report = render_report(result, {c.id: c for c in chunks}, explain)
        if args.report:
            Path(args.report).write_text(report)
        print(report)
    elif args.cmd == "fix":
        fixed, log = fix_chunks(load_chunks(args.chunks))
        save_chunks(fixed, args.out)
        print("\n".join(log))
        print(f"wrote {len(fixed)} chunks to {args.out}")
