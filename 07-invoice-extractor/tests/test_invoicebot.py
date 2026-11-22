import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from invoicebot import baseline, extract  # noqa: E402
from invoicebot.parse import amounts, find_date, gstin_ok  # noqa: E402


def load(iid):
    return (ROOT / "data" / "invoices" / f"{iid}.txt").read_text(encoding="utf-8")


def test_indian_amounts_and_dates():
    assert amounts("Total Amount    1,71,100.00") == [171100.0]
    assert find_date("Date: 03/11/2026") == "2026-11-03"
    assert find_date("Invoice Date: 12-Nov-2026") == "2026-11-12"
    assert find_date("Invoice Date: 10th Nov 2026") == "2026-11-10"


def test_gstin_shape():
    assert gstin_ok("27AAFCS1234K1Z3")
    assert not gstin_ok("29AAGFG9753R1Z")  # 14 characters


def test_skips_buyer_gstin_and_due_date():
    inv = extract(load("INV02"))
    assert inv.vendor == "Kaveri Packaging Pvt Ltd"
    assert inv.gstin == "33AADCK4321M1Z2"
    assert inv.date == "2026-11-12"
    assert inv.tax == 3330.0


def test_flags_total_that_does_not_add_up():
    inv = extract(load("INV04"))
    assert inv.problems == ["total_mismatch"]
    assert inv.review


def test_advance_is_not_the_total():
    assert extract(load("INV08")).total == 11328.0


def test_tax_adds_cgst_and_sgst():
    assert extract(load("INV01")).tax == 612.0
    assert baseline(load("INV01")).tax == 306.0  # the quick regex stops at the first GST line


def test_unregistered_seller_has_no_tax():
    inv = extract(load("INV06"))
    assert inv.gstin is None and inv.tax == 0.0 and inv.total == 25000.0
    assert not inv.review


def test_missing_field_goes_to_review():
    inv = extract("Some Shop\nInvoice No: A-1\nDate: 01/11/2026\nWidgets   100.00\n")
    assert "Could not find total" in inv.review
