"""Score the extractors against hand-labeled tasks.

A predicted task matches a labeled task when both point at the same transcript turn.
- Precision: share of predicted tasks that are real tasks
- Recall: share of real tasks that were found
- Owner right / Due right: among matched tasks
- Fully right: real tasks found with the correct owner AND the correct due date

Usage: python eval/run_eval.py [--modes baseline,rules,llm]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meetbot.agent import run  # noqa: E402


def score(gold: list[dict], pred: list[dict]) -> dict:
    g = {t["turn"]: t for t in gold}
    p = {t["turn"]: t for t in pred}
    matched = [n for n in p if n in g]
    owner_ok = sum(p[n]["owner"] == g[n]["owner"] for n in matched)
    due_ok = sum(p[n]["due"] == g[n]["due"] for n in matched)
    full = sum(p[n]["owner"] == g[n]["owner"] and p[n]["due"] == g[n]["due"] for n in matched)
    return {"gold": len(g), "pred": len(p), "matched": len(matched),
            "owner_ok": owner_ok, "due_ok": due_ok, "full": full}


def pct(a, b):
    return f"{100 * a / b:.0f}%" if b else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", default="baseline,rules")
    args = ap.parse_args()
    rows = [json.loads(line) for line in (ROOT / "eval" / "gold.jsonl").read_text().splitlines() if line.strip()]
    out = ["| Split | Method | Tasks (real) | Precision | Recall | Owner right | Due date right | Fully right |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    misses = []
    for split in ["dev", "holdout"]:
        for mode in args.modes.split(","):
            tot = dict(gold=0, pred=0, matched=0, owner_ok=0, due_ok=0, full=0)
            for row in [r for r in rows if r["split"] == split]:
                raw = (ROOT / "data" / "transcripts" / row["file"]).read_text()
                pred = run(raw, mode=mode)["tasks"]
                s = score(row["tasks"], pred)
                for k in tot:
                    tot[k] += s[k]
                if mode == "rules":
                    g = {t["turn"]: t for t in row["tasks"]}
                    p = {t["turn"]: t for t in pred}
                    for n in sorted(set(g) | set(p)):
                        if n not in p:
                            misses.append(f"{row['file']} turn {n}: missed (owner {g[n]['owner']}, due {g[n]['due']})")
                        elif n not in g:
                            misses.append(f"{row['file']} turn {n}: not a real task, but extracted")
                        elif (p[n]["owner"], p[n]["due"]) != (g[n]["owner"], g[n]["due"]):
                            misses.append(f"{row['file']} turn {n}: got owner {p[n]['owner']}, due {p[n]['due']}; "
                                          f"expected owner {g[n]['owner']}, due {g[n]['due']}")
            out.append(f"| {split} | {mode} | {tot['gold']} | {pct(tot['matched'], tot['pred'])} | "
                       f"{pct(tot['matched'], tot['gold'])} | {pct(tot['owner_ok'], tot['matched'])} | "
                       f"{pct(tot['due_ok'], tot['matched'])} | {tot['full']}/{tot['gold']} ({pct(tot['full'], tot['gold'])}) |")
    text = "\n".join(out) + "\n\nRules mode errors:\n\n" + "\n".join(f"- {m}" for m in misses) + "\n"
    print(text)
    (ROOT / "eval" / "results.md").write_text("# Results\n\n" + text)


if __name__ == "__main__":
    main()
