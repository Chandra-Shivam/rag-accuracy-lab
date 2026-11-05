"""ANSWERING box of MAP.md: check the model's citations against the labels in the context. No LLM.

Flags only: the answer is returned unchanged. A valid citation means that source was sent to the
model, not that the page supports the claim. The Faithful judge checks that.
"""
import re

CONTEXT_LABEL = re.compile(r"^\[([^\[\]]+, page \d+)\]$", re.MULTILINE)
BRACKET = re.compile(r"\[([^\[\]]+)\]")
# A comma followed by a file name starts a new citation: "a.pdf, page 1, b.pdf, page 2".
NEXT_CITATION = re.compile(r",\s*(?=[^\s,]+\.pdf)")


def check_citations(answer, context):
    """Splits each bracket into citations and sorts them by whether they exactly match a context label."""
    labels = set(CONTEXT_LABEL.findall(context))
    citations = [part.strip() for bracket in BRACKET.findall(answer) for part in NEXT_CITATION.split(bracket)]
    return {"valid": [c for c in citations if c in labels], "invalid": [c for c in citations if c not in labels]}


def citations_ok(result):
    """True if the answer cites at least one source and every citation is valid."""
    return bool(result["valid"]) and not result["invalid"]
