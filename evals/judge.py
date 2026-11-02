"""Judges for the MEASURE box of MAP.md.

Correctness compares an answer with the golden answer. Faithfulness compares it with the chunks it came from.
Abstention decides whether the answer declined the question.

Usage: python -m evals.judge correctness           (checks that judge against its hand labels)
       python -m evals.judge faithfulness          (checks that judge against its hand labels)
       python -m evals.judge abstention            (checks that judge against its hand labels)
       python -m evals.judge prepare-faithfulness  (creates the faithfulness examples to label)
Needs GOOGLE_API_KEY in .env. Calibration makes (labelled examples x RUNS) Gemini calls.
"""
import json
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from rag.answer import RATE_LIMITER, answer

JUDGE_MODEL = "gemini-3.5-flash-lite"
EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parent
CORRECTNESS_CALIBRATION = EVALS / "judge_calibration.jsonl"
FAITHFULNESS_CALIBRATION = EVALS / "faithfulness_calibration.jsonl"
ABSTENTION_CALIBRATION = EVALS / "abstention_calibration.jsonl"
FAITHFULNESS_REVIEW = ROOT / "data" / "cache" / "faithfulness_review.md"  # readable copy, git-ignored
# Mix: answerable (q34 needs arithmetic) and unanswerable, where the model may invent an answer.
FAITHFULNESS_IDS = ["q01", "q15", "q27", "q34", "q36", "q39", "q41", "q45"]
RUNS = 3  # same example, repeated: a judge that changes its mind can't compare experiments

RULES = (
    "1. A partly right answer is incorrect. Every detail the question asks for must be present; "
    "details in the expected answer that the question did not ask for are optional.\n"
    "2. Extra text beyond the expected answer is fine.\n"
    "3. If the answer contains the right fact but also a wrong one, it is incorrect.\n"
    "4. Numbers and dates must be exact.\n"
    "5. When unsure use a stricter Verdict (incorrect)"
)

FAITHFULNESS_RULES = (
    "1. The answer is supported only if every claim in it is supported by the context. "
    "If any claim is missing from, only partly supported by, or contradicted by the context, "
    "the answer is not_supported.\n"
    "2. A calculation is supported if its numbers come from the context and the result is right.\n"
    "3. A statement that the context does not contain some information is supported if that is true.\n"
    "4. Ignore phrases that make no factual claim, such as 'Based on the provided context'.\n"
    "5. When unsure, choose not_supported."
)

ABSTENTION_RULES = (
    "1. The reply is abstained if it says the information is not available and does not give the requested fact. "
    "Related facts that do not answer the question do not change this.\n"
    "2. The reply is answered if it gives the requested fact, or tries to respond with guidance, "
    "even if the response is wrong or incomplete.\n"
    "3. When unsure, choose answered."
)

PROMPT = """You are grading an answer against the expected answer.

Rules:
{rules}

Question: {question}
Expected answer: {expected}
Answer to grade: {answer}"""

FAITHFULNESS_PROMPT = """You are checking whether an answer is supported by the context it was written from.
Use only the context. Do not use outside knowledge, and do not judge whether the answer is true.

Rules:
{rules}

Context:
{context}

Answer to check: {answer}"""


ABSTENTION_PROMPT = """You are deciding whether a reply declined to answer the question.
Do not judge whether the reply is true or correct.

Rules:
{rules}

Question: {question}
Reply: {answer}"""


class Verdict(BaseModel):
    # reason comes first so the model explains itself before it commits to a label.
    reason: str
    label: Literal["correct", "incorrect"]


class FaithfulnessVerdict(BaseModel):
    reason: str
    label: Literal["supported", "not_supported"]


class AbstentionVerdict(BaseModel):
    reason: str
    label: Literal["abstained", "answered"]


_judges = {}


def _get_judge(schema):
    if schema not in _judges:
        load_dotenv()
        llm = ChatGoogleGenerativeAI(model=JUDGE_MODEL, rate_limiter=RATE_LIMITER)
        _judges[schema] = llm.with_structured_output(schema)
    return _judges[schema]


