# Results

| Resumes | Method | Right label | Shortlist (marked strong) | Strong fits found | Good candidates rejected |
| --- | --- | --- | --- | --- | --- |
| dev (21) | Keyword filter | 10/21 (48%) | 3/11 really strong | 3/6 | 1 |
| dev (21) | Scorer | 21/21 (100%) | 6/6 really strong | 6/6 | 0 |
| holdout (15) | Keyword filter | 8/15 (53%) | 2/4 really strong | 2/6 | 3 |
| holdout (15) | Scorer | 11/15 (73%) | 2/2 really strong | 2/6 | 1 |

## Scorer mistakes

- **R08** (holdout, J1): labeled strong, scored maybe
  - Has Python: "Built the public API with Django REST Framework on Python 3."
  - Has Django or FastAPI: "Built the public API with Django REST Framework on Python 3."
  - Has PostgreSQL: "Ran Postgres 14 in production and handled schema changes."
  - Missing REST APIs
  - 5 years of work, job asks for 3 (enough)
  - Nice to have: Docker, Redis
- **R11** (holdout, J1): labeled strong, scored maybe
  - Has Python: "Wrote RESTful APIs in Python with FastAPI for hotel bookings."
  - Has Django or FastAPI: "Wrote RESTful APIs in Python with FastAPI for hotel bookings."
  - Has PostgreSQL: "Owned the PostgreSQL database for search and pricing."
  - Missing REST APIs
  - 4 years of work, job asks for 3 (enough)
  - Nice to have: AWS
- **R32** (holdout, J3): labeled strong, scored no
  - Missing Customer support
  - Missing Team lead
  - Has Zendesk or Freshdesk: "Ran Freshdesk queues and weekly quality checks."
  - 8 years of work, job asks for 4 (enough)
- **R35** (holdout, J3): labeled strong, scored maybe
  - Has Customer support: "Supervised a team of 9 in customer support for home service bookings."
  - Missing Team lead
  - Has Zendesk or Freshdesk: "Ran the Zendesk setup, views and reports."
  - 6 years of work, job asks for 4 (enough)
  - Nice to have: CSAT
