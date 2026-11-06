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
| v3 | Hybrid search, BM25 + RRF, 20 from each search, 40 candidates | 0.974 | 0.776 | 0.923 | 1.000 | 0.909 | 23.81 | 3375 | Run 1; Evidence 0.949. By hand Correct is 37/39 (q31 is a judge false fail). Median latency 19.95 s, not repeated in run 2 (see Day 4 notes) |
| v3 | Same code, run 2 (noise check) | 0.974 | 0.776 | 0.949 | 1.000 | 0.909 | 3.27 | 3374 | No change to retrieval or questions; median latency 2.39 s, of which retrieval 1.07 s and Gemini 1.35 s. q31 is now correct, so the judge agrees with the hand count (see Day 4 notes) |
| v4 | Embedding swap: gemini-embedding-2, re-rank 20, no BM25 | 1.000 | 0.787 | 0.949 | 1.000 | 0.909 | 5.78 | 3390 | Run 1; Evidence 0.974. No Correct, Faithful or Abstain flips against v3 run 2. Median latency 3.93 s, of which retrieval 2.11 s and Gemini 1.34 s (see Day 4 notes) |
| v5 | Grounding rules, required citations, labelled context | 0.974 | 0.776 | 0.897 | 0.780 | 0.909 | 15.85 | 3552 | Run 1; Evidence 0.949. Most Faithful fails look like a judge problem, not reviewed by the user yet. Median latency 14.69 s, not comparable with v3 (see Day 5 notes) |
| v6 | Prompt fixes: calculate from the context, one label per bracket | 0.974 | 0.776 | 0.949 | 1.000 | 1.000 | 16.93 | 3575 | Run 1; Evidence 0.949. Faithful is 39/39 because exact refusals skip the judge; v5 on the same rule is 37/39. By hand Correct is 38/39 (q31 looks like a judge false fail). Median latency 7.39 s, not comparable (see Day 5 notes) |
| v6 | Same code, run 2 (noise check) | 0.974 | 0.776 | 0.872 | 1.000 | 0.909 | 10.24 | 3578 | Evidence 0.949. Faithful is 38/38 because exact refusals skip the judge. q04 looks like a judge false fail, not confirmed by the user. Median latency 6.20 s, of which retrieval 1.28 s and Gemini 4.89 s |

## Final results (Day 5 check)

One row per change. Two numbers (a–b) mean two runs of the same code. Latency is re-timed in one session (`evals/latency.py`); the latency column above is from each run's own day and is not comparable.

| Version | Change | Hit@5 | MRR | Evidence | Correct | Faithful | Abstain | Citations ok | Latency (s) | Tokens/q |
|---|---|---|---|---|---|---|---|---|---|---|
| v0 | Naive baseline | 0.795 | 0.597 | 22/39 | 30/39 | 44/50 | 10/11 | n/a | 1.46 | 1467 |
| v1 | + Re-ranking, 20 candidates | 0.897 | 0.722 | 26/39 | 33–34/39 | 47–48/50 | 9–10/11 | n/a | 1.60 | 1438 |
| v2 | + Neighbouring chunks | 0.897 | 0.722 | 35/39 | 36/39 | 50/50 | 10/11 | n/a | 2.54 | 3357 |
| v3 | + Hybrid search, BM25 + RRF | 0.974 | 0.776 | 37/39 | 36–37/39 | 50/50 | 10/11 | n/a | 2.63 | 3374 |
| v4 | Gemini embeddings instead of BM25 (not kept) | 1.000 | 0.787 | 38/39 | 37/39 | 50/50 | 10/11 | n/a | 3.62 | 3390 |
| v5 | v3 + grounding, citations, labels | 0.974 | 0.776 | 37/39 | 35/39 | 37/39 | 10/11 | 35/39 | 2.77 | 3552 |
| v6 (final) | + Calculate rule, one label per bracket | 0.974 | 0.776 | 37/39 | 34–37/39 | 38/38–39/39 | 10–11/11 | 38/38–38/39 | 2.77 | 3575 |

