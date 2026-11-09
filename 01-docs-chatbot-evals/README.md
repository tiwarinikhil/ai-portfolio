# Docs Chatbot with Evals

A chatbot that answers questions from your own documents and shows the source for every answer. It also comes with a small test set, so you can measure whether a change makes answers better or worse.

## Why this matters for a business

Most RAG chatbots fail quietly. They give a confident answer, but the part of the document that holds the real answer was never found. This project shows a simple fix and proves it with numbers.

## Result: how you split documents changes everything

Same document, same 24 questions, same retriever (BM25). Only the chunking changes.

| Chunking | Chunks | Hit@1 | Hit@3 | MRR |
| --- | --- | --- | --- | --- |
| Fixed 300 characters | 17 | 79% | 92% | 0.86 |
| Fixed 800 characters | 7 | 88% | 100% | 0.94 |
| Split by headings | 23 | 100% | 100% | 1.00 |

- **Hit@1**: the right passage is the first result.
- **Hit@3**: the right passage is in the top 3.
- **MRR**: average of 1 / rank of the right passage. 1.00 means it is always first.

Why heading-based wins:

1. Fixed-size chunks cut sentences in half. With 300 characters, the answer to "What happens if my manager does not approve my leave in time?" was split across two chunks, so it was never found.
2. Bigger fixed chunks find more answers, but each chunk carries a lot of unrelated text. That means more tokens per question and more room for the model to get confused.
3. Heading-based chunks keep each section whole and put the heading path at the top, like `Leave Policy > Sick leave`. That small label makes search much more accurate.

This is a small, clean demo document. Real documents are messier, which makes this gap bigger, not smaller.

## How it works

```
documents (.md / .txt)
   -> split by headings, heading path kept on each chunk
   -> retrieve: BM25 (keywords), embeddings (meaning) or hybrid (both)
   -> LLM writes a short answer using only those chunks, with [1] [2] citations
```

- `docbot/chunking.py`: fixed-size and heading-based chunking
- `docbot/retrieval.py`: BM25, embeddings and hybrid (reciprocal rank fusion)
- `docbot/llm.py`: answer with citations, works with any OpenAI-compatible API
- `docbot/api.py`: FastAPI app with a simple chat page
- `eval/run_eval.py`: compares chunking strategies on `eval/questions.jsonl`

## Run it

```bash
pip install -r requirements.txt

# 1. Run the evaluation (no API key needed)
python eval/run_eval.py

# 2. Start the chat app
uvicorn docbot.api:app --reload
# open http://127.0.0.1:8000
```

Without an API key the app runs in retrieval-only mode and shows the best matching passage. To get written answers, set:

```bash
export LLM_API_KEY=your_key
export LLM_MODEL=gpt-4o-mini            # or any model your provider offers
export LLM_BASE_URL=https://...         # only for non-OpenAI providers
export USE_EMBEDDINGS=1                 # optional: hybrid search
```

To test embeddings and hybrid search too: `python eval/run_eval.py --embeddings`

## Use your own documents

Put `.md` or `.txt` files in `data/` and restart the app. For PDFs, convert them to markdown first so the headings are kept.

## Tests

```bash
pytest -q
```

## Demo data

`data/northwind_handbook.md` is a made-up employee handbook for a fictional company. It is only demo data.
