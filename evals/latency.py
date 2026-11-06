"""MEASURE box of MAP.md: re-time every version in one session, so server load doesn't look like a code change.

Usage: python evals/latency.py retrieval   (v0 to v4 retrieval settings on the 39 answerable questions, no Gemini answers)
       python evals/latency.py gemini      (the Gemini step for three prompt setups on 10 questions, 30 calls)
The versions take turns on each question. The Gemini step reuses each version's saved context,
so only the prompt and the context size differ. Saves evals/results/latency_<mode>.jsonl.
"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# "python evals/latency.py" puts evals/ on the path, not the project root.
sys.path.insert(0, str(ROOT))

from langchain_google_genai.chat_models import GoogleAPIError

import rag.answer
from evals.run import load_golden
from rag.answer import PROMPT, RATE_LIMITER, REFUSAL, retrieve
from rag.store import get_store

RESULTS = ROOT / "evals" / "results"
# name: (embedder, hybrid, candidates, window). v5 and v6 retrieve exactly as v3.
RETRIEVAL = {"v0": ("bge", 0, None, 0), "v1": ("bge", 0, 20, 0), "v2": ("bge", 0, 20, 1),
             "v3": ("bge", 20, 40, 1), "v4": ("gemini", 0, 20, 1)}
# The prompt from v0 to v4, before Day 5 added the rules.
OLD_PROMPT = """Answer the question using the context below.

Context:
{context}

Question: {question}"""
# name: (saved run whose contexts are reused, prompt). v1's context is the same size as v0's.
GEMINI = {"v0-v1": ("v0_run3", OLD_PROMPT), "v2-v4": ("v3_hybrid20_run2", OLD_PROMPT),
          "v5-v6": ("v6_prompt_fixes", PROMPT)}
GEMINI_QUESTIONS = 10
WAIT = 90


def taking_turns(names, i):
    """Rotates the order on each question, so no version always goes first."""
    return names[i % len(names):] + names[:i % len(names)]


def time_retrieval():
    stores = {embedder: get_store(embedder) for embedder in ("bge", "gemini")}
    questions = [q for q in load_golden() if q["type"] != "unanswerable"]
    rows = []
    for i, q in enumerate([questions[0]] + questions):  # the first pass is a warm-up and is not saved
        for name in taking_turns(list(RETRIEVAL), i):
            embedder, hybrid, candidates, window = RETRIEVAL[name]
            rag.answer._store = stores[embedder]  # retrieve() searches whichever store is set here
            start = time.perf_counter()
            retrieve(q["question"], candidates=candidates, window=window, hybrid=hybrid)
            if i:
                rows.append({"version": name, "id": q["id"], "seconds": round(time.perf_counter() - start, 3)})
    return rows


def invoke(llm, prompt):
    for retry in range(8):
        try:
            RATE_LIMITER.acquire()
            start = time.perf_counter()
            reply = llm.invoke(prompt)
            return time.perf_counter() - start, reply.usage_metadata["total_tokens"]
        except GoogleAPIError as error:
            if "503" not in str(error) or retry == 7:
                raise
            print(f"503, waiting {WAIT} s", flush=True)
            time.sleep(WAIT)


def time_gemini():
    llm = rag.answer._get_llm()
    saved = {name: {r["id"]: r for r in map(json.loads, (RESULTS / f"{run}.jsonl").read_text().splitlines())}
             for name, (run, _) in GEMINI.items()}
    answerable = [qid for qid, r in saved["v5-v6"].items() if r["type"] != "unanswerable"]
    rows = []
    for i, qid in enumerate(answerable[::len(answerable) // GEMINI_QUESTIONS][:GEMINI_QUESTIONS]):
        for name in taking_turns(list(GEMINI), i):
            r = saved[name][qid]
            prompt = GEMINI[name][1].format(refusal=REFUSAL, context=r["context"], question=r["question"])
            seconds, tokens = invoke(llm, prompt)
            rows.append({"version": name, "id": qid, "seconds": round(seconds, 3), "tokens": tokens})
            print(name, qid, f"{seconds:.2f} s", flush=True)
    return rows


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("retrieval", "gemini"):
        sys.exit("usage: python evals/latency.py retrieval|gemini")
    mode = sys.argv[1]
    rows = time_retrieval() if mode == "retrieval" else time_gemini()
    (RESULTS / f"latency_{mode}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for name in dict.fromkeys(r["version"] for r in rows):
        seconds = sorted(r["seconds"] for r in rows if r["version"] == name)
        print(f"{name:<6} n={len(seconds):<3} median {statistics.median(seconds):.2f} s  "
              f"p95 {statistics.quantiles(seconds, n=20)[-1]:.2f} s")


if __name__ == "__main__":
    main()
