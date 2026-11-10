"""Optional: ask an LLM why each miss happened.

Works with any OpenAI-compatible chat API. Set:
  LLM_API_KEY   your key
  LLM_BASE_URL  optional, for Gemini, Groq, OpenRouter or a local server
  LLM_MODEL     optional, default gpt-4o-mini
Without a key, the report uses the rule-based issue labels only.
"""

import os

PROMPT = (
    "A search system returned the wrong passage for a question. In one short sentence, say why "
    "the wrong passage probably ranked first and what to change in the documents or chunks."
)


def llm_enabled() -> bool:
    return bool(os.getenv("LLM_API_KEY"))


def explain_miss(question: str, expected: str, wrong_text: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": f"Question: {question}\nThe right passage contains: {expected}\n"
                                        f"Passage that ranked first:\n{wrong_text}"},
        ],
    )
    return resp.choices[0].message.content.strip()
