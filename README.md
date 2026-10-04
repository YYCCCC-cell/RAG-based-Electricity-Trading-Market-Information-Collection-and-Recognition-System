# RAG-based Electricity Trading Market Information Collection and Recognition System

A system for collecting public electricity-market notices, sorting them into operational categories, and retrieving relevant source material for analysts. It covers notices and rules indexed by the Guangzhou Power Exchange Center.

The current implementation combines rule-based classification, BM25 retrieval and extractive answers with source citations. It provides the retrieval baseline for a RAG workflow; generative language-model integration is not included in this version.

[Open the live website](https://yycccc-cell.github.io/RAG-based-Electricity-Trading-Market-Information-Collection-and-Recognition-System/) · [System documentation](docs/PRODUCT_DOCUMENTATION.md) · [Deployment guide](docs/DEPLOYMENT.md) · [Evaluation](docs/EVALS.md)

## Try the live website

The public application is hosted on GitHub Pages. Visitors need only a web browser: no installation, Python service or API key is required, and the maintainer's computer does not need to stay running.

1. Open the live website and browse the 100-notice snapshot.
2. Filter the queue by category and inspect the market-impact flags and matching rules.
3. Ask a question such as `最近有哪些绿色电力交易安排？`.
4. Open the cited official notice to verify dates, eligibility and attachments before taking action.

This is a **fixed-snapshot demonstration**, not a live market feed. Classification results are computed during the build; public-site retrieval and extractive answers run in the visitor's browser. Publishing the site does not schedule new crawls or enable a generative language model.

## Features

- Collect public notice titles, dates, text and source URLs through an on-demand Python crawler.
- Classify notices as transaction actions, rules and policies, results and settlement, or other services.
- Flag potentially market-impacting notices and show the rules behind each decision.
- Search the notice collection and return excerpts linked to the original sources.
- Produce a digest and reproduce classification and retrieval metrics from the included snapshot.

The demo uses a fixed collection of 100 records. It does not refresh automatically, and the 30-minute ingestion target has not been measured. Official notices and attachments remain the basis for operational decisions.

## Public website and local tools

| Capability | Public website | Local Python tools |
| --- | --- | --- |
| Browse and filter the snapshot | Yes | Yes, through the local web interface |
| Retrieve excerpts with source links | Browser-side JavaScript | Python retrieval engine |
| Classify notices and generate a digest | Displays precomputed classifications | Recomputes classifications and writes a digest |
| Fetch new official notices | No | On-demand crawl command |
| Reproduce evaluation results | See the repository results | Run the evaluator and validation scripts |

The website and local tools use the same versioned records. The reported retrieval metrics below are produced by the Python evaluator; they are not a separate browser-performance benchmark.

## Evaluation

The included snapshot contains 44 latest notices, 36 market-training records and 20 rules or policy records. These sections provide different types of examples; their proportions do not represent the full source archive.

| Metric | Result |
| --- | ---: |
| Four-way classification accuracy | 93.0% |
| Macro F1 | 93.0% |
| Market-impact precision | 89.1% |
| Market-impact recall | 100.0% |
| Market-impact F1 | 94.2% |
| Retrieval hit rate at rank 1 / top 3 | 100% / 100% on 10 questions |

Flagging every notice produces the same recall but only 57% precision and 43 false alerts. The rules produce seven false alerts and a review queue of 64 notices. Individual errors and source links appear in `outputs/metrics.json` under `classification.errors`.

Labels are marked `development_draft` and require author review. The rules were refined on this collection, and the retrieval questions are close to source titles. These scores describe development-set behaviour, not performance on an independent test set. Label provenance and review procedures are documented in the [Data Card](docs/DATA_CARD.md) and [labelling guide](docs/LABELING_GUIDE.md).

## Repository structure

```text
app.py                 Application entry point
src/market_radar/       Crawler, classifier, retrieval, evaluation and HTTP server
web/                   Browser interface source
dist/                  Static demo and public snapshot
data/raw/              Collected notice snapshot
data/labels/           Category and market-impact labels
data/evals/            Retrieval questions and relevant notice IDs
outputs/               Predictions, digest and evaluation results
scripts/               Data preparation, static build and validation
tests/                 Classification, retrieval and evaluation tests
docs/                  System, data, evaluation and reproduction documentation
.github/workflows/     CI checks and GitHub Pages deployment
```

## Tests and static build

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/build_static_site.py
python3 scripts/check_repository.py
```

On macOS/Linux, `make ci` runs tests and validates the saved results. After editing `web/`, run `make site` first so that the checked-in `dist/` assets match their source.

## Deployment and ongoing updates

Two GitHub Actions workflows have different responsibilities:

- **CI** (`.github/workflows/ci.yml`) tests the project and checks saved and regenerated results on pushes and pull requests.
- **Deploy website** (`.github/workflows/pages.yml`) tests the default-branch source, builds and validates `dist/`, and deploys it to GitHub Pages. A successful push to the current default branch, `main`, starts this workflow. It can also be started manually on that branch.

To update the public application, edit the source files, rebuild and validate locally, then commit the changes to `main`. Wait for the latest **Deploy website** run to complete before checking the live URL. Changes on other branches are not published by this workflow. A README-only edit changes the repository documentation; it does not change the website's interface.

For interface changes, edit `web/`, not only `dist/`: the deployment build replaces the generated assets from `web/`. For data or rule changes, also regenerate predictions and metrics, review the results, rebuild the static site and update any affected numbers in the documentation. Keep the evaluation snapshot separate from exploratory live crawls.

See [Deployment and maintenance](docs/DEPLOYMENT.md) for the full update procedure, required files and troubleshooting. There is no scheduled crawl or persistent Python backend on GitHub Pages.

See [Reproducibility](docs/REPRODUCIBILITY.md) for Windows commands, expected outputs and instructions for reviewing labels.

## Scope and limitations

The crawler reads public pages and metadata. It does not parse every attachment or QR-linked document. The retriever returns source excerpts rather than generated explanations. Users should verify dates, participant eligibility and later corrections at the official source before acting. The application does not submit bids or approve settlements.


