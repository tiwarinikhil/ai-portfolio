"""Plain-words summary for a recruiter. Uses an LLM only when LLM_API_KEY is set."""

import os

from .match import Match


def summary(m: Match, job_title: str) -> str:
    head = {"strong": "Strong fit", "maybe": "Maybe, worth a closer look", "no": "Not a fit"}[m.label]
    lines = [f"{head} for {job_title}."] + [f"- {r}" for r in m.reasons()]
    text = "\n".join(lines)
    if not os.getenv("LLM_API_KEY"):
        return text
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.getenv("LLM_BASE_URL"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        messages=[
            {"role": "system", "content": (
                "Rewrite this resume check as 2 or 3 short sentences for a recruiter. "
                "Keep the verdict as given. Use only the facts listed. "
                "Never mention or guess name, gender, age, college or location."
            )},
            {"role": "user", "content": text},
        ],
    )
    return resp.choices[0].message.content.strip()
