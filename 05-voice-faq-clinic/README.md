# Voice FAQ Agent for a Clinic

A phone assistant for a small clinic. It hears the caller (speech to text), answers simple questions from the clinic's FAQ, reads the answer back (text to speech), and knows when it must not answer: emergencies go to 108 and to staff right away, and medical questions go to a person.

It runs fully offline in text-only mode. With an API key it adds real speech in and out.

## Why this matters for a business

A clinic front desk spends hours a day on the same calls: timings, fees, parking, reports. A bot can take those. But a clinic bot that answers everything is dangerous. If someone says "my husband has chest pain" and the bot replies with the opening hours, that is a serious failure. So the most important number here is not how many questions it answers. It is how many wrong or unsafe answers it reads out.

## Result: 3 of 3 emergencies caught, 2 wrong answers instead of 8

Demo data: a made-up FAQ for a fictional clinic (18 entries) and 48 made-up caller transcripts, written in phone style with fillers, slips and missing punctuation. I labeled every call by hand (the right FAQ entry, "urgent" or "handoff") and committed the labels **before** writing any code. The rules were built while looking at the 28 dev calls only. The 20 holdout calls were scored at the end.

The quick FAQ bot searches the raw transcript and always reads out the top answer. That is what many simple FAQ bots do.

| Calls | Method | Right action | FAQ answered right | Emergencies caught | Wrong answers read out |
| --- | --- | --- | --- | --- | --- |
| dev (28) | Quick FAQ bot | 17/28 (61%) | 17/20 | 0/3 | 11 |
| dev (28) | Clinic agent | 27/28 (96%) | 19/20 | 3/3 | 0 |
| holdout (20) | Quick FAQ bot | 12/20 (60%) | 12/15 | 0/3 | 8 |
| holdout (20) | Clinic agent | 13/20 (65%) | 8/15 | **3/3** | **2** |

- **Right action**: answered with the right FAQ entry, or sent an emergency or a medical question to a person when it should.
- **Wrong answers read out**: the caller heard an FAQ answer that did not answer them. This includes emergencies answered with clinic info.

**Read the holdout row, not the dev row.** On unseen calls the agent is only a little better on "right action" (65% vs 60%). It answers fewer FAQ questions (8 vs 12 of 15), because when it is unsure it hands the call to the front desk. That is the trade: fewer answers, but far fewer wrong ones, and no missed emergencies.

### An honest mistake I caught

My first version scored **19/20 (95%) on the holdout**. Then I noticed why: I had written the holdout calls first, and some of the word mappings I added later ("bike" means two-wheeler parking, "lab results" means reports, "lift" means wheelchair access) came straight from those calls. The rules had seen the test.

I removed every mapping that was not needed by a dev call, and the holdout score dropped to 13/20 (65%). That lower number is the real one. The gap is the main lesson of this project: if you write rules while looking at your test set, your score is lying to you.

### What went wrong on the holdout calls

From `eval/results.md`:

1. **2 wrong answers.** "Fix an appointment with doctor Sharma" got the doctors' schedule, not how to book. "Can I talk to the doctor in Hindi" got the video call answer, not languages. The word "doctor" pulled both the wrong way.
2. **5 safe misses.** "Address", "bike", "move my booking", "lab results" and "lift" are not words the FAQ uses, so the score was too low and the call went to the front desk. Annoying, but not dangerous.
3. All 3 emergencies (stroke, heavy bleeding, collapse) and both medical questions (a child's paracetamol dose, knee surgery) were routed to a person.

## When this does not work

The safety check is a list of standard red-flag words (chest pain, breathing, unconscious, collapsed, stroke, bleeding, seizure and so on). It will miss an emergency described in words that are not on the list, and it does not understand "no chest pain". It must never be the only safety net. In a real clinic, every call should offer "press 0 for staff" at any time, and the word list should be reviewed by a doctor and tested on real call recordings.

Word matching also struggles when callers use different words from the FAQ. The fix is more FAQ questions written the way patients talk, or LLM mode, measured on your own calls.

## How it works

```
caller audio
   -> speech to text (any OpenAI-compatible audio API; skipped in text-only mode)
   -> safety check: emergency words -> "call 108" + transfer
                    medical advice or results -> hand off to a person
   -> clean the transcript: drop fillers, fix spelling slips, map caller words to FAQ words
   -> search the FAQ (BM25)
   -> confident? (score, gap to the next match, word overlap)
         yes -> short spoken answer (rewritten by an LLM if a key is set)
         no  -> hand off to the front desk
   -> text to speech
```

- `voicefaq/safety.py`: emergency and medical-advice checks, run before anything else
- `voicefaq/normalize.py`: transcript clean-up and the word mappings
- `voicefaq/faq.py`: loads `data/faq.md` and searches it
- `voicefaq/agent.py`: the full turn, the confidence rules and the quick-bot baseline
- `voicefaq/speech.py`: speech to text and text to speech
- `eval/run_eval.py`: the table above

## Run it

```bash
pip install -r requirements.txt

# Text-only, no API key
python run.py "hello um what time do you open on sunday"
python run.py "my wife collapsed in the kitchen"

# The benchmark
python eval/run_eval.py
```

With an API key (any OpenAI-compatible provider), you get voice in and out and spoken-style answers:

```bash
export LLM_API_KEY=your_key
export LLM_BASE_URL=https://...    # only for non-OpenAI providers
python run.py --audio call.wav --speak reply.mp3
```

Voice mode was not scored here because this run had no API key. The benchmark scores the text path, which is the same logic the voice path uses after speech to text.

## Use it for your own clinic

Edit `data/faq.md` (one `##` section per question, with `Q:` and `A:` lines). Then record 30 or more real questions, label them in `data/calls.jsonl`, and run the eval before you put it on a phone line.

## Tests

```bash
pytest -q
```

## Demo data

`data/faq.md` describes a fictional clinic, and `data/calls.jsonl` holds 48 made-up caller transcripts. It is only demo data. No real patients or calls were used.
