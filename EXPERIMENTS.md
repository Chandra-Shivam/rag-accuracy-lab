# Experiments

Every change is measured on the same golden set. One change per row.

| Version | Change | Hit@5 | MRR | Correct | Faithful | Abstain acc. | Latency (s) | Tokens/q | Notes |
|---|---|---|---|---|---|---|---|---|---|
| v0 | Naive baseline | 0.795 | 0.597 | 0.795 | 0.940 | 0.909 | 4.18 | 1460 | Run 1 of 2, after the q44 fix; n=39 answerable, 11 unanswerable; median latency 2.07 s |
| v0 | Same code, run 2 (noise check) | 0.795 | 0.597 | 0.795 | 0.900 | 0.909 | 1.78 | 1462 | No change to code or questions; median latency 1.71 s |
| v0 | Run 3, final judge rules and golden answers (**baseline**) | 0.795 | 0.597 | 0.769 | 0.880 | 0.909 | 1.93 | 1467 | Compare later versions with this row; median latency 1.92 s |
| v1 | Re-ranking, 20 candidates, ms-marco-MiniLM-L-6-v2 | 0.897 | 0.722 | 0.846 | 0.960 | 0.909 | 5.86 | 1440 | Run 1; median latency 6.16 s, but most of the rise is Gemini time, not re-ranking (see Day 4 notes) |
| v1 | Same code, run 2 (noise check) | 0.897 | 0.722 | 0.872 | 0.940 | 0.818 | 3.07 | 1438 | No change to code or questions; median latency 1.97 s. q24's Correct and q40's Abstain look like judge errors (see Day 4 notes) |
| v2 | Neighbouring chunks, same page, window 1 | 0.897 | 0.722 | 0.923 | 1.000 | 0.909 | 3.46 | 3357 | Run 1; median latency 2.50 s; Evidence 0.897, up from 0.667 (see Day 4 notes) |

## Day 4 re-ranking

Change: fetch more chunks from Pinecone, re-score them with `cross-encoder/ms-marco-MiniLM-L-6-v2`, keep the best 5.

Prediction (written before the run): Hit@5 36/39, MRR 0.8. 50 candidates beat 20, and the number can be reduced later if 50 is too many.

Retrieval-only result (no answers or judges yet):

| Candidates | Hit@5 | MRR | Median retrieval time, 30 questions |
|---|---|---|---|
| Off (v0) | 0.795 (31/39) | 0.597 | 0.35 s |
| 20 | 0.897 (35/39) | 0.722 | 0.53 s |
| 50 | 0.897 (35/39) | 0.721 | 0.64 s |

- **Fixed misses:** q01, q02, q03, q27, q36. The gold chunk for q02 is now at rank 5.
- **Still missing:** q08 and q20 (gold chunks below 50 for search), q22 (gold chunks are in the top 20, but the re-ranker does not put them in the top 5).
- **New miss, q44:** the top 5 holds other copies of the "Digital assets are not accepted" sentence, not gold page p509 p13. This looks like the false miss noted when q44 was moved, not a real loss.
- **Not fixed behind the hit:** q15 and q35 count as hits, but the Table 2 chunk with the needed values is still outside the top 5, so their answers will probably stay wrong.

Decision: 20 candidates, since the scores match 50 and it is faster.

Prediction for the full eval with 20 candidates (written before the run): Correct 35/39, Faithful 46/50, Abstain 11/11.

Result (`evals/results/v1_rerank20.jsonl`): Correct 33/39 (0.846), Faithful 48/50 (0.960), Abstain 10/11 (0.909). Wrong: q02, q08, q15, q22, q24, q35. Unfaithful: q12, q48.

- **Correct gains:** q27 and q36 (the gold page is now retrieved) and q20 (a hit@5 miss, but the answer is right from another page). q37 also flipped back; it was right in v0 runs 1 and 2, so that is probably noise, not re-ranking.
- **Correct loss, q24:** a real regression. Re-ranking moved the chunk with the 6.0% rate out of the context, and the answer gives only 0.6%.
- **q02:** the gold chunk is now in the context, but the answer still leaves out 2026 in this run.
- **Unchanged:** q15 and q35 still lack the Table 2 value, and q39 still does not abstain. Its answer also looks unsupported, as in v0, so its faithful verdict here is doubtful.
- **Faithful:** q48 and q12 look like too-strict verdicts. The rise to 0.960 is just above the v0 range of 0.880 to 0.940, so it is not clear evidence yet.
- **Latency:** a 5-question check gave retrieval about 0.6 s and Gemini about 4 to 6 s, with tracing on or off. So tracing and re-ranking don't explain the jump. Gemini was about this slow in this session, but the cause is unknown, so v0 and v1 latency can't be compared fairly yet.

