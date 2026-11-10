"""Write the first reply to a lead.

Works with any OpenAI-compatible chat API. Set:
  LLM_API_KEY   your key
  LLM_BASE_URL  optional, for Gemini, Groq, OpenRouter or a local server
  LLM_MODEL     optional, default gpt-4o-mini
Without a key, it fills a short template instead, so the whole flow still runs offline.
"""

import os

SYSTEM_PROMPT = (
    "You write the first reply to a sales lead for a freelance AI engineer. "
    "Use simple English, 60 to 110 words, no hype, no emojis. "
    "Mention their problem in their own words, suggest one concrete next step, "
    "and ask at most one question. Never promise prices or dates."
)

NEXT_STEP = {
    "hot": "Could we do a 20 minute call this week? I can share a short plan and a rough timeline after it.",
    "warm": "If it helps, I can send a one page plan you can share with your team before we talk.",
    "cold": "If this becomes a real project later, just reply to this email and I will pick it up.",
}


def _first_name(lead: dict) -> str:
    return (lead.get("name") or "there").split()[0]


def template_reply(lead: dict, tier: str) -> str:
    problem = (lead.get("message") or "").strip().rstrip(".")
    company = lead.get("company") or "your team"
    return (
        f"Hi {_first_name(lead)},\n\n"
        f"Thanks for reaching out. You said: \"{problem}.\" "
        f"I build RAG chatbots, LLM agents and automations for teams like {company}, "
        f"and this sounds like something I can help with.\n\n"
        f"{NEXT_STEP[tier]}\n\n"
        f"Nikhil"
    )


def draft_reply(lead: dict, tier: str, reasons: list[str]) -> tuple[str, str]:
    """Return (reply text, mode). Mode is 'llm' or 'template'."""
    key = os.getenv("LLM_API_KEY")
    if not key:
        return template_reply(lead, tier), "template"

    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL"))
    lead_text = "\n".join(f"{k}: {v}" for k, v in lead.items() if k != "expected_tier" and v)
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Lead:\n{lead_text}\n\nTier: {tier}\nWhy: {'; '.join(reasons)}\n"
                f"Next step to suggest: {NEXT_STEP[tier]}\nSign off as Nikhil.",
            },
        ],
    )
    return resp.choices[0].message.content.strip(), "llm"