- **Faithful from v5 on** leaves out exact refusals, so it has fewer rows. v5's Faithful is shown under that rule.
- **Citations ok** counts answers that aren't exact refusals, with at least one citation and all of them valid. v0 to v4 had no citation rule.
- **Correct by the judge.** By hand: v1 33/39 and v3 37/39; q31 in v6 run 1 and q04 in v6 run 2 look like judge false fails.
- **Known costs in v6:** q22 (evidence not retrieved), q44 (false refusal, about 4 in 5), q39 (answers about 1 in 5).

## Day 5 grounding and citations

Change: add `[source, page N]` labels to the context, and rules to the prompt: use only the context, cite each claim, copy dates and amounts exactly, and add a year only when the context makes it clear.

Prediction (written before the run): Correct 39/39, Faithful 50/50, Abstain 10/11.

Result, `evals/results/v5_grounding.jsonl`, against v3 run 2: Correct 35/39, Faithful 39/50, Abstain 10/11. Retrieval has no flips.

**Correct flips**
- q02 is fixed: the answer now gives April 15, 2026.
- q34 is a real regression: both limits are in the context, but the model refuses because the increase isn't stated. Rule 1 doesn't allow a calculation.
- q04 and q44 look like judge false fails, not yet checked by the user. q04 adds a backup withholding exception supported by the context (rule 2 allows extra text). q44 says digital assets aren't accepted, and the question didn't ask about U.S. dollars.
- q22 stays wrong: its evidence isn't in the context, so the refusal is honest. This is a retrieval problem.

If q04 and q44 are confirmed, Correct by hand is 37/39, the same count as v3 run 2, with q34 replacing q02.

**Faithful flips (11)**
- `judge_faithfulness()` receives the context and the answer, but not the question. For 8 unanswerable refusals (q40, q41, q43, q46, q47, q48, q49, q50) and q22, it can't tell what the refusal refers to, and several reasons say no question was asked.
- q01 has the same cause: "complete Step 2" looks unconditional when the judge can't see "I have two jobs".
- q34 is a real failure: the refusal contradicts the context.

If the other 10 are confirmed as judge problems, Faithful by hand is 49/50.

**Retest: giving the faithfulness judge the question.** Day 3 tried this and removed it. Pass mark: at least 7/8 agreement and 8/8 stable, the level of the accepted judge. Result: agreement 5/8, stable 7/8, so it failed. q15 (all 3 runs): the judge marks the answer down for not fully answering the question, which isn't its job. q27 (all 3 runs): too lenient, the known limitation. q39: flips in 1 of 3 runs. The change was undone.

**Decision: exact refusals skip the Faithful judge.** A refusal makes no factual claim, and Abstain and Correct still score it. A refusal with other claims in it, like q34's, is still judged. Applied to v5's saved verdicts, with no new calls: Faithful 37/39 (0.949), with 11 refusals left out (q22, q40, q41, q42, q43, q45, q46, q47, q48, q49, q50). Fails: q34 (real) and q01 (looks like a judge false fail). From now on Faithful covers fewer than 50 answers, so compare it with earlier rows with care.

**v6 prompt fixes.** Change: add "calculate it" for numbers in the context (q34) and "Cite one label per bracket" (merged citations).

Prediction (written before the run): Correct 38/39, Faithful 39/39 on questions judged in both v5 and v6, Abstain 10/11, q34 fixed.

Result, `evals/results/v6_prompt_fixes.jsonl`: Correct 37/39, Faithful 39/39 (11 exact refusals left out, the same 11 as v5), Abstain 11/11, q34 fixed. Retrieval has no flips. The run took 3 attempts because of Gemini 503 errors, using the resume feature.

