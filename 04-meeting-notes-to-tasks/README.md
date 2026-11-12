# Meeting Notes to Tasks

Paste a meeting transcript. Get back every task with an owner and a due date, as JSON for your task tool and as a short markdown summary for the team. Anything unclear is flagged for a person to check.

## Why this matters for a business

After a meeting, someone has to write down who agreed to do what, and by when. It gets skipped, or it is done from memory. Then "I thought Ravi was doing that" happens a week later.

Most quick tools just grab every line with "will" or "should" in it and give it to the person who spoke. That gets the owner wrong when a manager says "Rahul, can you ...", misses the person who said "I'll take that", and never works out what "by Friday" means as a date.

## Result: 69% of tasks fully right on unseen meetings, vs 6% for the keyword method

Demo data: 7 made-up meeting transcripts from small businesses (store, clinic, SaaS, cafe, realty, grocery, tutoring). I labeled every real task by hand (turn, owner, due date) and committed the labels **before** writing the extractor. The rules were built while looking at the 4 dev meetings only. The 3 holdout meetings were not looked at until the end.

A task is **fully right** only if it is found, the owner is right and the due date is right.

| Split | Method | Real tasks | Precision | Recall | Owner right | Due date right | Fully right |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev (4 meetings) | Keyword baseline | 22 | 70% | 95% | 48% | 19% | 2/22 (9%) |
| dev (4 meetings) | This tool, offline rules | 22 | 100% | 100% | 100% | 100% | 22/22 (100%) |
| holdout (3 meetings) | Keyword baseline | 16 | 81% | 81% | 54% | 23% | 1/16 (6%) |
| holdout (3 meetings) | This tool, offline rules | 16 | 94% | 94% | 93% | 73% | 11/16 (69%) |

- **Precision**: of the tasks it pulled out, how many were real tasks.
- **Recall**: of the real tasks, how many it found.
- **Owner right / Due date right**: checked on the tasks it found.
- The keyword baseline marks any line with "will", "should", "can you", "please" and so on as a task, gives it to the speaker, and has no dates.

**Read the dev row with care.** 100% on dev only means the rules fit the meetings they were built on. The holdout row (69%) is the honest number. The gap between them is the main lesson of this project: always keep some test data you never tune on.

### What went wrong on the holdout meetings

All 6 errors, from `eval/results.md`:

1. "Let's have Elena post the sale on Friday": missed. No rule for "let's have NAME do X".
2. "Can someone check the coupon code?" then "I'll look into it today": the reply was read as a new task, so the request had no owner. Counted twice as an error.
3. "Prepare the site visit schedule **for** next week" and "book the room **for** next Tuesday": the rules made these the due dates. They are the dates of the event, not the deadline.
4. "Right after this meeting": not understood as today.

The check step flagged 3 of the 16 holdout tasks for a human (no owner or no date). 2 of those 3 were real errors. The date mistakes in point 3 were not flagged, which is the riskiest kind of error here.

## When this does not work

The offline rules are tuned on 4 short, clean, made-up meetings. Real calls have people talking over each other, transcription errors and tasks spread across many lines. For real meetings, use LLM mode and still run the eval on 20 or more of your own labeled meetings first. LLM mode was not scored here because this run had no API key.

## How it works

```
transcript.txt (Date, Attendees, "Name: text" lines)
   -> extract tasks (offline rules, or any OpenAI-compatible LLM)
   -> check: owner must be in the meeting, due date not before the meeting,
      flag tasks with no owner or no date
   -> tasks.json + summary.md (table, tasks by person, "needs a human check" list)
```

The offline rules, in plain words:

1. "Rahul, can you ...", "Neha to ...", "Karan will ..." -> owner is that person.
2. "I'll ...", "let me ...", "I'm going to ..." -> owner is the speaker.
3. "Can you ...", "someone should ...", "we need to ..." -> owner unknown for now.
4. "Sure." or "I'll take that" right after a request -> fills in the owner and date. Not a new task.
5. "Scratch that" removes the last task. "Not now" right after a suggestion removes it.
6. Questions and past actions ("already sent", "paid it yesterday") are skipped.

Date rules are listed at the top of `meetbot/dates.py` (for example "next week" means Friday of next week).

- `meetbot/transcript.py`: reads the transcript
- `meetbot/dates.py`: "by Friday", "end of month", "the 20th" -> a real date
- `meetbot/rules.py`: offline extractor and the keyword baseline
- `meetbot/llm.py`: LLM extractor with JSON output
- `meetbot/agent.py`: the check step and the markdown summary
- `eval/run_eval.py`: the table above

## Run it

```bash
pip install -r requirements.txt

# Offline, no API key
python -m meetbot data/transcripts/holdout-02-grocery-ops.txt --json tasks.json --md summary.md

# The benchmark
python eval/run_eval.py
```

Example output for one holdout meeting, errors included: [examples/holdout-02-summary.md](examples/holdout-02-summary.md) and [examples/holdout-02-tasks.json](examples/holdout-02-tasks.json).

With an API key (any OpenAI-compatible provider):

```bash
export LLM_API_KEY=your_key
export LLM_MODEL=gpt-4o-mini            # or any model your provider offers
export LLM_BASE_URL=https://...         # only for non-OpenAI providers
python -m meetbot your_meeting.txt --md summary.md
python eval/run_eval.py --modes baseline,rules,llm
```

## Use it on your own meetings

Most meeting tools (Zoom, Meet, Teams, Otter) can export a transcript. Turn it into this format:

```
Meeting: Weekly sync
Date: 2026-11-09
Attendees: Priya, Rahul, Meera

Priya: Rahul, can you pull the return reasons by Wednesday?
Rahul: Sure.
```

To score it, add a line to `eval/gold.jsonl` with the turn number, owner and due date of each real task.

## Tests

```bash
pytest -q
```

## Demo data

All transcripts, people and companies in `data/transcripts/` are made up for this demo. Any match with a real business is by chance.
