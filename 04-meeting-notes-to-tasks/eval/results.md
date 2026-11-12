# Results

| Split | Method | Tasks (real) | Precision | Recall | Owner right | Due date right | Fully right |
| --- | --- | --- | --- | --- | --- | --- | --- |
| dev | baseline | 22 | 70% | 95% | 48% | 19% | 2/22 (9%) |
| dev | rules | 22 | 100% | 100% | 100% | 100% | 22/22 (100%) |
| holdout | baseline | 16 | 81% | 81% | 54% | 23% | 1/16 (6%) |
| holdout | rules | 16 | 94% | 94% | 93% | 73% | 11/16 (69%) |

Rules mode errors:

- holdout-01-realty-sales.txt turn 11: got owner Mark, due 2026-11-20; expected owner Mark, due None
- holdout-02-grocery-ops.txt turn 6: got owner None, due None; expected owner Ravi, due 2026-11-16
- holdout-02-grocery-ops.txt turn 7: not a real task, but extracted
- holdout-02-grocery-ops.txt turn 11: missed (owner Elena, due 2026-11-20)
- holdout-03-tutoring-team.txt turn 9: got owner Kate, due 2026-11-24; expected owner Kate, due None
- holdout-03-tutoring-team.txt turn 12: got owner Shreya, due None; expected owner Shreya, due 2026-11-18
