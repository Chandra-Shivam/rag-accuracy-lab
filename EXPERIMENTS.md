# Experiments

Every change is measured on the same golden set. One change per row.

| Version | Change | Hit@5 | MRR | Correct | Faithful | Abstain acc. | Latency (s) | Tokens/q | Notes |
|---|---|---|---|---|---|---|---|---|---|
| v0 | Naive baseline | 0.795 | 0.597 | 0.795 | 0.940 | 0.909 | 4.18 | 1460 | Run 1 of 2, after the q44 fix; n=39 answerable, 11 unanswerable; median latency 2.07 s |
| v0 | Same code, run 2 (noise check) | 0.795 | 0.597 | 0.795 | 0.900 | 0.909 | 1.78 | 1462 | No change to code or questions; median latency 1.71 s |

## Day 3 noise check: v0 run 1 vs run 2

No prediction was recorded before run 2. Files: `evals/results/v0.jsonl`, `evals/results/v0_run2.jsonl`.

- **Retrieval:** same context on 50/50 questions, so Hit@5 and MRR did not move. A change in them comes from the code, not from noise.
- **Answers:** the text was identical on only 12/50 questions, so the generator varies between runs.
- **Correct:** the total is the same, but 2 of 39 verdicts flipped: q02 wrong to correct, q30 correct to wrong. The flips cancelled out.
- **Faithful:** 4 of 50 verdicts flipped: q12 to faithful; q27, q32 and q36 to unfaithful.
- **Abstain:** 0 flips.
- **Latency:** the run 1 mean is pulled up by outliers (max 21.8 s, against 3.25 s in run 2). The medians are closer: 2.07 s and 1.71 s. Cause of the outliers unknown.

Working noise floor from these two runs: Correct about 5 points (2 questions), Faithful about 8 points (4 questions), if the flips all went the same way. Compare runs question by question, because equal totals can hide flips. Two runs give only a rough estimate.

Not separated yet: every flipped question also had different answer text, so these runs can't show how much noise comes from the answer and how much from the judge. `evals/stability.py` tests this by judging the same saved answers again.

**Correctness rule change after run 2:** rule 4 now lets an answer leave out the year if the question makes it clear. Reason: q02 said "April 15" in both runs and got two different verdicts. The rule was changed after seeing these results, and the two runs above used the old rule.

**Golden set change after run 2:** the q30 answer now has all three cases from iss4.pdf p2, adding 855-641-6935 for applicants with a residence or business in the 50 states or DC. Reason: the old answer left out the case that applies to most US applicants, and run 2's more complete answer was marked wrong. The two runs above were scored against the old q30 answer.

**Prediction for the judge stability test and the correctness calibration re-run (written before the runs):** 8 of 12 checks stable; 10/10 agreement with hand labels.

Result: 9/12 stable (correctness 4/4, faithfulness 5/8); calibration 10/10 agreement, 10/10 stable. These use the new rule 4 and the new q30 answer.

- **Judge noise:** q12 was unstable on both answers. q36 was unstable on the run 2 answer, and on the run 1 answer gave 3 not_supported against supported in the saved run.
- **Verdict follows the answer text:** q27 and q32 were stable on each answer, with different verdicts for run 1 and run 2. For q27, run 2 really is worse. For q32 the run 2 verdict still looks too strict, and stable does not mean right.
- **q30:** correct on both answers after the golden fix.
- **q02:** run 1 answer correct 3/3, run 2 answer incorrect 3/3, both saying "April 15" with no year. The judge's reason on run 2 is the missing year, so the new rule 4 is not applied consistently. The question says 2025 and the deadline is in 2026, so "the question makes it clear" may be too vague.

**Rule 4 reworded after this test:** "Numbers and dates must be exact. A deadline without its year is still correct if the question names the tax year or period it belongs to." It was written by looking at q02, so q02 passing later is not independent evidence.

Prediction for the re-check (written before the run): q02 correct on 6 of 6 verdicts; calibration 10/10 agreement.

Result: q02 correct on 0 of 6 verdicts; all 6 say incorrect because the year 2026 is missing. Calibration 10/10 agreement, 10/10 stable. The reworded rule made q02 consistent, but in the opposite direction to the hand decision. One judge reason says the year is required because 2026 is not the tax year the question names (2025).

**Rule 4 final decision:** "Numbers and dates must be exact, including the year when the expected answer gives one." q02 now counts as wrong while its answer leaves out 2026. q02 was a retrieval miss, so on Day 4 check whether better retrieval brings the year into the answer. No prediction was taken for this small re-check.

Result under the final rule: q02 incorrect on 6 of 6 verdicts. The correctness calibration did not finish: it stopped after q01 and q05 (both agree) on the free-tier limit of 500 requests per day per model. Re-run it after the quota resets.

## Day 3 prediction for the full v0 eval (written before the first full run)

Correct 38/38. Faithful 80-90%. Abstain 4-5 of 12 (33-42%). Lowest type: unanswerable, because the answer prompt has no abstention rules.

Result (run 1, evals/results/v0.jsonl): Correct 78.9% (30/38), Faithful 94.0% (47/50), Abstain 83.3% (10/12). Lowest Correct: needs_table (0.625). Lowest Faithful: single_fact (0.857); unanswerable was 0.917.
Of the 8 wrong answers, 6 were retrieval misses (q02, q08, q20, q22, q27, q36) and 2 were page-level false hits where the table value was not in the retrieved text (q15, q35).
The numbers above are from before the q44 change below.

**Golden set change after run 1:** q44 ("Can I pay my federal taxes with Bitcoin?") moved from unanswerable to single_fact, gold p509.pdf p13. Reason: a label error. "Bitcoin" is absent from the corpus, but seven pages say "Digital assets are not accepted", so declining would be wrong. This raises Abstain, and was made because the label was wrong, not to improve the score. The set is now 15 single_fact, 8 needs_table, 8 multi_part, 8 comparison, 11 unanswerable. The same sentence is on 7 pages, so a retrieval that finds only another copy scores a false miss.

After re-scoring q44 (hit at rank 5, correct, faithful): Hit@5 79.5% (31/39), MRR 0.597, Correct 79.5% (31/39), Faithful 94.0% (47/50), Abstain 90.9% (10/11).

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