- **Correct, against v5:** q34 is fixed by the calculation rule. q44 now mentions U.S. dollars. q04 has nearly the same answer as v5 and now passes, so its v5 fail was judge noise. q31 is new: it gives both default rates, but the judge wants details the question didn't ask for. That looks like a judge false fail, as in v3 run 1. By hand Correct is 38/39, and only q22 is wrong (its evidence isn't in the context).
- **Abstain:** q39 now refuses and explains why, with citations. No rule was aimed at q39, and one run can't show this will hold, so check it again before task 2 closes.
- **Citations:** 79 of 84 exactly match a label, up from 62 of 72 in v5. Left: 3 merged citations (q02, q03, q33) and 2 without the word "page" (q14). Task 3's check must handle these.
- **Latency:** median 7.39 s, of which retrieval 1.52 s and Gemini 5.21 s. Mean 16.93 s. Gemini speed changed a lot during the run, so this isn't a fair measure of the prompt. Mean tokens 3,575.

One run only; the noise floor on Correct is about 2 questions.

**q39 repeat, v6 prompt.** Prediction (written before the run): refuses 2 to 3 times out of 5. Result: refuses 4 out of 5, so it's better than v3 but not reliable. All 4 refusals also mention the general penalty rules, so none is the exact refusal text and Faithful still judges them: 2 supported, 2 not_supported on very similar answers. Not saved to `evals/results/`.

**Score cutoff check, no Gemini calls.** Could a low top re-rank score trigger a refusal? From v6's saved scores: cutoff 0 catches 5/11 unanswerable and wrongly refuses 2/39 answerable; cutoff 2 catches 8/11 and refuses 3/39; cutoff 3 catches 11/11 and refuses 7/39. q39 scores 2.91, the highest of the unanswerable group, because related penalty text exists. The model already refused the other 10 in v6, so a cutoff would add wrong refusals. The lowest useful cutoff for q39 is 2.92, which catches 11/11 but also refuses 4/39 answerable questions that v6 answers correctly (q12, q29, q37, q44). It would also sit only 0.02 below q22's 2.93, so it's fitted to this golden set. These cutoffs are from the golden set, so they would look better here than on new questions.

Decision (task 2): no score cutoff and no rule written for q39. Abstention stays in the prompt, which goes against PLAN.md's suggestion of using retrieval scores. Known risk: q39-style questions, where related text exists but not the answer, may still get answered about 1 time in 5. A repeat run checks that Abstain and Correct hold.

**v6 run 2 (noise check).** No code change. Prediction (written before the run): the same as run 1, Correct 37/39, Faithful 39/39, Abstain 11/11.

Result, `evals/results/v6_prompt_fixes_run2.jsonl`: Correct 34/39 against 37/39, Faithful 38/38 on the questions judged in both, Abstain 10/11 against 11/11. Hit@5, MRR and Evidence have no flips. Median latency 6.20 s (retrieval 1.28 s, Gemini 4.89 s). Citations: 82/85 exact, 3 merged (q33, q35 twice). Gemini returned 429 (quota) after 45 questions, so q46 to q50 were run later on a different API key, with the same model and code.

- **Flips:** q21 dropped the income limits and q44 wrongly refused. q39 answered instead of refusing, the known 1-in-5 risk. q04 looks like a judge false fail: its reason is the backup withholding note, which run 1 also had and passed. Not confirmed by the user.
- **q21 and q44 repeat, 5 times each.** Prediction (written before the run): each is correct 4 of 5 times, give or take 1. Result: q21 5/5 by the judge and q44 1/5, with Evidence true on all 10.
  - **q21:** 4 of 5 answers give the income limits. Try 4 leaves them out and passes, while nearly the same answer failed in run 2, so the judge is inconsistent on this omission. Whether the limits are required is not decided.
  - **q44:** 3 exact refusals, 1 refusal that also states the rule and says the context "does not specifically mention Bitcoin", and 1 correct answer. Run 1's pass was the less common result. v3 had no grounding rules and got q44 right, so this looks like a side effect of grounding: the model doesn't connect Bitcoin to "digital assets".
- **Noise:** only 22 of 50 answers are word-for-word the same. Correct moved by 3 with no code change, so a difference of 2 or 3 between versions is not enough on its own to show a real change. This includes v5 (35/39) to v6 (37/39), but q34's fix is a specific change that held in run 2.

