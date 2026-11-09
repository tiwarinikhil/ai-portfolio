"""Answer a question from retrieved chunks, with numbered sources.

Works with any OpenAI-compatible chat API. Set:
  LLM_API_KEY   your key
  LLM_BASE_URL  optional, for Gemini, Groq, OpenRouter or a local server
  LLM_MODEL     optional, default gpt-4o-mini
Without a key, it returns the best matching passages instead of a written answer.
"""

import os

from .chunking import Chunk

SYSTEM_PROMPT = (
    "You answer questions using only the numbered sources given. "
    "Cite sources like [1] or [2] after each fact. "
    "If the sources do not contain the answer, say you could not find it in the documents. "
    "Keep answers short and clear."
)


def build_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))


def answer(question: str, chunks: list[Chunk]) -> dict:
    sources = [{"n": i + 1, "heading": c.heading, "text": c.text} for i, c in enumerate(chunks)]
    key = os.getenv("LLM_API_KEY")
    if not key:
        top = chunks[0].text if chunks else "No matching passage found."
        return {
            "answer": f"(No LLM key set, showing the best matching passage.)\n\n{top}",
            "sources": sources,
            "mode": "retrieval-only",
        }

    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL"))
    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Sources:\n{build_context(chunks)}\n\nQuestion: {question}"},
        ],
    )
    return {"answer": resp.choices[0].message.content, "sources": sources, "mode": "llm"}
