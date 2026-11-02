"""Metrics, as fixed in PLAN.md (Day 3). Pure functions: no Pinecone, no LLM.

gold = the golden set's list of {source, page}; sources = retrieved chunks in rank order.
Unanswerable questions (gold = []) must be filtered out by the caller of is_hit and reciprocal_rank.
"""


def _page(entry):
    return entry["source"], entry["page"]


def is_hit(gold, sources):
    """True only if ALL gold pages appear somewhere in the retrieved chunks."""
    return {_page(g) for g in gold} <= {_page(s) for s in sources}


def reciprocal_rank(gold, sources):
    """1 / rank of the first chunk on any gold page (rank 1 = top); 0 if none."""
    gold_pages = {_page(g) for g in gold}
    for rank, s in enumerate(sources, 1):
        if _page(s) in gold_pages:
            return 1 / rank
    return 0.0


def summarize(rows):
    """Averages each metric over the rows that have it; None if no row has it.

    Each metric lives only on the rows it applies to: an unanswerable row has "abstained",
    but no "hit", "rr" or "correct". So every metric gets the right denominator automatically.
    """
    return {key: _mean([r[key] for r in rows if key in r])
            for key in ("hit", "rr", "correct", "faithful", "abstained", "latency", "tokens")}


def _mean(values):
    return sum(values) / len(values) if values else None
