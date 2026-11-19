"""Score every labeled resume with the keyword filter and with the scorer.

    python eval/run_eval.py             # dev and holdout, writes eval/results.md
    python eval/run_eval.py --dev-only  # only the dev resumes (use this while building rules)
"""

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jobmatch import keyword_baseline, load_jobs, load_resumes, score  # noqa: E402


def metrics(rows):
    n = len(rows)
    right = sum(r["pred"] == r["gold"] for r in rows)
    false_strong = sum(r["pred"] == "strong" and r["gold"] != "strong" for r in rows)
    pred_strong = sum(r["pred"] == "strong" for r in rows)
    gold_strong = [r for r in rows if r["gold"] == "strong"]
    found_strong = sum(r["pred"] == "strong" for r in gold_strong)
    good_rejected = sum(r["pred"] == "no" and r["gold"] != "no" for r in rows)
    return {
        "Right label": f"{right}/{n} ({right / n:.0%})",
        "Shortlist (marked strong)": f"{pred_strong - false_strong}/{pred_strong} really strong",
        "Strong fits found": f"{found_strong}/{len(gold_strong)}",
        "Good candidates rejected": str(good_rejected),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-only", action="store_true")
    args = ap.parse_args()

    jobs = load_jobs(ROOT / "data" / "jobs.md")
    resumes = load_resumes(ROOT / "data" / "resumes.md")
    labels = list(csv.DictReader(open(ROOT / "data" / "labels.csv", encoding="utf-8")))
    splits = ["dev"] if args.dev_only else ["dev", "holdout"]

    table, errors = [], []
    for split in splits:
        rows = [l for l in labels if l["split"] == split]
        for method in ["Keyword filter", "Scorer"]:
            out = []
            for l in rows:
                r, j = resumes[l["resume_id"]], jobs[l["job_id"]]
                text = "\n".join(x for x in r.text.splitlines() if not x.startswith("Name:"))
                pred = keyword_baseline(text, j) if method == "Keyword filter" else score(r, j).label
                out.append({"id": l["resume_id"], "gold": l["label"], "pred": pred})
                if method == "Scorer" and pred != l["label"]:
                    errors.append((split, l["resume_id"], l["job_id"], l["label"], pred, score(r, j).reasons()))
            table.append((f"{split} ({len(rows)})", method, metrics(out)))

    cols = list(table[0][2])
    lines = ["| Resumes | Method | " + " | ".join(cols) + " |", "| --- " * (len(cols) + 2) + "|"]
    lines += [f"| {s} | {m} | " + " | ".join(v[c] for c in cols) + " |" for s, m, v in table]
    lines += ["", "## Scorer mistakes", ""]
    for split, rid, jid, gold, pred, reasons in errors:
        lines.append(f"- **{rid}** ({split}, {jid}): labeled {gold}, scored {pred}")
        lines += [f"  - {x}" for x in reasons]
    report = "\n".join(lines)
    print(report)
    if not args.dev_only:
        (ROOT / "eval" / "results.md").write_text("# Results\n\n" + report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
