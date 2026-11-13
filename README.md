# AI Portfolio

Practical AI projects by Nikhil Tiwary, AI Engineer (M.Tech in AI, IIT Ropar). Each project solves a real business problem, has tests, and shows results with numbers.

| # | Project | What it shows | Stack |
| --- | --- | --- | --- |
| 01 | [Docs Chatbot with Evals](01-docs-chatbot-evals) | RAG chatbot with sources, and proof that heading-based chunking beats fixed-size chunking (79% to 100% Hit@1) | Python, FastAPI, BM25, embeddings, OpenAI-compatible LLMs |
| 02 | [Lead Qualifier Agent](02-lead-qualifier-agent) | Scores leads with reasons and drafts replies a human approves. 88% vs 69% accuracy against budget-only sorting on a holdout set | Python, LangGraph, OpenAI-compatible LLMs |
| 03 | [RAG Accuracy Audit Tool](03-rag-accuracy-audit) | Finds the chunks that make a RAG bot answer wrong (stale pages, heading-only chunks, footers) and fixes them: Hit@1 30% to 70% | Python, BM25, OpenAI-compatible LLMs |
| 04 | [Meeting Notes to Tasks](04-meeting-notes-to-tasks) | Turns a meeting transcript into tasks with owners and due dates, with a human-check list. 69% fully right on unseen meetings vs 6% for keyword matching | Python, rule-based NLP, OpenAI-compatible LLMs |
| 05 | [Voice FAQ Agent for a Clinic](05-voice-faq-clinic) | Phone assistant that answers clinic FAQs and sends emergencies and medical questions to a person. On unseen calls: 3/3 emergencies caught, 2 wrong answers vs 8 for a simple FAQ bot | Python, BM25, OpenAI-compatible speech and LLM APIs |

New project every week.

## Work with me

I build RAG chatbots, LLM agents and AI automations for businesses.
Website: [nikhiltiwary.in](https://nikhiltiwary.in) · GitHub: [tiwarinikhil](https://github.com/tiwarinikhil)
