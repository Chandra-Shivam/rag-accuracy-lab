# Project
Measured RAG accuracy improvement. Plan: PLAN.md. Results log: EXPERIMENTS.md. Pipeline map: MAP.md.
Quick reference: NOTES.md. After answering a doubt or adding/changing a file, add or update a 1–2 line entry there. Keep it short.
Progress and resume point: STATUS.md. Read it at the start of a session; update it at the end.

# Working style
- Repo files stay in simple English.
- Leave real design decisions as TODO(human), and commit only after review.

# Commands
- Run the full eval: python evals/run.py
- Run one eval case: python evals/run.py <case_id>
- Start the API: uvicorn api:api --reload

# Gotchas
- Free-tier Gemini quotas are tight; run single cases while debugging.
- Never commit .env.