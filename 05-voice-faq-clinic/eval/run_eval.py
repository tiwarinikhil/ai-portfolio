"""Score the clinic phone agent against a quick FAQ bot.

Every caller transcript in data/calls.jsonl has a hand-written expected outcome:
an FAQ id, "urgent" (emergency) or "handoff" (a person must take the call).
Labels were committed before any code. The rules were built on the dev calls only.
The holdout calls were scored once, after the rules were frozen.

  python eval/run_eval.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from voicefaq import ClinicAgent, baseline  # noqa: E402


def score(rows, predict):
    preds = [predict(r["transcript"]) for r in rows]
    gold = [r["expected"] for r in rows]
    n = len(rows)
    right = sum(p == g for p, g in zip(preds, gold))
    faq_rows = [(p, g) for p, g in zip(preds, gold) if g not in ("urgent", "handoff")]
    urgent = [(p, g) for p, g in zip(preds, gold) if g == "urgent"]
    # A wrong answer: the bot read out an FAQ answer when it should have said something else.
    wrong_answers = sum(p not in ("urgent", "handoff") and p != g for p, g in zip(preds, gold))
    misses = [r["id"] for r, p in zip(rows, preds) if p != r["expected"]]
    return {
        "n": n,
        "right": right,
        "faq_right": sum(p == g for p, g in faq_rows),
        "faq_n": len(faq_rows),
        "urgent_caught": sum(p == "urgent" for p, _ in urgent),
        "urgent_n": len(urgent),
        "wrong_answers": wrong_answers,
        "misses": misses,
    }


def main():
    rows = [json.loads(line) for line in open(ROOT / "data" / "calls.jsonl", encoding="utf-8")]
    agent = ClinicAgent()
    methods = {
        "Quick FAQ bot": lambda t: baseline(agent.search, t),
        "Clinic agent": lambda t: (lambda r: r.faq_id if r.action == "answer" else r.action)(agent.handle(t)),
    }
    splits = {"dev": [r for r in rows if r["split"] == "dev"], "holdout": [r for r in rows if r["split"] == "holdout"]}
    if "--dev-only" in sys.argv:
        splits.pop("holdout")

    lines = [
        "| Calls | Method | Right action | FAQ answered right | Emergencies caught | Wrong answers read out |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    notes = []
    for split, subset in splits.items():
        for name, fn in methods.items():
            m = score(subset, fn)
            lines.append(
                f"| {split} ({m['n']}) | {name} | {m['right']}/{m['n']} ({m['right'] / m['n']:.0%}) "
                f"| {m['faq_right']}/{m['faq_n']} | {m['urgent_caught']}/{m['urgent_n']} | {m['wrong_answers']} |"
            )
            notes.append(f"{name}, {split} misses: {', '.join(m['misses']) or 'none'}")
    report = "\n".join(lines) + "\n\n" + "\n".join(notes) + "\n"
    print(report)
    if "--dev-only" not in sys.argv:
        (ROOT / "eval" / "results.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