**Specific-case rule.** Change: rule 1 adds "If the question asks about a specific case of something the context covers, apply what the context says", for q44's false refusals. Repeat of q44 and q39, 5 times each. Prediction (written before the run): q44 correct 4 of 5, q39 refuses 4 of 5. Result: q44 correct 3 of 5 (was 1 of 5), q39 refuses 0 of 5 (was 4 of 5), by the judges. q39 now applies p15's general penalty text to an individual return, which is what the rule asks for, so the rule trades q39's refusal for part of q44's gain. Only 5 tries each, but q39's change is large. Decision: undone. A false refusal is safer than a confident answer that goes beyond the source, so q44 stays a known cost of strict grounding.

**Citation check (flag only), on the saved v6 answers, no Gemini calls.** `evals/check_citations.py` splits merged brackets and matches each citation against that question's context labels. Exact refusals are left out. Prediction (written before the run): 4 to 5 invalid citations in each run. Result: run 1 has 85 valid and 2 invalid, both q14 (`[p15.pdf, 21]`, `[p15b.pdf, 32]`, missing the word "page"); 38 of 39 answers pass. Run 2 has 88 valid and 0 invalid; 38 of 38 answers pass. No full re-run is needed, because the check doesn't change the answers. It shows that each cited source was sent to the model, not that the page supports the claim.

**Latency re-timed in one session (task 4).** `evals/latency.py`, versions taking turns on each question. Prediction (written before the run): v6's retrieval is the slowest median (v6 retrieves as v3), and the v5–v6 prompt takes more Gemini time than v2–v4.

Result, `evals/results/latency_retrieval.jsonl` and `latency_gemini.jsonl`:

| Version | Retrieval median (p95) | Gemini median (p95) | Total, sum of medians | Tokens/q |
|---|---|---|---|---|
| v0 | 0.36 s (0.84) | 1.10 s (31.62) | 1.46 s | 1467 |
| v1 | 0.50 s (0.80) | 1.10 s, as v0 | 1.60 s | 1438 |
| v2 | 1.11 s (1.21) | 1.43 s (1.64) | 2.54 s | 3357 |
| v3 | 1.20 s (4.40) | 1.43 s, as v2 | 2.63 s | 3374 |
| v4 | 2.19 s (4.63) | 1.43 s, as v2 | 3.62 s | 3390 |
| v5, v6 | 1.20 s, as v3 | 1.57 s (2.53) | 2.77 s | 3575 |

- **Retrieval:** v4 is the slowest, not v3 and v6: the Gemini query embedding is a network call, while bge runs locally. Neighbours (v2) add the most to retrieval, 0.61 s, for the extra Pinecone fetch.
- **Gemini:** the v5–v6 prompt is slower than v2–v4 on 7 of 10 questions, by 0.14 s at the median. The 5 to 13 s Gemini times in the saved v5 and v6 runs were server load, not the prompt. One v0 call took 22.3 s (q22), the same kind of outlier.
- **Limits:** the totals add two medians, which is close to but not the same as the median of totals. 10 questions for the Gemini step is a small sample. Tokens/q is from the saved runs.
- **Cost:** $0 on the free tier. Tokens/q is the cost measure: it more than doubles at v2 (neighbours), and the Day 5 prompt adds about 200.

**Day 5 check: biggest improvement per extra second of latency.** User's first answer: the Day 5 prompt, together with leaving exact refusals out of the Faithful judge. Changed after noting that the Faithful change is in the measuring, not the system. Final answer: hybrid search (v3), because BM25 finds chunks that vector search left out, since their meaning wasn't close enough to the question's.

**Citations:** 62 of 72 cited brackets exactly match a context label. 9 merge several sources or pages, for example `[p15t.pdf, page 6, p15t.pdf, page 7]`. 1 is not a real source (q04, `[p6, page 6]`). q31 answers with no citation. Task 3's check must handle these.

**Abstention:** still 10/11. q39 still answers. Refusals on answerable questions: q22 and q34.

