"""Small helpers: money amounts, dates and GST numbers as they appear on Indian invoices."""

import re
from datetime import date

AMOUNT = re.compile(r"-?\d{1,3}(?:,\d{2,3})*(?:\.\d{2})|-?\d+\.\d{2}")
GSTIN_LIKE = re.compile(r"\b\d{2}[A-Z0-9]{11,13}\b")
# 2 digit state code, 10 character PAN, entity number, the letter Z, check character.
GSTIN_SHAPE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

# Date formats seen in the dev invoices only.
DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"), "ymd"),                       # 2026-10-28
    (re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](\d{4})\b"), "dmy"),             # 03/11/2026, 05.11.2026
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?[ -]([A-Za-z]{3,9})[ -](\d{4})\b"), "d_mon_y"),  # 12-Nov-2026, 9 November 2026
]


def amounts(line: str) -> list[float]:
    return [float(a.replace(",", "")) for a in AMOUNT.findall(line)]


def last_amount(line: str) -> float | None:
    found = amounts(line)
    return found[-1] if found else None


def find_date(line: str) -> str | None:
    for pattern, kind in DATE_PATTERNS:
        m = pattern.search(line)
        if not m:
            continue
        try:
            if kind == "ymd":
                d = date(int(m[1]), int(m[2]), int(m[3]))
            elif kind == "dmy":
                d = date(int(m[3]), int(m[2]), int(m[1]))
            else:
                month = MONTHS.get(m[2][:3].lower())
                if not month:
                    continue
                d = date(int(m[3]), month, int(m[1]))
        except ValueError:
            continue
        return d.isoformat()
    return None


def gstin_ok(value: str | None) -> bool:
    return bool(value) and bool(GSTIN_SHAPE.match(value))
