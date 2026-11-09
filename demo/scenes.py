"""DEMO: the video script. Each scene is what is said, and what is shown while it is said.

Edit the narration here. python -m demo.build only re-generates voice clips whose text changed.
Kinds: slide, flow, code, live, terminal, results, trace, ci (see demo/pages.py and demo/record.py).
"""
from dataclasses import dataclass, field


@dataclass
class Scene:
    id: str
    kind: str
    narration: str
    show: dict = field(default_factory=dict)
    short: bool = False  # also in the 2-minute cut (python -m demo.build --short)


# TODO(human): read the narration through and change anything that doesn't sound like you.
SCENES = [
    Scene("s01", "slide", short=True, show={
        "label": "Portfolio project",
        "title": "RAG Accuracy Lab",
        "subtitle": "From 30/39 to 37/39 correct: fixing a RAG chatbot, one measured change at a time",
        "bullets": ["IRS payroll documents", "50 hand-written test questions", "Every change measured, including the failures"],
    }, narration=(
        "This is RAG Accuracy Lab: a chatbot that answers US payroll questions from IRS publications. "
        "The chatbot itself isn't the interesting part. The interesting part is that every change to it was measured. "
        "The naive version got 30 of 39 answerable questions right. "
        "The final version gets 34 to 37, cites its sources, and declines questions it can't answer."
    )),
    Scene("s02", "slide", show={
        "title": "The setup",
        "bullets": ["Corpus: 20 IRS payroll PDFs, 314 pages, 2026 revisions",
                    "Golden set: 39 answerable questions, each with its page and a quote as proof",
                    "Plus 11 questions the documents can't answer: the right reply is to decline",
                    "Scored on every version: right page found, correct, supported by the text, declines when it should"],
    }, narration=(
        "Here's the setup. The corpus is 20 IRS payroll PDFs, 314 pages, all 2026 revisions. "
        "I wrote 50 test questions by hand. 39 can be answered from the documents, and each one has the page and a quote that proves the answer. "
        "The other 11 can't be answered, so the right response is to decline. "
        "Every version of the system is scored on the same 50 questions: did retrieval find the right page, "
        "is the answer correct, is it supported by the retrieved text, and does it decline when it should."
    )),
    Scene("s03", "flow", show={
        "title": "The final pipeline",
        "steps": [("Question", ""), ("Vector search", "Pinecone, bge-small: matches meaning"),
                  ("Keyword search", "BM25: matches exact terms"), ("Fuse", "RRF, 40 candidates"),
                  ("Re-rank", "cross-encoder, top 5"), ("Neighbours", "same-page chunks"),
                  ("Gemini", "grounding and citation rules"), ("Citation check", "flags bad labels")],
    }, narration=(
        "This is the final pipeline. A question goes to two searches. "
        "Vector search in Pinecone matches meaning, and BM25 keyword search matches exact terms like form numbers. "
        "Reciprocal rank fusion merges the two lists into 40 candidates. "
        "A cross-encoder re-ranks them and keeps the best five, and each of those brings its neighbouring chunks from the same page. "
        "Gemini answers with strict rules: use only the context, cite every claim, and decline if the answer isn't there. "
        "Finally, code checks that every citation points to a page the model was actually given."
    )),
    Scene("s04", "code", show={
        "title": "Indexing (offline)",
        "blocks": [("rag/ingest.py", "load_pages"), ("rag/ingest.py", "chunk_pages"), ("rag/ingest.py", "save_chunks")],
    }, narration=(
        "Indexing runs once, offline. load_pages reads every PDF page with pypdf and keeps the page number, because citations need it. "
        "chunk_pages cuts the text into chunks of 1,000 characters. "
        "The chunks are embedded with bge-small, a local model, and stored in Pinecone. "
        "They're also saved to a file, so the keyword index can be rebuilt at startup without the PDFs. "
        "That's what lets the app ship in a container with no source documents inside."
    )),
    Scene("s05", "code", show={
        "title": "Retrieval",
        "blocks": [("rag/answer.py", "retrieve"), ("rag/hybrid.py", "fuse"), ("rag/rerank.py", "rerank")],
    }, narration=(
        "This is retrieve, the heart of the system. It takes 20 results from vector search and 20 from keyword search. "
        "fuse combines them with reciprocal rank fusion. Each chunk scores one over sixty plus its rank in each list, "
        "so a chunk that ranks well in both rises to the top. "
        "rerank then scores every candidate together with the question using a cross-encoder. "
        "It reads both texts at once, which is much more accurate than comparing two separate embeddings."
    )),
    Scene("s06", "code", show={
        "title": "Generation and citations",
        "blocks": [("rag/answer.py", "PROMPT"), ("rag/answer.py", "stream_answer"), ("rag/citations.py", "check_citations")],
    }, narration=(
        "The prompt has three rules: use only the context, cite the label of every block you use, and copy dates and amounts exactly. "
        "stream_answer sends the sources first, then the answer piece by piece as Gemini writes it, and the citation check last. "
        "check_citations pulls every bracket out of the answer and keeps only labels that exactly match a block in the context, "
        "so a made-up page number gets flagged."
    )),
    Scene("s07", "code", show={
        "title": "Serving",
        "blocks": [("api.py", "query_stream"), ("static/index.html", ("while (true) {", "answer.textContent += data;"))],
    }, narration=(
        "The API is FastAPI. The stream route wraps each event in the server-sent events format: an event name, and a line of JSON data. "
        "On the page, a short JavaScript loop reads the stream. "
        "Network chunks don't line up with events, so it keeps a buffer, handles only complete events, and keeps the unfinished part for the next read."
    )),
    Scene("s08", "live", short=True, show={
        "question": "On the 2026 W-4 deductions worksheet, how much do I enter if I'm 65 or older?",
        "open_citation": True,
    }, narration=(
        "Let's run it. I'll ask how much to enter on the 2026 W-4 deductions worksheet if I'm 65 or older. "
        "The answer streams in, and it cites Form W-4, page 4. "
        "The page only lists sources the answer actually cited. "
        "Clicking the link opens the IRS PDF at that exact page, and there it is: line 3a, six thousand dollars."
    )),
    Scene("s09", "live", short=True, show={
        "question": "What is the exact penalty amount if I file my 2025 individual return late?",
    }, narration=(
        "Now a question the documents can't answer: the exact penalty for filing a 2025 individual return late. "
        "These are mostly employer publications, so the honest answer is to decline. "
        "It does, and it says what it did find, which isn't the amount I asked for."
    )),
    Scene("s10", "code", show={
        "title": "Measuring",
        "blocks": [("evals/run.py", "score_question"), ("evals/judge.py", "Verdict"), ("evals/judge.py", "judge_correctness")],
    }, narration=(
        "Here's how it was measured. run.py sends each test question through the system, "
        "then a separate Gemini judge decides three things: is the answer correct, is it supported by the context, "
        "and did it decline when it should. Each judge must return a fixed label through a Pydantic schema. "
        "Before trusting any judge, I checked it against labels I wrote by hand, "
        "and ran each example three times to make sure it doesn't change its mind."
    )),
    Scene("s11", "results", short=True, show={"title": "Results, one change at a time"}, narration=(
        "These are the results, one change at a time. Re-ranking put the right page in the top five more often. "
        "Neighbouring chunks gave the biggest jump in correct answers, because many answers were split across a chunk boundary. "
        "Hybrid search pushed hit at five to 0.974. "
        "A stronger embedding model, v4, retrieved slightly better but answered no better and was slower, so I didn't keep it. "
        "The prompt rules in v5 and v6 didn't raise accuracy, but nearly every answer now cites its source, and refusals are consistent."
    )),
    Scene("s12", "terminal", show={
        "title": "Comparing two runs, question by question",
        "commands": [["python", "evals/compare.py", "v0_run3", "v6_prompt_fixes"]],
    }, narration=(
        "Totals can hide changes, so compare.py lists every question that flipped between two runs. "
        "This led to the biggest lesson of the project. When I ran the same code twice, only 12 of the 50 answers came out word for word the same. "
        "So I ran every version that mattered twice, and I only trust a gain that's bigger than that noise."
    )),
    Scene("s13", "trace", show={"title": "Tracing in production (LangSmith data)"}, narration=(
        "In production, every question is one LangSmith trace: the root, the retrieval step with its sources, and the Gemini call with its tokens. "
        "Each trace is tagged with the git commit, the prompt version, and two flags, refused and citations ok, "
        "so false refusals and bad citations can be found in real traffic."
    )),
    Scene("s14", "terminal", show={
        "title": "The eval gate",
        "commands": [["python", "evals/gate.py", "v6_prompt_fixes_run2"], ["python", "evals/gate.py", "v5_grounding"]],
    }, narration=(
        "An eval gate turns results into a clear pass or fail, with an exit code that CI can read. "
        "It first checks that the run is complete, so a run that stopped halfway can't look good. Then it checks minimum scores. "
        "The final v6 run passes. The older v5 run fails on faithfulness."
    )),
    Scene("s15", "ci", show={"title": "Unit tests on every push (GitHub Actions data)"}, narration=(
        "Unit tests run on every push in GitHub Actions. "
        "I broke one test on purpose, to confirm that a failure really shows up as red and doesn't get reported as a pass."
    )),
    Scene("s16", "slide", short=True, show={
        "title": "What I learned",
        "bullets": ["Measure before changing anything, and change one thing at a time",
                    "Run it twice: only 12 of 50 answers were identical across two runs",
                    "Known failures: one retrieval miss, one false refusal",
                    "Reports what IRS publications say; not tax advice"],
    }, narration=(
        "To sum up: measure before you change anything, change one thing at a time, and run it twice, because these systems are noisy. "
        "The final version still has known failures: one question where retrieval misses the evidence, "
        "and one false refusal, where the model doesn't connect Bitcoin to digital assets. "
        "It reports what IRS publications say, and it isn't tax advice. "
        "The code, the full experiment log and the results are on GitHub."
    )),
]