**Latency:** median 14.69 s, of which retrieval 1.28 s and Gemini 13.38 s. Not comparable with v3 run 2. Just before this run, 3 pairs of calls on the same context gave a median of 11.75 s with the old prompt and 14.84 s with the new one, so Gemini was slow with either prompt. Three pairs are too few to measure the new prompt's own cost. Mean tokens rose from 3,374 to 3,552.

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

## Day 4 hybrid search

Change: local BM25 + vector search, merged with Reciprocal Rank Fusion (k = 60). N chunks come from each search, fusion keeps the best 20, then re-ranking and neighbours run as in v2.

Prediction (written before the run): Hit@5 0.95, MRR 0.85, Evidence 37/39, q08 and q22 fixed.

Retrieval-only result, no Gemini calls:

| N | Hit@5 | MRR | Evidence | Hit gains | Hit losses |
|---|---|---|---|---|---|
| 0 (v2) | 0.897 | 0.722 | 0.897 (35/39) | | |
| 20 | 0.949 | 0.742 | 0.923 (36/39) | q08, q20, q22 | q36 |
| 50 | 0.949 | 0.744 | 0.897 (35/39) | q08, q22, q44 | q36 |

- **q08:** fixed. Its gold chunk `fw4s.pdf:1:0` is at vector rank 57 and BM25 rank 1.
- **q22:** Hit@5 only. The hit comes from `fw4.pdf:4:0`. The answer is in `4:2`, which the re-ranker puts at position 13, so the evidence is still missing.
- **q36:** a real loss. Its gold chunks are at vector ranks 12 and 13 and BM25 ranks 61 and 41. With N = 20 they appear in one list only, score less than the top BM25 chunks, and are cut from the 20 before re-ranking. With N = 50, `fw4.pdf:1:0` is still cut.
- **q20:** N = 20 finds `p15b.pdf:6:1` (BM25 rank 5, then re-rank position 1). With N = 50 it is cut, because more chunks appear in both lists and fill the 20. q20 was already right in v2, from another page.
- **MRR:** q01 and q05 fell slightly with both N values.

Verdict: not decided. Both values lose q36, and the cut to 20 looks like the cause. Not yet tested with the full eval.

Prediction for N = 20 with 40 candidates, so nothing is cut (written before the run): Hit@5 0.95, MRR 0.85, Evidence 37/39, q36 comes back.

Result, retrieval-only: Hit@5 0.974 (38/39), MRR 0.776, Evidence 0.949 (37/39). Median retrieval time over 20 questions: 0.82 s for v2, 0.82 s for N = 20 with 20 candidates, 0.91 s for N = 20 with 40 candidates.

- **Cause confirmed:** q36 is back, so the cut to 20 caused its loss. q08 and q20 stay fixed.
- **No evidence:** q10 (right in v2, from different wording) and q22 (a page-level false hit; the answer chunk is not in the top 5).
- **Miss:** q44, though its evidence text is in the context from other pages.
- **Limit:** N and the candidate count were chosen on the same 39 questions we report, so these numbers may be slightly optimistic.

Verdict: best retrieval so far. Not yet tested with the full eval.

Prediction for the full eval (written before the run): Correct 37/39, Faithful 50/50, Abstain 11/11, q02, q08 and q22 right.

Result (`evals/results/v3_hybrid20.jsonl`): Correct 36/39 (0.923), Faithful 50/50 (1.000), Abstain 10/11 (0.909), mean tokens 3,375. Wrong: q02, q22, q31. Not abstained: q39.

- **Correct gain:** q08 now names the third-party payer, and hybrid search brought in its gold chunk.
- **q31 flip is a judge false fail:** the answer gives the same 10% and 20% as v2. The question asks for the default rates, so the other details are optional (rule in NOTES.md). Re-judging the saved answer gave correct 3 of 3. By hand, Correct is 37/39.
- **Still wrong:** q22 has no evidence in the context, and the answer says the worksheet has no such entry. q02 has its evidence but leaves out 2026, a generation problem for Day 5.
- **q36:** right, so the loss seen with 20 candidates did not come back.
- **q39:** still doesn't abstain, a generation problem for Day 5.
- **Latency:** median 19.95 s and maximum 155 s, against 2.50 s and 14 s for v2. Separate timing puts retrieval at about 1 s, so most of it is probably not retrieval. In 2 spot checks Gemini took 1.3 s and 9.6 s. The new Gemini key from another account changed in the same run, so the cause is not confirmed. Retries on rate limits are possible but not checked.

