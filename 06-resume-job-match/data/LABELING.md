# How the labels were made

Every resume was labeled by hand against the one job it applies for, before any scoring code was written.

For each must-have skill, I asked one question: does the resume show it?

- **Shown**: the resume says the person used it in a job or a project.
- **Listed**: it only appears in a skills list, with no job or project that uses it.
- **Missing**: not there at all, or the resume says "no experience with it", "learning it" or "basic course only".

Then:

- **strong**: every must-have is shown, and total years of work are at least the job's minimum.
- **no**: 2 or more must-haves are missing.
- **maybe**: everything else (one must-have missing, a must-have only listed, or too few years).

Years of work come from the date ranges in the Experience section. "present" means 2026. Overlapping jobs are not double counted.

Names, colleges, age and gender play no part in the label.

Split: for each job, the first 7 resumes are **dev** (rules may be built while reading them) and the last 5 are **holdout** (not read while building rules, scored once at the end).
