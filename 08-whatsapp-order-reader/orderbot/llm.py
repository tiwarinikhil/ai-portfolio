"""LLM reading with any OpenAI-compatible API. Used only when LLM_API_KEY is set."""

import json
import os

from .reader import Order

PROMPT = (
    "You read WhatsApp grocery orders (Hindi and English mixed). Catalog, as sku: unit: {catalog}. "
    "Reply with JSON only: {{\"items\": {{sku: quantity in the catalog unit or null if not given}}, "
    "\"unknown\": [things asked for that are not in the catalog]}}. "
    "Convert grams to kg and egg counts to dozens. Never invent items."
)


def read_order_llm(text: str, catalog: dict) -> Order:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.getenv("LLM_BASE_URL"))
    cat = ", ".join(f"{s}: {r['unit']}" for s, r in catalog.items())
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": PROMPT.format(catalog=cat)}, {"role": "user", "content": text}],
    )
    data = json.loads(resp.choices[0].message.content)
    items = {k: v for k, v in data.get("items", {}).items() if k in catalog}  # drop anything not sold
    return Order(items=items, unknown=list(data.get("unknown", [])))
