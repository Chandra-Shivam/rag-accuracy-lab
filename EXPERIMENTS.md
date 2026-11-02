# Experiments

Every change is measured on the same golden set. One change per row.

| Version | Change | Hit@5 | MRR | Correct | Faithful | Abstain acc. | Latency (s) | Tokens/q | Notes |
|---|---|---|---|---|---|---|---|---|---|
| v0 | Naive baseline | 0.789 | 0.607 | | | | | | Retrieval only so far; n=38 answerable |

## Day 3 prediction for abstention judge calibration (written before the first run)

The judge agrees with the hand labels on all 8 examples.

Result: agreement 8/8, stable across 3 runs 8/8. The rules were discussed using some of these same examples, so this is not a held-out test.

## Day 3 prediction for faithfulness judge calibration (written before the first run)

The judge agrees with the hand labels on all 8 examples.

Result: agreement 5/8, stable across 3 runs 8/8. Disagreements: q27, q39, q41. On review, the judge looks right on q39 and q41 (hand labels to re-check), and too lenient on q27.

Run 2 changes: q39 relabelled not_supported, q41 relabelled supported, question added to the faithfulness prompt.
Run 2 prediction (written before the run): agreement 8/8.
Run 2 result: agreement 6/8, stable 7/8. Disagreements: q15 (1 of 3 runs flipped), q27 (still supported). Run 1's verdicts on the new labels would have been 7/8 agreement, 8/8 stable, so adding the question did not help.
Decision: question removed from the prompt; judge accepted. Known limitation: it can pass an answer whose sentences are each true but which doesn't support what it claims as the answer (q27), so Faithful may be a little high. Hand-check a sample of `supported` verdicts after the full run.

## Day 3 prediction for judge calibration (written before the first run)

The judge agrees with the hand labels on 70% of the 10 examples.

Result: agreement 10/10, stable across 3 runs 10/10. The rules were discussed using these same examples, so this is not a held-out test.

## Day 3 prediction for v0 retrieval (written before the first real run)

Hit@5 57%, MRR 0.3, lowest type: needs_table.

Result: Hit@5 78.9% (30/38), MRR 0.607. Lowest hit@5: single_fact (0.714). Lowest MRR: needs_table (0.510).
Misses: q01, q02, q03, q08, q20, q22, q27, q36. Causes not labelled yet. Each type has only 8-14 questions, so one question moves its hit@5 by 7-12 points.

## Day 1 predictions for v0 (written before any code)

Golden set: 50 questions (14 single_fact, 8 needs_table, 8 multi_part, 8 comparison, 12 unanswerable).
Failures will be labelled by stage: **ingestion** (text extraction), **retrieval** (gold page not in top-k)
or **generation** (wrong answer, or answered when it should have abstained).

Ranked from most failures to fewest:

1. **unanswerable**, generation. Top-k always returns the closest chunks, often lookalikes
   (e.g. employer penalties for q39). With no abstention rule, the model answers from them.
2. **needs_table**, ingestion. Flattened tables either keep the chunk out of the top-k or make
   the model read the wrong row (q15/q35 also need the rule on p15t p6 *and* the table on p7).
3. **multi_part**, generation and chunking. All 8 have one gold page; expect partial answers,
   or a chunk boundary splitting the two parts.
4. **comparison**, retrieval and generation. q35 and q36 need both gold pages in the top-k;
   q34 needs arithmetic.
5. **single_fact**, retrieval. Mostly right; risks are near-duplicate forms (W-4 / W-4P / W-4 sp)
   and q05, where training memory ($600) contradicts the document ($2,000).