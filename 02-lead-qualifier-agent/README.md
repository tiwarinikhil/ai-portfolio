# Lead Qualifier Agent

An agent that reads new leads from a CSV or a form, scores each one from 0 to 100, explains the score, and drafts a first reply. A human approves, edits or rejects every draft. Nothing is sent without a person saying yes.

## Why this matters for a business

Small teams get leads from many places and reply in the order they arrive. The best lead of the week often waits two days behind people who will never buy. The usual shortcut is to sort by budget, but budget alone misses founders who did not write a number and promotes students who did.

## Result: 4 signals beat budget alone

40 made-up leads, each with a hand-written expected tier (hot, warm or cold). Leads L01 to L24 were used to write the rules. Leads L25 to L40 are a holdout set, scored once after the rules were frozen.

| Leads | Method | Accuracy | Hot precision | Hot recall | Hot leads marked cold |
| --- | --- | --- | --- | --- | --- |
| Holdout (16) | Budget only | 69% | 67% | 67% | 1 |
| Holdout (16) | Lead agent | **88%** | **100%** | 83% | **0** |
| All 40 | Budget only | 68% | 73% | 73% | 2 |
| All 40 | Lead agent | **92%** | **100%** | **93%** | **0** |

- **Hot precision**: of the leads marked hot, how many really are hot. 100% means you never rush to call a weak lead.
- **Hot recall**: of the real hot leads, how many were found.
- **Hot leads marked cold**: real buyers who would get no reply at all. This is the most costly mistake.

Full numbers, including the tuning set, are in `eval/results.md`.

What budget alone gets wrong (from the holdout set):

1. L28, a CEO who needs a fact check step and "can move fast", gave no budget. Budget-only marks this lead cold, so it gets no reply.
2. L33 and L39 have budgets but start next quarter. Budget-only calls them hot.
3. L36 is a coordinator who has to ask a manager. Budget-only cannot see that.

Where the agent is still wrong: L28 is hot but scores warm, and L31 (a consultant with a vague demo request) is warm but scores cold. Rules are only as good as the words they look for.

## How it works

```
lead (CSV row or form)
   -> score: budget + authority + need + timeline, with reasons
   -> cold?  yes -> skip, no reply drafted
   -> draft a first reply (LLM, or a template with no API key)
   -> human review: approve, edit or reject   <- the graph pauses here
   -> approved replies saved to outbox/approved.jsonl
```

It is built as a LangGraph graph with a checkpoint, so the agent can stop at the review step and resume later with the human's answer.

- `leadbot/scoring.py`: the 4 signals, the reasons, and the budget-only baseline
- `leadbot/graph.py`: the LangGraph flow with the human review pause
- `leadbot/llm.py`: reply drafts with any OpenAI-compatible API, or a template offline
- `run.py`: score a CSV and review drafts in the terminal
- `eval/run_eval.py`: compares the agent with budget-only on `data/leads.csv`

## Run it

```bash
pip install -r requirements.txt

# 1. Run the evaluation (no API key needed)
python eval/run_eval.py

# 2. Score leads and review each draft
python run.py data/leads.csv

# Or skip the review and save every draft as pending
python run.py data/leads.csv --no-input
```

Without an API key, replies come from a short template. To get written replies from an LLM, set:

```bash
export LLM_API_KEY=your_key
export LLM_MODEL=gpt-4o-mini            # or any model your provider offers
export LLM_BASE_URL=https://...         # only for non-OpenAI providers
```

## Use your own leads

Export your leads to a CSV with the columns `id, name, company, role, company_size, budget_usd, timeline, message`. The `expected_tier` column is only needed for the evaluation. Then change the word lists in `leadbot/scoring.py` to match your business.

## When this does not work

If most of your leads write one line with no role or budget, the rules have little to go on. In that case, add a short form with 3 fixed questions (role, budget range, start date) before scoring.

## Tests

```bash
pytest -q
```

## Demo data

`data/leads.csv` holds 40 made-up leads for fictional people and companies. It is only demo data. The expected tiers were written by hand.
