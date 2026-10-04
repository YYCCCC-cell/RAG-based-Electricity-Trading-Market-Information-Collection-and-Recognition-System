# Product documentation

## Persona and job to be done

**Primary persona:** an analyst or trader at a generator, retailer or market-service company who begins each day by checking whether a public notice changes a deadline, eligible product, settlement treatment or required action.

**Job:** reduce repetitive scanning while preserving a defensible route from each alert or answer to the official notice. This is decision support, not automatic trading.

## Inputs

- Public latest notices on the Guangzhou Power Exchange Center website.
- Public market-training notices from the same website.
- Public rules and policy records indexed by the same website.
- A written labelling guide and a versioned 100-document evaluation snapshot.

Weather, fuel, carbon and green-certificate price series are outside the classifier and retrieval inputs. Official notices about certificates remain within scope.

## Outputs

- Four-way category: `transaction_action`, `rules_policy`, `results_settlement`, or `service_other`.
- Binary `market_impacting` flag with rule evidence and risk flags.
- Daily digest with source links and a priority review queue.
- Citation-bound question answering over the checked-in snapshot.
- Evaluation artefacts covering classification, retrieval, model latency and unit model cost; ingestion freshness is unmeasured.

## High-level architecture

```text
Official centre pages
        |
        v
[polite crawler] -> [raw snapshot + timestamps] -> [parser / normalization]
                                                    |                |
                                                    v                v
                                           [four-way rules]   [BM25 index]
                                                    |                |
                                                    v                v
                                           [alert + reasons]  [extractive answer]
                                                    \                /
                                                     v              v
                                              [digest + local web UI]
                                                         |
                                                         v
                                               human verification
```

Every output retains `notice_id`, publication date, source section and URL. The retrieval layer cannot cite a record that is absent from the index.

## Logic and external intelligence

The implementation uses standard-library code only. Classification is rule-based because the labelled sample is small, operational users need reason codes, and the four classes have strong domain cues. Retrieval is BM25-like lexical scoring with Chinese bigrams. The response layer extracts the best matching sentence from each retrieved notice and attaches its notice ID and URL.

An external LLM is a future, optional presentation layer. It would receive retrieved passages, preserve IDs, refuse unsupported claims and pass a citation validator. The current implementation runs without credentials or a paid service.

## Metrics targeted and reached

| Metric | Target | Development result | Interpretation |
| --- | ---: | ---: | --- |
| Market-impact recall | >=90% | 100.0% | Target met on draft labels |
| Market-impact precision | Report beside recall | 89.1% | Seven false alerts remain |
| Market-impact F1 | No original target | 94.2% | Balanced summary of alert quality |
| Four-way accuracy / macro F1 | Diagnostic | 93.0% / 93.0% | Seven service records route to rules |
| Citation hit rate@1 / @3 | >=90% @3 | 100% / 100% (10 questions) | Small, title-like test set; optimistic |
| Crawl freshness | <=30 minutes | Not measured | This is a scheduling SLA, not model latency |
| Offline cost/notice | Track | USD 0 | Excludes hosting and analyst time |

The full machine-readable result is in `outputs/metrics.json`.

The flag-everything baseline has 100% recall, 57% precision, 100 alerts and 43 false alerts. The rules have 100% recall, 89.1% precision, 64 alerts and seven false alerts on the same draft-labelled snapshot. Errors and source links are exposed in `classification.errors`.

## Deployment boundary

The public website is a static snapshot demo; queries run in the visitor's browser. The local Python demo serves the versioned dataset and supports an on-demand crawl command. No automatic schedule is installed. Answers are extracted from retrieved text; a generative LLM is not integrated. GitHub CI verifies the code but does not deploy the public website.

The rules were refined on this development set, including use of source-section and title context. These results therefore measure a transparent development baseline, not generalisation to unseen data.

## Human workflow

1. Analyst opens the dashboard and filters the alert queue.
2. Analyst reads the reason code and cited official page.
3. Analyst verifies dates, participant eligibility and any attachments.
4. Analyst records or escalates the action outside this system.
5. Incorrect classifications are relabelled and added to the error set.

## Failure handling

- Evaluation uses the checked-in snapshot; run new crawls to a separate output path. The crawler can retain title-only records after individual article failures, so a live crawl needs coverage and parse-success checks before promotion.
- Low-confidence rules add `human_review`.
- No retrieval match returns an explicit no-evidence response.
- Source URLs remain visible in the digest, UI and Q&A output.
- The offline snapshot ensures a repeatable demo if the live site is unavailable.
