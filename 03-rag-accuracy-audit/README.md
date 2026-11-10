# RAG Accuracy Audit Tool

Give it your chunks, a list of test questions and your retriever. It tells you how often the right passage comes first, which questions fail, and which chunks are causing the failures. Then it can apply safe fixes and you measure again.

## Why this matters for a business

When a support chatbot gives a wrong answer, people usually blame the model. Most of the time the model never saw the right text. The search step picked an old policy page, a heading with no content, or a footer that repeats on every page.

This tool finds those chunks for you, with numbers, before your customers find them.

## Result: fixing the chunks took Hit@1 from 30% to 70%

Demo: a made-up help center for an online home store (6 documents, 30 test questions). The documents were split the quick way most pipelines do it: on blank lines. Retriever: BM25, top 5. Nothing else changed between rows.

| Setup | Chunks | Hit@1 | Hit@3 | MRR |
| --- | --- | --- | --- | --- |
| Raw chunks (split on blank lines) | 68 | 30% | 70% | 0.50 |
| Only drop the stale document | 58 | 40% | 73% | 0.57 |
| Only remove duplicate footers | 63 | 23% | 70% | 0.45 |
| Only merge heading chunks | 34 | 63% | 73% | 0.69 |
| All three fixes | 25 | 70% | 80% | 0.74 |
| All three fixes + simple stemming | 25 | 77% | 90% | 0.83 |

- **Hit@1**: the right passage is the first result.
- **Hit@3**: the right passage is in the top 3.
- **MRR**: average of 1 / rank of the right passage. 1.00 means it is always first.
- A passage counts as right if it contains the expected answer text, so the score still works after the chunks change.

What the audit found on the raw chunks:

1. **21 of 30 questions missed at rank 1. 17 of those 21 were caused by chunks the audit flagged.**
2. **Stale document (6 misses).** An old 2023 copy of the returns policy was still indexed. It says 14 days to return. The current policy says 30. For "How many days do I have to send something back?" the old page won. That is a wrong answer a customer would act on.
3. **Heading-only chunks (11 more misses).** Lines like `## Cash on delivery limit` became their own chunk. They match the question words perfectly and are very short, so BM25 ranks them first. They hold no answer.
4. **Footer copies (6 chunks).** The same "Need more help?" text in every document.
5. **The other 4 misses** were word mismatch (sofa vs Sofas, track vs Tracking). No chunk fix helps there. Simple stemming fixed some of them. Embeddings or hybrid search would be the next step.

One surprise: removing the duplicate footers on its own made things worse (30% to 23%). The footers were adding common words like "account" and "warranty" to many chunks. Without them, those words became rarer, so the empty heading chunks scored even higher. Fixes interact. That is why you run the audit after every change, not just once.

Full reports: [eval/report_before.md](eval/report_before.md) and [eval/report_after.md](eval/report_after.md).

## When this does not work

The audit is only as good as your question set. 30 questions on 6 short documents is a small demo. On your own data, write at least 50 real questions from support tickets or search logs. The checks are simple rules too, so a near-duplicate with very different wording will not be caught.

## How it works

```
chunks.jsonl + questions.jsonl + retriever
   -> run every question, find the rank of the passage that contains the answer
   -> Hit@1, Hit@3, Hit@5, MRR
   -> flag chunks: tiny or heading-only, duplicate, boilerplate, conflict (same text, different numbers),
      stale (older copy of a newer document)
   -> list the chunks that rank first for questions they cannot answer
   -> fix: drop stale docs, keep one copy of duplicates, merge headings into the next chunk
```

- `ragaudit/chunks.py`: chunk format and a simple paragraph chunker for the demo
- `ragaudit/retrievers.py`: BM25 (with optional stemming), and a loader for your own retriever
- `ragaudit/audit.py`: metrics and bad chunk checks
- `ragaudit/fix.py`: the safe fixes. Conflicts are only reported, because a person has to decide which number is right
- `ragaudit/llm.py`: optional one-line explanation per miss from any OpenAI-compatible API
- `eval/run_eval.py`: the before/after table above

## Run it

```bash
pip install -r requirements.txt

# 1. The before/after benchmark (no API key needed)
python eval/run_eval.py

# 2. The tool, step by step
python -m ragaudit chunk data/docs data/chunks.jsonl
python -m ragaudit audit --chunks data/chunks.jsonl --questions eval/questions.jsonl --report report.md
python -m ragaudit fix data/chunks.jsonl data/chunks_fixed.jsonl
python -m ragaudit audit --chunks data/chunks_fixed.jsonl --questions eval/questions.jsonl --retriever bm25-stem
```

With an API key, `--explain` adds a short reason for each miss:

```bash
export LLM_API_KEY=your_key
export LLM_MODEL=gpt-4o-mini            # or any model your provider offers
export LLM_BASE_URL=https://...         # only for non-OpenAI providers
python -m ragaudit audit --chunks data/chunks.jsonl --questions eval/questions.jsonl --explain
```

## Use it on your own RAG system

1. Export your chunks as JSON lines: `{"id": "...", "doc": "...", "text": "...", "updated": "2025-06-01"}`. `updated` is optional but needed for the stale check.
2. Write questions as JSON lines: `{"question": "...", "answer": "a short phrase the right chunk must contain"}`.
3. To test your own retriever (vector DB, hybrid, reranker), write a small module:

```python
# my_search.py
def build(chunks):
    return MySearch(chunks)   # any object with .search(query, k) -> list of chunk ids, best first
```

and run `python -m ragaudit audit --chunks ... --questions ... --retriever my_search:build`.

## Tests

```bash
pytest -q
```

## Demo data

Everything in `data/docs/` is made up. "Brightleaf Home" is a fictional store. The questions in `eval/questions.jsonl` are written for this demo only.
