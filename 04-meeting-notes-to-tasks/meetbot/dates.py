"""Turn phrases like "by Friday" or "end of month" into a real date.

Rules (written down so a person can check them):
- today, tonight, EOD             -> meeting day
- tomorrow                        -> meeting day + 1
- in N days                       -> meeting day + N
- this week, end of week          -> Friday of the meeting week
- next week                       -> Friday of the next week
- next <weekday>                  -> that weekday in the next week
- <weekday>                       -> the next one after the meeting day
- end of month                    -> last day of the month
- Nov 25, 25 November, December 1 -> that date (next year if already past)
- the 20th                        -> the 20th of this month (next month if past)
Returns None when there is no date in the text.
"""

import calendar
import re
from datetime import date, timedelta

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "ten": 10}
MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))


def _next_weekday(d: date, wd: int) -> date:
    days = (wd - d.weekday()) % 7 or 7
    return d + timedelta(days=days)


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _safe(y: int, m: int, day: int) -> date | None:
    try:
        return date(y, m, day)
    except ValueError:
        return None


def resolve_due(text: str, d: date) -> date | None:
    t = text.lower()
    if re.search(r"\b(today|tonight|eod|end of (the )?day)\b", t):
        return d
    if "tomorrow" in t:
        return d + timedelta(days=1)
    m = re.search(r"\bin (\d+|" + "|".join(NUMBERS) + r") days?\b", t)
    if m:
        n = m.group(1)
        return d + timedelta(days=int(n) if n.isdigit() else NUMBERS[n])
    if re.search(r"\bend of (the )?month\b", t):
        return date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
    if re.search(r"\b(end of (the )?week|this week)\b", t):
        return max(d, _monday(d) + timedelta(days=4))
    m = re.search(r"\bnext (" + "|".join(WEEKDAYS) + r")\b", t)
    if m:
        return _monday(d) + timedelta(days=7 + WEEKDAYS.index(m.group(1)))
    if re.search(r"\bnext week\b", t):
        return _monday(d) + timedelta(days=11)
    m = re.search(r"\b(" + MONTH_RE + r")\.? (\d{1,2})(st|nd|rd|th)?\b", t)
    m2 = re.search(r"\b(\d{1,2})(st|nd|rd|th)? (" + MONTH_RE + r")\b", t)
    if m or m2:
        mon, day = (MONTHS[m.group(1)], int(m.group(2))) if m else (MONTHS[m2.group(3)], int(m2.group(1)))
        out = _safe(d.year, mon, day)
        if out and out < d:
            out = _safe(d.year + 1, mon, day)
        return out
    m = re.search(r"\bthe (\d{1,2})(st|nd|rd|th)\b", t)
    if m:
        day = int(m.group(1))
        out = _safe(d.year, d.month, day)
        if out is None or out < d:
            y, mo = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
            out = _safe(y, mo, day)
        return out
    m = re.search(r"\b(" + "|".join(WEEKDAYS) + r")\b", t)
    if m:
        return _next_weekday(d, WEEKDAYS.index(m.group(1)))
    return None
