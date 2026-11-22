"""LLM extraction with any OpenAI-compatible API. Used only when LLM_API_KEY is set."""

import json
import os

from .extract import Invoice, check

PROMPT = (
    "Extract these fields from the invoice text and reply with JSON only: "
    "vendor (the seller, not the buyer), invoice_no (not a PO number), date (invoice date as YYYY-MM-DD, "
    "day first for dates like 03/11/2026, never the due date), gstin (the seller's GST number exactly as "
    "printed, or null), subtotal (before tax), tax (all GST added together), total (as printed, before any "
    "advance is taken off). Use numbers for amounts. Use null for anything not on the invoice."
)


def extract_llm(text: str) -> Invoice:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.getenv("LLM_BASE_URL"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": text}],
    )
    data = json.loads(resp.choices[0].message.content)
    fields = {k: data.get(k) for k in ["vendor", "invoice_no", "date", "gstin", "subtotal", "tax", "total"]}
    # The same math and GSTIN checks run on the LLM's answer.
    return check(Invoice(**fields))
