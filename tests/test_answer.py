"""Pins what counts as a refusal and that the prompt asks for that exact text."""

from rag.answer import PROMPT, REFUSAL, is_refusal


def test_exact_refusal_is_a_refusal():
    assert is_refusal(REFUSAL)
    assert is_refusal(f"\n{REFUSAL} \n")


def test_refusal_with_other_claims_is_not_a_refusal():
    assert not is_refusal(f"{REFUSAL} The 2026 limit is $184,500 [p15.pdf, page 2].")


def test_prompt_contains_the_exact_refusal():
    assert REFUSAL in PROMPT.format(refusal=REFUSAL, context="c", question="q")
