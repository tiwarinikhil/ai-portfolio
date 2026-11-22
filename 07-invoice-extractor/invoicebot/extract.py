"""Pull the key fields out of an invoice's text, then check them.

Offline mode reads the invoice line by line and looks for the labels that
small Indian suppliers commonly print. The label lists were built from the
dev invoices only.
"""

import re
from dataclasses import asdict, dataclass, field

from .parse import GSTIN_LIKE, amounts, find_date, gstin_ok, last_amount

SUBTOTAL_LABELS = ["sub total", "sub-total", "subtotal", "taxable value", "taxable amount", "total before tax"]
TOTAL_LABELS = ["grand total", "amount payable", "total amount", "invoice total", "net amount"]
NOT_TOTAL = ["before tax", "advance", "balance"]
TAX_LINE = re.compile(r"^(cgst|sgst|igst|gst)\b(?!in)", re.I)
INVOICE_NO = re.compile(r"\b(?:invoice\s*(?:no\.?|number|#)|inv\s*no\.?|bill\s*no\.?|invoice)\s*[:.#]?\s*([A-Z0-9][A-Z0-9/\-]+)", re.I)
BUYER_WORDS = ["bill to", "buyer", "ship to"]
HEADER_WORDS = ["tax invoice", "invoice"]


@dataclass
class Invoice:
    vendor: str | None = None
    invoice_no: str | None = None
    date: str | None = None
    gstin: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    problems: list[str] = field(default_factory=list)
    review: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _starts(line: str, labels: list[str]) -> bool:
    low = line.lower()
    return any(low.startswith(lb) for lb in labels)


def extract(text: str) -> Invoice:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    inv = Invoice()

    # Vendor: the "From:" line if there is one, else the first line that is not a heading.
    for ln in lines:
        if ln.lower().startswith("from:"):
            inv.vendor = ln.split(":", 1)[1].strip()
            break
    if inv.vendor is None:
        inv.vendor = next((ln for ln in lines if ln.lower() not in HEADER_WORDS), None)

    for ln in lines:
        low = ln.lower()
        # Invoice number: skip PO numbers.
        if inv.invoice_no is None and not low.startswith("po "):
            m = INVOICE_NO.search(ln)
            if m and not m[1].lower().startswith(("date", "dt")):
                inv.invoice_no = m[1]
        # Date: the invoice date, never the due date.
        if inv.date is None and "date" in low and "due" not in low:
            inv.date = find_date(ln)
        # Seller GSTIN: skip the buyer's.
        if inv.gstin is None and "gst" in low and not any(w in low for w in BUYER_WORDS):
            m = GSTIN_LIKE.search(ln)
            if m:
                inv.gstin = m[0]

    tax_parts, last_plain_total = [], None
    for ln in lines:
        low = ln.lower()
        amt = last_amount(ln)
        if amt is None:
            continue
        if _starts(ln, SUBTOTAL_LABELS) and inv.subtotal is None:
            inv.subtotal = amt
        elif TAX_LINE.match(ln):
            tax_parts.append(amt)
        elif _starts(ln, TOTAL_LABELS):
            inv.total = amt
        elif re.match(r"^total\b", low) and not any(w in low for w in NOT_TOTAL):
            last_plain_total = amt
    if inv.total is None:
        inv.total = last_plain_total
    if tax_parts:
        inv.tax = round(sum(tax_parts), 2)
    elif re.search(r"not (applicable|registered)", text, re.I):
        inv.tax = 0.0
    if inv.subtotal is None and inv.tax == 0.0:
        # Unregistered sellers often print one line amount and a total.
        line_amounts = [a for ln in lines if not re.match(r"^(total|invoice total)", ln.lower()) for a in amounts(ln)]
        inv.subtotal = line_amounts[0] if len(line_amounts) == 1 else inv.total
    return check(inv)


def check(inv: Invoice) -> Invoice:
    """Flag what a person must look at before paying."""
    inv.problems, inv.review = [], []
    if None not in (inv.subtotal, inv.tax, inv.total) and abs(inv.subtotal + inv.tax - inv.total) > 1:
        inv.problems.append("total_mismatch")
        inv.review.append(f"Subtotal {inv.subtotal:,.2f} + tax {inv.tax:,.2f} is not the total {inv.total:,.2f}")
    if inv.gstin and not gstin_ok(inv.gstin):
        inv.problems.append("bad_gstin")
        inv.review.append(f"GST number {inv.gstin} does not have the 15-character GSTIN shape")
    for name in ["vendor", "invoice_no", "date", "subtotal", "tax", "total"]:
        if getattr(inv, name) is None:
            inv.review.append(f"Could not find {name}")
    return inv


def baseline(text: str) -> Invoice:
    """A quick template-style regex extractor: first match wins, no checks."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    inv = Invoice(vendor=lines[0] if lines else None)
    m = re.search(r"Invoice No[:.]?\s*(\S+)", text)
    inv.invoice_no = m[1] if m else None
    m = re.search(r"\b(\d{2})/(\d{2})/(\d{4})\b", text)
    inv.date = f"{m[3]}-{m[2]}-{m[1]}" if m else None
    m = re.search(r"GSTIN\W*(\w{15})", text)
    inv.gstin = m[1] if m else None
    for ln in lines:
        low = ln.lower()
        if inv.subtotal is None and "sub" in low:
            inv.subtotal = last_amount(ln)
        if inv.tax is None and "gst" in low and "%" in low:
            inv.tax = last_amount(ln)
        if "total" in low and last_amount(ln) is not None:
            inv.total = last_amount(ln)
    return inv