Verdict: best version so far, up 1 question from v2 by hand count (37/39 against 36/39), from q08. It is one run; repeat it, also to check latency.

Prediction for run 2 (written before the run): Correct 37/39, Faithful 50/50, Abstain 10/11, most of the time is Gemini.

Result (`evals/results/v3_hybrid20_run2.jsonl`): Correct 37/39 (0.949), Faithful 50/50 (1.000), Abstain 10/11 (0.909), mean tokens 3,374. Wrong: q02, q22. Not abstained: q39.

- **Flips:** only q31, from wrong to correct, which supports the judge false fail in run 1. Hit@5, MRR and Evidence did not move.
- **q08:** right in both runs, so v3's gain over v2 is repeatable. v2 itself has not been repeated.
- **Latency:** median total 2.39 s, retrieval 1.07 s, Gemini 1.35 s. Gemini is 65% of total time across all questions. The slowest question (q32, 30.2 s) spent 29.1 s in Gemini.
- **Run 1's 19.95 s:** the same retrieval code now gives 2.39 s, so hybrid search is not the cause. Run 1 did not save a split, so the cause stays unconfirmed; temporary Gemini slowness or retries are possible.

Verdict: v3 is the best version, Correct 37/39 in both runs by hand. The remaining failures are q22 (the answer chunk is not retrieved in the top 5), and q02 and q39 (generation, Day 5).

## Day 4 check: which change surprised you, and why?

Answer: the recursive splitter did not perform as expected, fixed chunking did better than expected, cleaning the junk brought no significant improvement, and Gemini did better without BM25.

Follow-up on what the data supports:
- Recursive tied v1 on Hit@5 (0.897) and was just below on MRR (0.716 against 0.722). The worst retrieval result was junk cleanup before cutting on v1 (0.821, 0.635). Our PDF text has no blank lines, so recursive could only cut at line ends, which makes this a weak test of structure-aware chunking.
- A better embedding model raised retrieval (vector only: Hit@5 0.795 to 0.846, MRR 0.597 to 0.729), but Correct stayed 37/39. One model pair on 39 questions doesn't show that bigger models keep helping.

## Day 4 junk cleanup, retest on v3

Change: remove the print-proof header, either before cutting (every later cut on the page moves, 1,663 chunks) or after cutting (cuts stay, 1,714 chunks, 280 changed). Everything else as in v3. Each has its own bge index. This separates the header's effect from the moved cuts, which option B mixed together.

Prediction for retrieval-only (written before the run):
- Clean after: Hit@5 0.9, MRR 0.7, Evidence 37/39, q22 gets its evidence.
- Clean before: Hit@5 0.821, MRR 0.635, Evidence 34/39, q22 does not.

Rule set before the run: keep cleanup only if Hit@5, MRR and Evidence aren't worse and no question is lost.

Retrieval-only result, no Gemini calls:

| Version | Chunks | Hit@5 | MRR | Evidence | Questions with a changed MRR | Hit or Evidence changes against v3 |
|---|---|---|---|---|---|---|
| v3, no cleanup | 1,714 | 0.974 | 0.776 | 37/39 | | |
| Clean after cutting | 1,714 | 0.949 | 0.763 | 36/39 | 3 | q01 lost |
| Clean before cutting | 1,663 | 0.897 | 0.694 | 34/39 | 15 | q01, q17, q34 lost; q02 loses evidence; q10 gains evidence |

- **Moved cuts did most of the damage:** q17, q34 and q02 change only when the cuts move, and most MRR changes appear only then. So most of option B's losses came from moved cuts, not from removing the junk.
- **q01:** its gold chunk `fw4.pdf:1:2` has no header, and its re-rank score is unchanged (2.32). Another chunk, `p15t.pdf:4:0`, lost its header and rose from 1.62 to 3.60, pushing the gold chunk from position 5 to 6. So cleanup made a competing chunk score higher. q01 was right in v0 even as a miss, so its answer may stay right; not tested.
- **q22:** still no evidence in either version.