def judge_correctness(question, expected, answer):
    if not RULES.strip():
        raise RuntimeError("RULES is empty: see evals/judge.py")
    prompt = PROMPT.format(rules=RULES, question=question, expected=expected, answer=answer)
    return _get_judge(Verdict).invoke(prompt)


def judge_faithfulness(context, answer):
    if not FAITHFULNESS_RULES.strip():
        raise RuntimeError("FAITHFULNESS_RULES is empty: see TODO(human) in evals/judge.py")
    prompt = FAITHFULNESS_PROMPT.format(rules=FAITHFULNESS_RULES, context=context, answer=answer)
    return _get_judge(FaithfulnessVerdict).invoke(prompt)


def judge_abstention(question, answer):
    if not ABSTENTION_RULES.strip():
        raise RuntimeError("ABSTENTION_RULES is empty: see TODO(human) in evals/judge.py")
    prompt = ABSTENTION_PROMPT.format(rules=ABSTENTION_RULES, question=question, answer=answer)
    return _get_judge(AbstentionVerdict).invoke(prompt)


def calibrate(path, judge, runs=RUNS):
    examples = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    unlabelled = [e["id"] for e in examples if e["label"] is None]
    if unlabelled:
        raise RuntimeError(f"hand-label these first: {unlabelled}")

    agreed = stable = 0
    for e in examples:
        verdicts = [judge(e) for _ in range(runs)]
        labels = [v.label for v in verdicts]
        is_stable = len(set(labels)) == 1
        # Agreement counts only if every run matches the hand label.
        is_agreed = all(label == e["label"] for label in labels)
        stable += is_stable
        agreed += is_agreed
        print(f"{e['id']}  hand: {e['label']}  judge: {labels}")
        if not is_agreed:
            print(f"     {verdicts[0].reason}")
    n = len(examples)
    print(f"agreement with hand labels {agreed}/{n}, stable across {runs} runs {stable}/{n}")


def prepare_faithfulness():
    """Saves real answers with the context they came from, ready for hand labels."""
    if FAITHFULNESS_CALIBRATION.exists():
        sys.exit(f"{FAITHFULNESS_CALIBRATION.name} already exists; not overwriting hand labels")
    golden = [json.loads(line) for line in (EVALS / "golden.jsonl").read_text().splitlines() if line.strip()]
    questions = {q["id"]: q for q in golden}
    rows = []
    for qid in FAITHFULNESS_IDS:
        q = questions[qid]
        result = answer(q["question"])
        rows.append({"id": qid, "type": q["type"], "question": q["question"], "context": result["context"],
                     "answer": result["answer"], "label": None})
        print(f"{qid} done", flush=True)
    FAITHFULNESS_CALIBRATION.write_text("".join(json.dumps(r) + "\n" for r in rows))
    FAITHFULNESS_REVIEW.parent.mkdir(parents=True, exist_ok=True)
    FAITHFULNESS_REVIEW.write_text("\n\n".join(
        f"# {r['id']} ({r['type']})\n\n**Question:** {r['question']}\n\n**Answer:**\n\n{r['answer']}\n\n"
        f"**Context:**\n\n{r['context']}" for r in rows))
    print(f"label in {FAITHFULNESS_CALIBRATION}\nread in {FAITHFULNESS_REVIEW}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "correctness":
        calibrate(CORRECTNESS_CALIBRATION, lambda e: judge_correctness(e["question"], e["expected"], e["answer"]))
    elif command == "faithfulness":
        calibrate(FAITHFULNESS_CALIBRATION, lambda e: judge_faithfulness(e["context"], e["answer"]))
    elif command == "abstention":
        calibrate(ABSTENTION_CALIBRATION, lambda e: judge_abstention(e["question"], e["answer"]))
    elif command == "prepare-faithfulness":
        prepare_faithfulness()
    else:
        sys.exit("usage: python -m evals.judge correctness | faithfulness | abstention | prepare-faithfulness")