Prediction for run 2 (written before the run): the same scores as run 1, with q24 wrong and q37 right.

Result (`evals/results/v1_rerank20_run2.jsonl`): Correct 34/39 (0.872), Faithful 47/50 (0.940), Abstain 9/11 (0.818). Wrong: q02, q08, q15, q22, q35. Unfaithful: q01, q39, q48. Not abstained: q39, q40. Hit@5 and MRR did not move, and all 50 contexts match run 1.

- **Correct, q24 flipped to right, but this looks like a false pass:** the answer still gives only 0.6%, as in run 1. The judge's reason says the 6.0% is "implicitly understood", but it is not in the answer or the context. By hand, Correct is 33/39 in both runs (only q24 was hand-checked).
- **Abstain, q40 flipped to answered:** both runs say the number is not in the context and then give the same TAS phone line, so this looks like judge noise, not a real drop.
- **Faithful flips:** q39 is now unfaithful, which fits the doubt from run 1. q12 is now faithful. q01's new unfaithful verdict looks too strict, but it was not checked against the context.
- **Stable in both runs:** the gains on q20, q27 and q36. q37 is also right in both runs, but it was right in v0 runs 1 and 2, so that does not show re-ranking helped it.
- **q02:** still leaves out the year for April 15 in both runs, even with the gold chunk in the context. Treat it as a generation problem for Day 5.
- **Latency:** the median fell back from 6.16 s to 1.97 s with the same code, against 1.92 s for v0. So the run 1 rise was not caused by re-ranking. The mean is still higher (3.07 s against 1.93 s), with slow answers of up to 12.29 s, and those were not investigated.

Verdict: re-ranking is a real retrieval gain (Hit@5 0.795 to 0.897, repeatable). Correct rose about 3 questions by hand count, above the noise floor of about 2. The Faithful rise overlaps the v0 range, so it is not proven. q24 is still a real loss, which the Correct score in run 2 hides.

## Day 4 chunking option A: recursive splitter

Change: `RecursiveCharacterTextSplitter`, 1,000 chars, no overlap, 1,746 chunks, index `irs-bge-small-recursive-1000`. Re-ranking stays on with 20 candidates. Our PDF text has no blank lines, so it cuts at line ends, not paragraphs.

Prediction (written before the run): Hit@5 0.90, MRR 0.8, Table 2 (q15, q35) not in the top 5, q24's 6.0% in the top 5.

Retrieval-only result: Hit@5 0.897 (35/39), MRR 0.716, against 0.897 and 0.722 for v1. No Gemini calls.

- **Hit flips:** q22 and q44 are fixed. q34 and q36 are new misses, and their cause was not investigated. q36 was one of re-ranking's Correct gains.
- **Table 2:** still not in the top 5. For q15 the chunk with 619.20 is at vector rank 48, so it is not in the 20 candidates. For q35, 309.60 is not in the top 50.
- **q24:** the chunk with 6.0% is at vector rank 3, but the re-ranker puts it at 9, so it is still not in the top 5.

Verdict: no measured gain, and the target questions did not move. No full eval was run, so its effect on Correct is unknown.

## Day 4 chunking option B: junk cleanup

Change: `clean_page()` removes the print-proof header from 277 of 314 pages. Fixed 1,000-char chunks, 1,663 chunks, index `irs-bge-small-cleaned-1000`. Re-ranking stays on with 20 candidates.

Prediction (written before the run): Hit@5 0.9, MRR 0.8, Table 2 and q24's 6.0% both in the top 5.

Retrieval-only result: Hit@5 0.821 (32/39), MRR 0.635, against 0.897 and 0.722 for v1. No Gemini calls.

- **Hit flips:** q01, q17 and q34 are new misses. Their cause was not investigated; removing the header also moves the later cuts on those pages, which may be why. They may also be false misses, since no answers were generated.
- **q24:** improved. The chunk with 6.0% is at vector rank 1 and re-rank 2, so it is back in the top 5.
- **Table 2:** still missing, and worse. 619.20 (q15) and 309.60 (q35) are not in the top 50. Chunk `7:0` starts with "Table 2 / Payroll period / Add additional", while "nonresident alien" is in the text before the table, which may be why search misses it. Chunk `7:1` is in the top 5 for both questions.

Verdict: worse overall on retrieval, with one target question fixed. No full eval was run, so its effect on Correct is unknown.

## Day 4 neighbouring chunks

Change: after re-ranking, also send the chunks on each side of each top-5 chunk to the LLM (same page, window 1). `sources` stays the top 5, so Hit@5 and MRR do not change. New metric: Evidence, true if all gold quotes are in the context.

Retrieval-only result, no Gemini calls:

