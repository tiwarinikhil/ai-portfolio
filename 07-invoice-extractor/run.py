"""Read an invoice text file and print its fields as JSON, plus anything a person should check.

  python run.py data/invoices/INV04.txt
  python run.py my_invoice.txt --json out.json
  LLM_API_KEY=... python run.py my_invoice.txt     # LLM extraction, same checks
"""

import argparse
import json
import os
from pathlib import Path

from invoicebot import extract


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="invoice as plain text (OCR or PDF-to-text output)")
    ap.add_argument("--json", help="also save the result to this JSON file")
    args = ap.parse_args()
    text = Path(args.file).read_text(encoding="utf-8")

    if os.getenv("LLM_API_KEY"):
        from invoicebot.llm import extract_llm
        inv = extract_llm(text)
    else:
        inv = extract(text)

    out = inv.to_dict()
    print(json.dumps(out, indent=2))
    print("\nOK to enter." if not inv.review else "\nCheck before paying:\n" + "\n".join(f"- {r}" for r in inv.review))
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
