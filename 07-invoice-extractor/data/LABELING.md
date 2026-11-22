# How the labels were made

20 made-up invoices, typed the way OCR or a PDF-to-text tool gives them back. Every field was filled in by hand and committed before any extraction code was written.

Fields:

- **vendor**: the business that sent the invoice (not the buyer). A field is right if the extracted name starts with the labeled name, ignoring case.
- **invoice_no**: the invoice or bill number as printed (not a PO number).
- **date**: the invoice date, as YYYY-MM-DD. Dates like 03/11/2026 are day first (Indian style). Not the due date.
- **gstin**: the seller's GST number as printed, or null if the seller is not GST registered. Not the buyer's.
- **subtotal**: amount before tax.
- **tax**: all GST added together (CGST + SGST, or IGST).
- **total**: the invoice total as printed, before any advance is taken off. Rounding is part of the total.

Problems a person should check before paying:

- **total_mismatch**: subtotal + tax does not equal the printed total (more than 1 rupee off).
- **bad_gstin**: the GST number does not have the 15-character GSTIN shape.

Split: INV01 to INV10 are **dev** (rules may be built while reading them). INV11 to INV20 are **holdout** (not read while building rules, scored once at the end).
