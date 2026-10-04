# Reproducibility

## Requirements

Use Python 3.10 or later and run commands from the repository root. The application, evaluation and tests use the standard library. The checked-in snapshot runs offline; only live crawling and opening official source links require a network connection.

## Verify the saved results

```bash
python3 scripts/check_repository.py
```

This checks unique notice IDs and URLs, raw/labelled snapshot alignment, valid label values, saved metrics against a fresh computation, static data without gold labels, and agreement between `web/` and `dist/`. Wall-clock latency fields are excluded from exact comparison because they vary by machine.

The expected results are 100 records, 57 true positives, seven false positives, 36 true negatives and zero false negatives. Four-way accuracy is 0.930. Market-impact precision, recall and F1 are 0.891, 1.000 and 0.942 respectively. Ten retrieval questions have hit@1 and hit@3 of 1.000. Development label status remains visible in the result file.

Both `.github/workflows/ci.yml` and `.github/workflows/pages.yml` belong in the source checkout. The repository validator explicitly requires `ci.yml`; the Pages workflow needs all three source files under `web/` to build successfully.

## Recompute outputs

```bash
python3 app.py run
python3 app.py evaluate
python3 app.py ask "最近有哪些绿色电力交易安排？"
```

The commands write `outputs/predictions.csv`, `outputs/daily_digest.md` and `outputs/metrics.json`. The digest date and execution timings may change. Notice classifications, confusion counts and retrieved IDs should match the checked-in results.

## Run the tests

macOS/Linux:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
py -m unittest discover -s tests -v
```

An editable install is optional: `python3 -m pip install -e .` makes the `power-notice-radar` command available. The existing package and command names are retained for compatibility; the repository title does not affect execution.

## Build the browser-only demo

```bash
PYTHONPATH=src python3 scripts/build_static_site.py
python3 scripts/check_repository.py
python3 -m http.server 8000 --directory dist
```

Open <http://127.0.0.1:8000>. On Windows, set `$env:PYTHONPATH = "src"` first and replace `python3` with `py` if necessary. Use an HTTP server rather than opening `dist/index.html` directly, because the browser must fetch `notices.json`.

Commit the generated `dist/` files together with the corresponding `web/` or data changes. `CI` checks saved files before regeneration, so uploading only an edited `web/` file can make that workflow fail on an asset mismatch even when the Pages build succeeds.

## Verify the public deployment

The [public application](https://yycccc-cell.github.io/RAG-based-Electricity-Trading-Market-Information-Collection-and-Recognition-System/) uses the static files built by `.github/workflows/pages.yml`. In the repository's Actions tab, inspect the latest `Deploy website` run for the intended commit and confirm that both `build` and `deploy` succeeded.

The separate `CI` workflow validates saved files before regenerating outputs and the static build, then validates the regenerated version. Passing CI alone does not prove that the website was deployed; check both workflows.

After deployment, open the site in a fresh browser session. Confirm that 100 records load, category filtering changes the queue, and a sample query returns clickable citations. Static browser retrieval uses JavaScript; the saved evaluation results use Python. Neither the local test suite nor the Pages build measures continuous availability or ingestion freshness.

See [Deployment and maintenance](DEPLOYMENT.md) for branch settings, update procedures and recovery steps.

## Data preparation

- `assemble_balanced_snapshot.py` collects notices and metadata from the selected official sections. Availability changes over time, so a new crawl may not have the same records or total count.
- `prepare_labels.py` creates provisional rule-derived labels marked `development_draft`. Running it overwrites the labelled CSV and must not be used over completed human reviews.
- `build_snapshot_questions.py` writes the fixed ten-question evaluation set tied to the included snapshot IDs. It is not a general question generator for newly crawled data.

These scripts document how inputs were prepared. They are not needed to run the application or reproduce results from the checked-in files.

Use a separate destination for a new crawl:

```bash
python3 app.py crawl --limit 100 --output tmp/live_notices.csv
```

## Label review

Follow `docs/LABELING_GUIDE.md`. Record `author_reviewed` only for records actually reviewed, then regenerate predictions, metrics and the static dataset. Update any affected numbers in README and the evaluation documentation. The optional check below requires all 100 labels to be reviewed:

```bash
python3 scripts/check_repository.py --require-reviewed
```

Author review improves label quality but does not create an independent holdout set. Classifier development and evaluation still need to be separated in a future experiment.