Verdict: cleanup is not kept, under the rule set before the run. Removing the junk itself did little harm (one question, by one position) and brought no gain. No full eval was run, so its effect on Correct is unknown.

## Day 4 embedding swap

Change: `gemini-embedding-2` (3,072 dimensions) replaces bge-small in vector search, with its own index `irs-gemini-embedding-2`. Same 1,714 chunks. BM25, RRF, re-ranking and neighbours stay as in v3.

Prediction for retrieval-only (written before the run): Hit@5 0.974, MRR 0.82, Evidence 37/39, q22 hit with evidence.

Indexing: 1,714 vectors, every chunk checked present with identical text. It hit three free-tier limits: 100 texts per minute, 30,000 tokens per minute and 1,000 texts per day. A second key was used to finish it the same day.

Retrieval-only result, neighbours on (window 1) in every row, no answer or judge calls:

| Search setup | bge Hit@5 | bge MRR | bge Evidence | Gemini Hit@5 | Gemini MRR | Gemini Evidence |
|---|---|---|---|---|---|---|
| Vector only | 0.795 | 0.597 | 30/39 | 0.846 | 0.729 | 32/39 |
| Vector + re-rank 20 | 0.897 | 0.722 | 35/39 (v2) | **1.000** | **0.787** | **38/39** |
| Hybrid + re-rank 40 | 0.974 | 0.776 | 37/39 (v3) | 0.974 | 0.768 | 37/39 |

- **The planned swap (Gemini inside v3's setup):** no gain. Only q12 and q21 moved, in MRR.
- **BM25 masked the model difference:** Gemini is better without BM25, and adding BM25 lowers it. bge needs BM25 to find q08 and q20; Gemini finds them with vector search.
- **Gemini + re-rank 20 against v3:** q10 gains evidence, q44 becomes a hit, q12 and q01 rise in MRR, q21 falls.
- **q22:** still no evidence in any setup. The hit comes from `fw4.pdf:4:0`, and the answer is in `4:2`.
- **Cost:** median retrieval was 2.16 s to 2.91 s with Gemini (timed on one run each, so noisy), against 1.07 s for v3. Every question needs an API call, and the free tier allows 1,000 per day. Chunks also go to Google.
- **Limit:** setups were compared on the same 39 questions, and one question is about 2.6 points.

Verdict: not decided. Gemini + re-rank 20 is the best retrieval so far, but q02 (generation) and q22 stay wrong, and q10 and q44 were already right, so Correct may not rise. No full eval yet.

Prediction for the full eval on Gemini + re-rank 20 (written before the run): Correct 38/39, Faithful 50/50, Abstain 10/11, median latency 3 s, q02 wrong, q22 a false hit.

Result (`evals/results/v4_gemini_rerank20.jsonl`): Correct 37/39 (0.949), Faithful 50/50 (1.000), Abstain 10/11 (0.909), mean tokens 3,390. Wrong: q02, q22. Not abstained: q39. The run stopped at question 12 on the daily limit of 500 answer-model requests and continued after the reset, with the same settings.

- **No flips against v3 run 2** on Correct, Faithful or Abstain. Better retrieval did not change any answer's verdict: q10 and q44 were already right, and q22 still lacks its evidence.
- **q22:** the answer says the worksheet has no state and local tax line, because `fw4.pdf:4:2` is not in the context.
- **Latency:** median 3.93 s against 2.39 s for v3 run 2. Retrieval is 2.11 s against 1.07 s, and the Gemini answer step is about the same (1.34 s against 1.35 s).

Verdict: no measured gain in answers, at higher latency, with an API call per question, a daily limit and all chunks sent to Google. Decision: keep v3 (bge + hybrid) as the default. It is one run, and the Gemini index stays for later comparisons.

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