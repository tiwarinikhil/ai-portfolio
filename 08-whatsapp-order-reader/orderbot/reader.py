"""Turn a WhatsApp order message into a packing list.

    message -> words -> split into parts at "," "and" "aur" "."
            -> in each part: find products and their quantities
            -> anything left that is not a filler word = something we don't sell
            -> unknown items or missing quantities = the shop must reply first

The word lists below were built from the dev messages only.
"""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

CATALOG_FILE = Path(__file__).resolve().parents[1] / "data" / "catalog.csv"

# Other names customers use. Hindi words written in English letters.
ALIASES = {
    "aloo": "potato", "pyaaz": "onion", "tamatar": "tomato", "anda": "eggs", "doodh": "milk",
    "dahi": "curd", "dhaniya": "coriander", "chini": "sugar", "namak": "salt",
}
NUMBER_WORDS = {"ek": 1, "do": 2, "aadha": 0.5}
# unit word -> (unit it belongs to, multiplier)
UNITS = {
    "kg": ("kg", 1), "kilo": ("kg", 1), "gm": ("kg", 0.001),
    "dozen": ("dozen", 1), "packet": ("packet", 1), "litre": ("litre", 1), "ltr": ("litre", 1),
    "bunch": ("bunch", 1),
}
FILLERS = {
    "hi", "bhaiya", "please", "send", "need", "also", "some", "kal", "subah", "tak", "bhej", "dena",
    "can", "you", "thanks",
}
SPLIT_WORDS = {"and", "aur"}


@dataclass
class Order:
    items: dict[str, float | None] = field(default_factory=dict)
    unknown: list[str] = field(default_factory=list)

    @property
    def needs_reply(self) -> bool:
        return bool(self.unknown) or any(q is None for q in self.items.values())

    def reply_questions(self, catalog: dict) -> list[str]:
        out = [f"How much {catalog[s]['name'].lower()} do you need?" for s, q in self.items.items() if q is None]
        out += [f"Sorry, we don't have \"{w}\". Anything else instead?" for w in self.unknown]
        return out


def load_catalog(path: Path = CATALOG_FILE) -> dict:
    with open(path, encoding="utf-8") as f:
        return {r["sku"]: r for r in csv.DictReader(f)}


def tokens(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(r"(\d)([a-z])", r"\1 \2", t)   # 5kg -> 5 kg
    t = re.sub(r"[,.!?;]", " , ", t)
    return t.split()


def parts(words: list[str]) -> list[list[str]]:
    out, cur = [], []
    for w in words:
        if w == "," or w in SPLIT_WORDS:
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(w)
    if cur:
        out.append(cur)
    return out


def number(w: str) -> float | None:
    if re.fullmatch(r"\d+(\.\d+)?", w):
        return float(w)
    return NUMBER_WORDS.get(w)


def quantities(words: list[str]) -> list[tuple[int, float, str | None]]:
    """(position, amount, unit word or None) for every number in the part."""
    out = []
    for i, w in enumerate(words):
        n = number(w)
        if n is not None:
            unit = words[i + 1] if i + 1 < len(words) and words[i + 1] in UNITS else None
            out.append((i, n, unit))
    return out


def to_shop_unit(amount: float, unit_word: str | None, sku: str, catalog: dict) -> float:
    shop_unit = catalog[sku]["unit"]
    if unit_word:
        unit, mult = UNITS[unit_word]
        return round(amount * mult, 3) if unit == shop_unit else amount
    if shop_unit == "dozen":
        return round(amount / 12, 3)   # "6 eggs" means 6 pieces
    return amount


def read_order(text: str, catalog: dict | None = None) -> Order:
    catalog = catalog or load_catalog()
    order = Order()
    for part in parts(tokens(text)):
        found = [(i, ALIASES.get(w, w)) for i, w in enumerate(part) if ALIASES.get(w, w) in catalog]
        qty = quantities(part)
        used = {i for i, _ in found}
        for i, _, unit in qty:
            used.add(i)
            if unit:
                used.add(i + 1)
        if found:
            # Quantity before the product ("2 kg aloo") or after it ("milk 2 packet")?
            before = bool(qty) and qty[0][0] < found[0][0]
            for k, (pos, sku) in enumerate(found):
                if before:
                    cands = [q for q in qty if q[0] < pos and (k == 0 or q[0] > found[k - 1][0])]
                    q = cands[-1] if cands else None
                else:
                    nxt = found[k + 1][0] if k + 1 < len(found) else len(part)
                    cands = [q for q in qty if pos < q[0] < nxt]
                    q = cands[0] if cands else None
                order.items[sku] = to_shop_unit(q[1], q[2], sku, catalog) if q else None
        leftover = [w for i, w in enumerate(part)
                    if i not in used and w not in FILLERS and w not in UNITS and not re.fullmatch(r"\d+", w)]
        if leftover:
            order.unknown.append(" ".join(leftover))
    return order


def baseline(text: str, catalog: dict | None = None) -> Order:
    """A quick catalog search: English product names only, number just before the name, else 1."""
    catalog = catalog or load_catalog()
    words = tokens(text)
    order = Order()
    for i, w in enumerate(words):
        if w in catalog:
            prev = words[i - 1] if i > 0 else ""
            order.items[w] = float(prev) if re.fullmatch(r"\d+", prev) else 1.0
    return order
