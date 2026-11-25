"""Read a WhatsApp order and print the packing list, or the questions to ask first.

  python run.py "2 kg aloo, 1 dozen eggs aur do packet doodh"
  python run.py                       # type messages, one per line
  LLM_API_KEY=... python run.py "..."  # LLM reading
"""

import os
import sys

from orderbot import load_catalog, read_order


def show(text: str, catalog: dict) -> None:
    if os.getenv("LLM_API_KEY"):
        from orderbot.llm import read_order_llm
        order = read_order_llm(text, catalog)
    else:
        order = read_order(text, catalog)
    print(f"Message: {text}")
    for sku, qty in order.items.items():
        unit = catalog[sku]["unit"]
        print(f"  {catalog[sku]['name']}: {qty if qty is not None else '?'} {unit}")
    if order.needs_reply:
        print("Reply before packing:")
        for q in order.reply_questions(catalog):
            print("  -", q)
    else:
        print("Ready to pack.")
    print()


def main() -> None:
    catalog = load_catalog()
    if len(sys.argv) > 1:
        show(" ".join(sys.argv[1:]), catalog)
        return
    print("Type an order message. Empty line to stop.\n")
    for line in sys.stdin:
        if not line.strip():
            break
        show(line.strip(), catalog)


if __name__ == "__main__":
    main()
