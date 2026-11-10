"""Score every lead in a CSV, draft replies, and ask you to approve each one.

  python run.py data/leads.csv            # review drafts one by one
  python run.py data/leads.csv --no-input # skip review, save drafts as pending

Results go to outbox/: approved.jsonl (ready to send) and pending.jsonl.
Nothing is ever sent by this script. Sending stays a human step.
"""

import argparse
import csv
import json
from pathlib import Path

from langgraph.types import Command

from leadbot import build_graph

TIER_ORDER = {"hot": 0, "warm": 1, "cold": 2}


def review(payload: dict) -> dict:
    print(f"\n--- {payload['lead_id']} | {payload['tier'].upper()} | score {payload['score']}")
    print("Why: " + "; ".join(payload["reasons"]))
    print("\n" + payload["draft"] + "\n")
    choice = input("[a]pprove, [e]dit, [r]eject? ").strip().lower()
    if choice.startswith("a"):
        return {"action": "approve"}
    if choice.startswith("e"):
        return {"action": "edit", "text": input("New reply (one line): ")}
    return {"action": "reject"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--no-input", action="store_true", help="do not ask, keep drafts as pending")
    ap.add_argument("--out", default="outbox")
    args = ap.parse_args()

    leads = list(csv.DictReader(open(args.csv_path, encoding="utf-8")))
    graph = build_graph()
    out = Path(args.out)
    out.mkdir(exist_ok=True)
    results = []

    for lead in leads:
        config = {"configurable": {"thread_id": lead["id"]}}
        state = graph.invoke({"lead": lead}, config)
        if "__interrupt__" in state:
            payload = state["__interrupt__"][0].value
            if args.no_input:
                results.append({**payload, "status": "pending"})
                continue
            state = graph.invoke(Command(resume=review(payload)), config)
        results.append(
            {
                "lead_id": lead["id"],
                "tier": state["tier"],
                "score": state["score"],
                "reasons": state["reasons"],
                "status": state["decision"],
                "reply": state.get("final_reply", ""),
            }
        )

    results.sort(key=lambda r: (TIER_ORDER[r["tier"]], -r["score"]))
    approved = [r for r in results if r["status"] in ("approved", "edited")]
    pending = [r for r in results if r["status"] == "pending"]
    (out / "approved.jsonl").write_text("".join(json.dumps(r) + "\n" for r in approved), encoding="utf-8")
    (out / "pending.jsonl").write_text("".join(json.dumps(r) + "\n" for r in pending), encoding="utf-8")

    counts = {t: sum(r["tier"] == t for r in results) for t in TIER_ORDER}
    print(f"\nLeads: {len(results)} | hot {counts['hot']} | warm {counts['warm']} | cold {counts['cold']}")
    print(f"Approved: {len(approved)} | Pending review: {len(pending)} | Saved to {out}/")
    print("\nTop 5 to reply to first:")
    for r in results[:5]:
        print(f"  {r['lead_id']}  {r['tier']:<4}  {r['score']:>3}  {r['reasons'][2]}")


if __name__ == "__main__":
    main()
