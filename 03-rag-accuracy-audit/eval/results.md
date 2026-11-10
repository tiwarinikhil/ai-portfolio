# Results

30 questions, retriever BM25 (top 5).

| Setup | Chunks | Hit@1 | Hit@3 | MRR |
| --- | --- | --- | --- | --- |
| Raw chunks (split on blank lines) | 68 | 30% | 70% | 0.50 |
| Only drop the stale document | 58 | 40% | 73% | 0.57 |
| Only remove duplicate footers | 63 | 23% | 70% | 0.45 |
| Only merge heading chunks | 34 | 63% | 73% | 0.69 |
| All three fixes | 25 | 70% | 80% | 0.74 |
| All three fixes + simple stemming | 25 | 77% | 90% | 0.83 |
