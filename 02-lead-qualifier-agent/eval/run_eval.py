"""Compare the agent's lead scoring with a budget-only baseline.

Every lead in data/leads.csv has a hand-written expected tier (hot, warm, cold).
Leads L01 to L24 were used to write and tune the rules. Leads L25 to L40 are a
holdout set that was scored once, after the rules were frozen.

  python eval/run_eval.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from leadbot import budget_only_tier, score_lead  # noqa: E402

TIERS = ("hot", "warm", "cold")


def metrics(rows: list[dict], predict) -> dict:
    preds = [predict(r) for r in rows]
    gold = [r["expected_tier"] for r in rows]
    acc = sum(p == g for p, g in zip(preds, gold)) / len(rows)
    tp = sum(p == g == "hot" for p, g in zip(preds, gold))
    pred_hot = sum(p == "hot" for p in preds)
    gold_hot = sum(g == "hot" for g in gold)
    # Hot leads that ended up as cold get no reply at all: the costly mistake.
    lost = sum(g == "hot" and p == "cold" for p, g in zip(preds, gold))
    return {
        "accuracy": acc,
        "hot_precision": tp / pred_hot if pred_hot else 0.0,
        "hot_recall": tp / gold_hot if gold_hot else 0.0,
        "hot_lost": lost,
        "misses": [r["id"] for r, p in zip(rows, preds) if p != r["expected_tier"]],
    }


def main() -> None:
    rows = list(csv.DictReader(open(ROOT / "data" / "leads.csv", encoding="utf-8")))
    sets = {"tuning (L01-L24)": rows[:24], "holdout (L25-L40)": rows[24:], "all 40": rows}
    methods = {"Budget only": budget_only_tier, "Lead agent (4 signals)": lambda r: score_lead(r).tier}

    lines = ["| Leads | Method | Accuracy | Hot precision | Hot recall | Hot leads marked cold |",
             "| --- | --- | --- | --- | --- | --- |"]
    misses = []
    for set_name, subset in sets.items():
        for m_name, fn in methods.items():
            m = metrics(subset, fn)
            lines.append(
                f"| {set_name} | {m_name} | {m['accuracy']:.0%} | {m['hot_precision']:.0%} "
                f"| {m['hot_recall']:.0%} | {m['hot_lost']} |"
            )
            if set_name == "holdout (L25-L40)":
                misses.append(f"{m_name} missed on holdout: {', '.join(m['misses']) or 'none'}")

    report = "\n".join(lines) + "\n\n" + "\n".join(misses) + "\n"
    print(report)
    (ROOT / "eval" / "results.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
