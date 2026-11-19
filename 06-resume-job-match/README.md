# Resume to Job Match Scorer

Give it a job post and a pile of resumes. For each resume it says **strong**, **maybe** or **no**, and shows why: which must-have skills the person has used at work, which are only in their skills list, which are missing, and whether they have enough years.

It runs fully offline. With an API key it also writes the reasons as two or three plain sentences for a recruiter.

## Why this matters for a business

A small company posts one job and gets 200 resumes. Most first filters are keyword filters: does the resume contain "PostgreSQL"? That is easy to fool. A tester who pastes every buzzword into the skills list looks perfect. A developer who writes "no hands-on PostgreSQL yet" also passes, because the word is there.

What a hiring manager really wants from a first filter is a shortlist they can trust, plus a reason for every decision, so nobody gets rejected by a black box.

## Result: no weak resumes on the shortlist, but it misses strong ones that use other words

Demo data: 3 made-up job posts (backend developer, data analyst, support team lead) and 36 made-up resumes, 12 per job. I labeled every resume by hand using the rules in [`data/LABELING.md`](data/LABELING.md) and committed the labels **before** writing any code. The rules were built while reading the 21 dev resumes only. The 15 holdout resumes were scored once, at the end.

The keyword filter looks for the job's must-have words anywhere in the resume. All present: strong. Two or more missing: no. Otherwise: maybe.

| Resumes | Method | Right label | Shortlist (marked strong) | Strong fits found | Good candidates rejected |
| --- | --- | --- | --- | --- | --- |
| dev (21) | Keyword filter | 10/21 (48%) | 3/11 really strong | 3/6 | 1 |
| dev (21) | Scorer | 21/21 (100%) | 6/6 really strong | 6/6 | 0 |
| holdout (15) | Keyword filter | 8/15 (53%) | 2/4 really strong | 2/6 | 3 |
| holdout (15) | Scorer | **11/15 (73%)** | **2/2 really strong** | 2/6 | **1** |

- **Shortlist**: of the resumes marked strong, how many really were strong. This is what a busy manager reads first.
- **Good candidates rejected**: labeled strong or maybe, but scored no.

**Read the holdout row, not the dev row.** 100% on dev only means the rules fit the resumes they were built on. On unseen resumes the scorer gets 73% of labels right against 53% for keywords, every resume it shortlisted was really strong, and it wrongly rejected 1 good candidate against 3.

But it found only 2 of the 6 strong candidates, the same as the keyword filter. That is the honest weak spot.

### What went wrong on the holdout resumes

All 4 mistakes, from `eval/results.md`:

1. **"RESTful APIs" and "Django REST Framework"** did not count as "REST APIs". Two strong backend developers became maybe.
2. **"Team Leader"**, **"Supervised a team of 9"** and **"Led 6 agents"** did not count as "Team lead". The word list only knew "team lead", "led a team" and "managed a team", because those were the words in the dev resumes.
3. **"Customer care"** did not count as "Customer support". Together with point 2, a support lead with 8 years of experience was scored **no**. That is the one good candidate it wrongly rejected.

Three of the four landed in "maybe", which in practice means a person reads them. Only one was rejected.

I did not add these words after seeing the holdout. That would make the holdout score look better and mean nothing. The fix is to add them, then test again on new resumes.

## Fairness

- The scorer never reads the name. A test checks that changing the name does not change the result.
- It does not look at college, age, gender, photo or location. The reasons only quote work lines from the resume.
- In LLM mode the model is told not to mention or guess any of those.
- It is still only a first sort. A person should read every "maybe" and every "no" before rejecting anyone, and the word lists should be checked on your own past hires.

## When this does not work

- **Other words for the same skill.** This is the main weakness, as the holdout shows. Every new job needs its own list of other ways people write each skill, built from real resumes for that role.
- **Messy resumes.** It reads a simple text format (see `data/resumes.md`). Real PDFs need a text extraction step first, and two-column layouts often come out jumbled.
- **Judgement.** It cannot tell a 3-month side project from 3 years of daily work, or spot someone switching careers who would be great.

## How it works

```
job post (must-haves, nice-to-haves, minimum years)  +  resume text
   -> split the resume into work lines and the skills list (name is dropped)
   -> for each must-have:
        used in a work line?          -> shown
        "no hands-on", "learning"?    -> missing
        only in the skills list?      -> listed
        not there?                    -> missing
   -> add up years from the date ranges (overlaps counted once)
   -> strong: all shown and enough years | no: 2+ missing | maybe: the rest
   -> reasons, each quoting the resume line it came from
      (rewritten in plain sentences by an LLM if a key is set)
```

- `jobmatch/parse.py`: reads `data/jobs.md` and `data/resumes.md`
- `jobmatch/match.py`: the checks, the other-words list, years, and the keyword filter
- `jobmatch/explain.py`: the recruiter summary
- `eval/run_eval.py`: the table above

## Run it

```bash
pip install -r requirements.txt

# Offline, no API key
python run.py --job J1 --resume R04      # the keyword-stuffed resume
python run.py --job J3                   # all resumes for a job, best first

# The benchmark
python eval/run_eval.py
```

With an API key (any OpenAI-compatible provider), the reasons are rewritten as short sentences:

```bash
export LLM_API_KEY=your_key
export LLM_BASE_URL=https://...    # only for non-OpenAI providers
python run.py --job J2 --resume R16
```

LLM mode was not scored here because this run had no API key. It only rewrites the reasons. The strong, maybe or no decision is always made by the rules above.

## Use it for your own hiring

Add your job to `data/jobs.md` (`Must have:` and `Nice to have:` lists, `or` for alternatives). Paste 30 or more past resumes for that role, label them with the rules in `data/LABELING.md`, keep a third aside, and run the eval before you trust it.

## Tests

```bash
pytest -q
```

## Demo data

All job posts, resumes, names and companies are made up. No real candidates were used.