| Window | Hit@5 | MRR | Evidence | Median context chars | Median retrieval time, 20 questions |
|---|---|---|---|---|---|
| 0 (v1) | 0.897 | 0.722 | 0.667 (26/39) | 5,028 | 0.46 s |
| 1 | 0.897 | 0.722 | 0.897 (35/39) | 11,148 | 0.80 s |

- **Target questions:** Table 2 (q15, q35) and q24's 6.0% are now in the context.
- **Still no evidence:** q08, q10, q20, q22.

Prediction for the full eval (written before the run): Correct 35/39, Faithful 49/50, Abstain 9/11, q15 and q35 right, q24 wrong.

Result (`evals/results/v2_neighbours1.jsonl`): Correct 36/39 (0.923), Faithful 50/50 (1.000), Abstain 10/11 (0.909), mean tokens 3,357. Wrong: q02, q08, q22. Not abstained: q39.

- **Correct gains:** q15, q35 and q24. Each answer was read by hand and gives the expected values, and each gain follows from its evidence now being in the context. q24 now states 6.0%, so this pass is real, unlike v1 run 2.
- **Still wrong:** q08 and q22 have no evidence in the context. q02 has its evidence but still leaves out 2026, a generation problem for Day 5.
- **Faithful 1.000:** one run, and just above v1's 0.940 to 0.960, so not clear evidence. q39 is marked faithful, and the text it uses is in the context, but q39 should still have abstained.
- **q10:** right with no evidence found, because the answer comes from different wording ("at no cost") than the gold quote.
- **Cost:** mean tokens rose from about 1,440 to 3,357 (2.3 times). Median latency was 2.50 s, against 1.97 s for v1 run 2 and 6.16 s for v1 run 1, so latency stays too noisy for a firm comparison.

Verdict: best version so far, up 3 questions from v1 by hand count, with a clear cause for each. It is one run; repeat it for noise.

## Day 3 error analysis of v0_run3

Rank = position of the chunk containing the gold evidence in a top-50 search.

| Cause | Questions | Wrong answers |
|---|---|---|
| Retrieval, near miss (gold chunk ranks 6 to 20) | q02 (8), q22 (16), q27 (6), q36 (12 and 13) | 4 |
| Retrieval, deep miss (gold chunk below 50) | q08, q20 | 2 |
| Table chunk not retrieved, page-level false hit (below 50) | q15, q35 | 2 |
| Generation, right context but wrong conclusion | q37 | 1 |

Other failures:
- **Answer correct, hit@5 is a miss:** q01 (the evidence is split across two chunks), q03 (gold chunk at rank 7; the answer came from other pages).
- **No abstention:** q39. The answer gives the failure-to-pay rate as the failure-to-file rate. The prompt has no abstention rule.
- **Unfaithful verdicts:** q27, q37 and q39 look right. q12 and q36 changed between runs and look like judge noise. q03 is not settled.

Hand-check of `supported` verdicts: 8 random questions (q05, q06, q08, q11, q23, q26, q29, q41), seed 7. All 8 look right. This sample is small, so it does not rule out errors in the other 36. It also did not include q27-style answers.

Most frequent cause: near-miss retrieval, so Day 4 should try re-ranking first. Then look at chunking (q15, q35, q01) and hybrid search (q08). A gold chunk's rank shows that a fix is possible, not that it will work.

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

Result under the final rule: q02 incorrect on 6 of 6 verdicts. The correctness calibration did not finish: it stopped after q01 and q05 (both agree) on the free-tier limit of 500 requests per day per model. Re-run with a new API key: 10/10 agreement, 10/10 stable under the final rule.

**Prediction for v0_run3 (written before the run):** Hit@5 0.795, MRR 0.597, Correct 32/39, Faithful 47/50, Abstain 10/11.

Result: Hit@5 0.795, MRR 0.597, Correct 30/39 (0.769), Faithful 44/50 (0.880), Abstain 10/11 (0.909). Same context as run 1 on 50/50 questions.
Wrong: q02, q08, q15, q20, q22, q27, q35, q36, q37. Unfaithful: q03, q12, q27, q36, q37, q39.

- **q37 is new:** the answer has both right limits ($5,250 and $7,500) but says educational assistance is higher. Run 2's answer got this right from the same context. This is a generation failure, so not every wrong answer traces to retrieval.
- **q02 and q30:** q02 is wrong because the year is missing, and q30 is correct against the fixed golden answer, as the rule and golden changes intended.
- **Faithful range over 3 runs:** 0.880 to 0.940. q12 and q36 changed again, which fits the judge noise seen in the stability test.
- **Limit of this baseline:** run 3 is the only run under the final rules, so Correct noise comes from one run with the final rules plus the flips seen earlier.

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