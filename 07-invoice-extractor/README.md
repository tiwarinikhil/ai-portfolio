# Invoice Data Extractor with Math Checks

Give it the text of a supplier invoice. It pulls out the seller, invoice number, date, GST number, subtotal, tax and total as JSON, then checks the numbers. If the total does not add up, the GST number has the wrong shape, or a field is missing, it says so before anyone types the invoice into the books or pays it.

It runs fully offline. With an API key it can use an LLM for the extraction, and the same checks still run on the LLM's answer.

## Why this matters for a business

A small business gets dozens of supplier invoices a month, from dozens of formats. Someone types each one into Tally, Zoho or a sheet. It is slow, and the costly mistakes are quiet ones: tax counted as only CGST and not SGST, a balance due typed in as the total, or a supplier's total that is simply wrong and gets paid anyway.

Speed is nice. What actually saves money is knowing which invoices a person must look at.

## Result: 87% of fields right on unseen invoices, both real problems caught, 1 silent error

Demo data: 20 made-up invoices from made-up Indian suppliers, typed the way OCR or a PDF-to-text tool returns them (different layouts, lakh-style amounts like 1,45,000.00, day-first dates, buyer and seller GST numbers on the same page). I filled in every field by hand, using the rules in [`data/LABELING.md`](data/LABELING.md), and committed the labels **before** writing any code. Two invoices have a total that does not add up, and two have a broken GST number. The rules were built while reading the 10 dev invoices only. The 10 holdout invoices were scored once, at the end.

The quick regex is what a first template script usually looks like: first match wins, no checks.

| Invoices | Method | Fields right | Invoices fully right | Problems caught | False alarms | Wrong and not flagged |
| --- | --- | --- | --- | --- | --- | --- |
| dev (10) | Quick regex | 43/70 (61%) | 1/10 | 0/2 | 0 | 9 |
| dev (10) | Extractor + checks | 70/70 (100%) | 10/10 | 2/2 | 0 | 0 |
| holdout (10) | Quick regex | 50/70 (71%) | 1/10 | 0/2 | 0 | 9 |
| holdout (10) | Extractor + checks | **61/70 (87%)** | 4/10 | **2/2** | 0 | **1** |

- **Fields right**: 7 fields per invoice (seller, invoice number, date, GST number, subtotal, tax, total).
- **Problems caught**: invoices where the total does not add up or the GST number is broken, and the tool flagged it.
- **Wrong and not flagged**: invoices with at least one wrong field and no warning at all. These are the dangerous ones, because nobody will look.

**Read the holdout row, not the dev row.** 100% on dev only means the rules fit the invoices they were built on. On unseen invoices it got 87% of fields right and only 4 of 10 invoices fully right. But 5 of the 6 imperfect invoices came with a "could not find" warning, so a person would check them. Only 1 was wrong without a warning. The quick regex was wrong on 9 of 10 invoices and warned about none of them.

The quick regex's most common mistake: it took the first GST line as the tax, so on CGST + SGST invoices it counted only half the tax (right on 3 of 10 holdout invoices).

### What went wrong on the holdout invoices

All mistakes, from `eval/results.md`:

1. **New label words**: "Invoice Ref", "Invoice dt", "Taxable Amt", "Invoice Value", "Total (before GST)", "Amount Due" and "Total Tax" were not in the label lists, which came from the dev invoices. Those fields came back empty and were flagged for a person.
2. **New date shapes**: "16-11-2026" and "Nov 17, 2026" were not read. Also flagged.
3. **"Invoice Ref: BSM-7781"** gave the invoice number "Ref". Wrong, but the same invoice had other missing fields, so it was still flagged.
4. **"Seller: Pinnacle Furniture Works"** kept the word "Seller:" in the name. This is the one silent error.

I did not add these words after seeing the holdout, because then the holdout score would mean nothing. The right fix is to add them, then test on a new set of invoices.

## When this does not work

- **Scanned images.** It reads text. A photo or scanned PDF needs OCR first, and OCR mistakes in numbers will flow through. The math check catches some of those, not all.
- **New layouts.** Label words differ between suppliers, as the holdout shows. Expect to add a few words for each new supplier, or use LLM mode.
- **The checks are basic.** The GST number check looks at its shape, not whether it is a real registered number (that needs the GST portal). The math check looks at the totals, not each line item.

## How it works

```
invoice text
   -> offline rules (or any OpenAI-compatible LLM if LLM_API_KEY is set)
        seller:   "From:" line, else the first line that is not a heading
        number:   "Invoice No", "Invoice #", "Bill No", ... (not a PO number)
        date:     the invoice date, never the due date, day first
        GSTIN:    the seller's, never the buyer's
        amounts:  subtotal, every CGST/SGST/IGST line added up, the total
                  (not the balance after an advance)
   -> checks: subtotal + tax = total (within 1 rupee), GSTIN shape, missing fields
   -> JSON + "Check before paying" list
```

- `invoicebot/parse.py`: amounts like 1,45,000.00, dates, GSTIN shape
- `invoicebot/extract.py`: the offline extractor, the checks, and the quick regex baseline
- `invoicebot/llm.py`: LLM extraction with JSON output, followed by the same checks
- `eval/run_eval.py`: the table above

## Run it

```bash
pip install -r requirements.txt

# Offline, no API key
python run.py data/invoices/INV17.txt          # a total that does not add up
python run.py data/invoices/INV02.txt --json out.json

# The benchmark
python eval/run_eval.py
```

With an API key (any OpenAI-compatible provider):

```bash
export LLM_API_KEY=your_key
export LLM_BASE_URL=https://...    # only for non-OpenAI providers
python run.py my_invoice.txt
```

LLM mode was not scored here because this run had no API key. Score it on your own invoices with `eval/run_eval.py` before trusting it.

## Use it for your own invoices

Save 30 or more of your real supplier invoices as text, fill in the fields in `data/labels.jsonl` the same way, keep a third aside, and run the eval. Add your suppliers' label words to the lists at the top of `invoicebot/extract.py` using only the other two thirds.

## Tests

```bash
pytest -q
```

## Demo data

All invoices, suppliers and GST numbers are made up. No real business data was used.
