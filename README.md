# RAG-based Electricity Trading Market Information Collection and Recognition System

A system for collecting public electricity-market notices, sorting them into operational categories, and retrieving relevant source material for analysts. It covers notices and rules indexed by the Guangzhou Power Exchange Center.

The current implementation combines rule-based classification, BM25 retrieval and extractive answers with source citations. It provides the retrieval baseline for a RAG workflow; generative language-model integration is not included in this version.

## Features

- Collect public notice titles, dates, text and source URLs through an on-demand crawler.
- Classify notices as transaction actions, rules and policies, results and settlement, or other services.
- Flag potentially market-impacting notices and show the rules behind each decision.
- Search the notice collection and return excerpts linked to the original sources.
- Produce a digest and reproduce classification and retrieval metrics from the included snapshot.

The demo uses a fixed collection of 100 records. It does not refresh automatically, and the 30-minute ingestion target has not been measured. Official notices and attachments remain the basis for operational decisions.

## Run locally

Python 3.10 or later is required. The application uses the Python standard library and needs no API key.

From the repository root:

```bash
python3 app.py
```

Open <http://127.0.0.1:8765>. Press `Ctrl+C` to stop the server. On Windows, use `py` if `python3` is unavailable.

Other commands:

```bash
# Classify the snapshot and produce the digest
python3 app.py run

# Recompute the evaluation results
python3 app.py evaluate

# Retrieve cited excerpts
python3 app.py ask "最近有哪些绿色电力交易安排？"

# Fetch new notices separately from the evaluation snapshot
python3 app.py crawl --limit 100 --output tmp/live_notices.csv

# Check the repository and saved results
python3 scripts/check_repository.py
```

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
.github/workflows/     Continuous integration
```

## Tests and static build

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/check_repository.py
PYTHONPATH=src python3 scripts/build_static_site.py
```

On macOS/Linux, `make ci` runs tests and validates the saved results. GitHub Actions runs these checks on pushes and pull requests. It does not deploy the public website.

See [Reproducibility](docs/REPRODUCIBILITY.md) for Windows commands, expected outputs and instructions for reviewing labels.

## Scope and limitations

The crawler reads public pages and metadata. It does not parse every attachment or QR-linked document. The retriever returns source excerpts rather than generated explanations. Users should verify dates, participant eligibility and later corrections at the official source before acting. The application does not submit bids or approve settlements.

Maintainer: Yang Yichen.
