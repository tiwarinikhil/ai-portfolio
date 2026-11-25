"""Score the order reader and a quick catalog search against the hand labels.

    python eval/run_eval.py             # dev and holdout, writes eval/results.md
    python eval/run_eval.py --dev-only  # only the dev messages (use this while building rules)
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orderbot import baseline, load_catalog, read_order  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev-only", action="store_true")
    args = ap.parse_args()
    catalog = load_catalog()
    msgs = [json.loads(l) for l in open(ROOT / "data" / "messages.jsonl", encoding="utf-8")]
    splits = ["dev"] if args.dev_only else ["dev", "holdout"]

    table, misses = [], []
    for split in splits:
        rows = [m for m in msgs if m["split"] == split]
        for method, fn in [("Quick catalog search", baseline), ("Order reader", read_order)]:
            items_ok = items_all = extra = full = caught = need = false_alarm = silent = 0
            for m in rows:
                o = fn(m["text"], catalog)
                gold_reply = bool(m["unknown"]) or any(v is None for v in m["items"].values())
                items_all += len(m["items"])
                items_ok += sum(s in o.items and o.items[s] == q for s, q in m["items"].items())
                extra += sum(s not in m["items"] for s in o.items)
                need += gold_reply
                caught += gold_reply and o.needs_reply
                false_alarm += (not gold_reply) and o.needs_reply
                ok = o.items == m["items"] and o.needs_reply == gold_reply
                full += ok
                silent += (o.items != m["items"]) and not o.needs_reply
                if method == "Order reader" and not ok:
                    misses.append((split, m["id"], m["text"], m["items"], o.items, o.unknown))
            n = len(rows)
            table.append([f"{split} ({n})", method, f"{items_ok}/{items_all}", str(extra), f"{full}/{n} ({full / n:.0%})",
                          f"{caught}/{need}", str(false_alarm), str(silent)])

    head = ["Messages", "Method", "Items right", "Wrong items added", "Orders fully right", "Needs reply: caught", "Needless questions", "Wrong and not flagged"]
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * len(head)]
    lines += ["| " + " | ".join(r) + " |" for r in table]
    lines += ["", "## Order reader mistakes", ""]
    for split, mid, text, want, got, unk in misses:
        lines.append(f"- **{mid}** ({split}) `{text}`: expected {want}, got {got}" + (f", unknown {unk}" if unk else ""))
    report = "\n".join(lines)
    print(report)
    if not args.dev_only:
        (ROOT / "eval" / "results.md").write_text("# Results\n\n" + report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
