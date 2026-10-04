# Evaluation explainer

## Classification

`market_radar.evaluation.evaluate_classification` recomputes a four-by-four confusion matrix from the checked-in labels. It reports per-class precision, recall and F1, overall four-way accuracy, macro F1, and binary precision/recall/F1/specificity for `market_impacting`. Alert volume per 100 notices makes review burden visible.

Why both precision and recall matter: recall penalizes missed market-impact notices; precision penalizes flooding the desk with false alerts. Reporting recall alone would allow the trivial “flag everything” system to score 100%.

| On the same 100 draft-labelled records | Flag everything | Rules |
| --- | ---: | ---: |
| Recall | 100.0% | 100.0% |
| Precision | 57.0% | 89.1% |
| F1 | 72.6% | 94.2% |
| Alerts needing review | 100 | 64 |
| False alerts | 43 | 7 |

The evaluator computes this baseline, rather than hard-coding it. Each mismatch is included in `classification.errors` with its ID, source URL, gold/predicted values and matching rules. This is an auditable development error set, not an untouched test set. The seven observed errors should inform a future experiment, not be relabelled merely to increase the score.

## Retrieval and citations

Ten versioned questions in `data/evals/questions.jsonl` name one or more relevant notice IDs. The evaluator builds the same BM25 index used by the demo, retrieves three records and reports hit rate@1, hit rate@3 and mean reciprocal rank. This tests whether the cited evidence is retrieved; it does not prove that a free-form generative answer is factually complete.

The questions are small and close to notice wording, so the perfect hit rate is an optimistic development result. A final study should add paraphrases, unanswerable questions, conflicting dates and attachment-only answers.

## Freshness

The 30-minute objective is defined as time from a notice becoming observable on the source to successful ingestion. It is not classification latency. The offline snapshot cannot measure that end-to-end clock, so the metric is correctly reported as “not measured.” Production measurement needs a scheduler log containing first-seen, fetch-success and parse-success timestamps.

## Cost per notice

The rules plus BM25 path has no variable model charge. An optional LLM scenario is calculated from explicit input/output token and per-million-token assumptions. It is a scenario, not a current vendor quote, and excludes compute, storage and analyst review.

The formula is `(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`. With 900 input tokens, 120 output tokens, and hypothetical rates of USD 0.15 and USD 0.60, it yields USD 0.000207 per notice. Inputs are saved under `cost.scenario_inputs`. Doubling both token counts doubles this cost.

For a transparent human-review scenario, assume USD 30/hour. At 0.5, 1 or 2 minutes per alert, reviewing 64 alerts costs USD 16, 32 or 64; reviewing 100 costs USD 25, 50 or 100. The corresponding differences of USD 9, 18 or 36 are assumptions-based illustrations. No timed analyst study, profit uplift or return on investment has been measured. Hosting, maintenance and source-access costs remain unmeasured.

## Reproduction

```bash
python3 -m pip install -e .
python3 -m market_radar.cli evaluate
```

The command rewrites `outputs/metrics.json`; no internet connection or API key is required.
