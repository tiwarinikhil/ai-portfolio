"""Score the extractor and the quick regex baseline against the hand labels.

    python eval/run_eval.py             # dev and holdout, writes eval/results.md
    python eval/run_eval.py --dev-only  # only the dev invoices (use this while building rules)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invoicebot import baseline, extract  # noqa: E402

FIELDS = ["vendor", "invoice_no", "date", "gstin", "subtotal", "tax", "total"]
PROBLEMS = ["total_mismatch", "bad_gstin"]


def field_right(name, got, want):
    if name == "vendor":
        return got is not None and got.lower().startswith(want.lower())
    if name in ("subtotal", "tax", "total"):
        return got is not None and abs(got - want) < 0.01
    return got == want


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-only", action="store_true")
    args = ap.parse_args()
    labels = [json.loads(l) for l in open(ROOT / "data" / "labels.jsonl", encoding="utf-8")]
    splits = ["dev"] if args.dev_only else ["dev", "holdout"]

    table, misses = [], []
    for split in splits:
        rows = [l for l in labels if l["split"] == split]
        for method, fn in [("Quick regex", baseline), ("Extractor + checks", extract)]:
            fields_ok = invoices_ok = caught = real = false_alarm = silent = 0
            for l in rows:
                inv = fn((ROOT / "data" / "invoices" / f"{l['id']}.txt").read_text(encoding="utf-8"))
                got = inv.to_dict()
                wrong = [f for f in FIELDS if not field_right(f, got[f], l[f])]
                fields_ok += len(FIELDS) - len(wrong)
                invoices_ok += not wrong
                silent += bool(wrong) and not inv.review
                real += len(l["problems"])
                caught += sum(p in inv.problems for p in l["problems"])
                false_alarm += sum(p not in l["problems"] for p in inv.problems if p in PROBLEMS)
                if method.startswith("Extractor") and wrong:
                    misses.append((split, l["id"], [(f, got[f], l[f]) for f in wrong]))
            n = len(rows)
            table.append([f"{split} ({n})", method, f"{fields_ok}/{n * len(FIELDS)} ({fields_ok / (n * len(FIELDS)):.0%})",
                          f"{invoices_ok}/{n}", f"{caught}/{real}", str(false_alarm), str(silent)])

    head = ["Invoices", "Method", "Fields right", "Invoices fully right", "Problems caught", "False alarms", "Wrong and not flagged"]
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    lines += ["| " + " | ".join(r) + " |" for r in table]
    lines += ["", "## Extractor mistakes", ""]
    for split, iid, wrong in misses:
        lines.append(f"- **{iid}** ({split}): " + "; ".join(f"{f} got `{g}`, expected `{w}`" for f, g, w in wrong))
    report = "\n".join(lines)
    print(report)
    if not args.dev_only:
        (ROOT / "eval" / "results.md").write_text("# Results\n\n" + report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
