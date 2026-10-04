#!/usr/bin/env python3
"""Validate dataset alignment, saved metrics and the static build."""

from __future__ import annotations

import csv
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_radar.classifier import CATEGORIES, classify
from market_radar.evaluation import evaluate_all
from market_radar.io import read_notices
REQUIRED = (
    "README.md",
    "docs/DATA_CARD.md",
    "docs/EVALS.md",
    "docs/LABELING_GUIDE.md",
    "docs/PRODUCT_DOCUMENTATION.md",
    "data/labels/notices_labeled.csv",
    "data/evals/questions.jsonl",
    "outputs/metrics.json",
    "docs/REPRODUCIBILITY.md",
    ".github/workflows/ci.yml",
    "dist/notices.json",
)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def without_timings(value):
    """Wall-clock measurements vary; all other saved results must reproduce."""
    if isinstance(value, dict):
        return {key: without_timings(item) for key, item in value.items() if "latency_ms" not in key}
    if isinstance(value, list):
        return [without_timings(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-reviewed", action="store_true", help="also require author-reviewed labels")
    args = parser.parse_args()
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")

    with (ROOT / "data/labels/notices_labeled.csv").open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 100:
        fail(f"expected 100 labelled records, found {len(rows)}")
    for field in ("notice_id", "title", "published_date", "url", "source_section"):
        if any(not row[field].strip() for row in rows):
            fail(f"blank required field: {field}")
    for field in ("notice_id", "url"):
        if len({row[field] for row in rows}) != len(rows):
            fail(f"duplicate field: {field}")

    statuses = Counter(row["label_status"] for row in rows)
    for row in rows:
        if row["gold_category"] not in CATEGORIES:
            fail(f"invalid gold category: {row['notice_id']}")
        if row["gold_market_impacting"].lower() not in {"true", "false"}:
            fail(f"invalid gold boolean: {row['notice_id']}")
        if row["label_status"] not in {"development_draft", "author_reviewed"}:
            fail(f"invalid label status: {row['notice_id']}")

    notices = read_notices(ROOT / "data/labels/notices_labeled.csv")
    raw = read_notices(ROOT / "data/raw/notices_snapshot.csv")
    raw_by_id = {item.notice_id: item for item in raw}
    if len(raw_by_id) != 100 or set(raw_by_id) != {item.notice_id for item in notices}:
        fail("raw snapshot and labelled snapshot have different IDs")
    for item in notices:
        for field in ("title", "body", "url", "published_date", "source_section", "fetched_at"):
            if getattr(item, field) != getattr(raw_by_id[item.notice_id], field):
                fail(f"source drift in {item.notice_id}: {field}")
    metrics = json.loads((ROOT / "outputs/metrics.json").read_text(encoding="utf-8"))
    if metrics["classification"]["evaluated_documents"] != len(rows):
        fail("metrics do not cover all labelled records")
    if metrics["classification"]["label_status_counts"] != dict(statuses):
        fail("metric label-status counts do not match the dataset")
    recomputed = evaluate_all(notices, ROOT / "data/evals/questions.jsonl")
    if without_timings(metrics) != without_timings(recomputed):
        fail("saved metrics differ from recomputed results; run make evaluate")

    public = json.loads((ROOT / "dist/notices.json").read_text(encoding="utf-8"))
    expected_public = []
    for item in notices:
        record = {k: v for k, v in item.to_dict().items() if k not in {"gold_category", "gold_market_impacting", "label_status"}}
        record["prediction"] = classify(item).to_dict()
        expected_public.append(record)
    if public != expected_public:
        fail("static demo differs from source/predictions or exposes gold labels; run make site")
    for name in ("index.html", "app.js", "styles.css"):
        if (ROOT / "dist" / name).read_bytes() != (ROOT / "web" / name).read_bytes():
            fail(f"static asset differs from web source: {name}")

    if args.require_reviewed and statuses != {"author_reviewed": 100}:
        fail("author review is incomplete; do not change statuses without actually reviewing each notice")

    print(
        "PASS: 100 unique records; source alignment, recomputed metrics and static demo verified; "
        f"{len(REQUIRED)} required files present."
    )
    if statuses.get("development_draft"):
        print(f"Label status: {statuses['development_draft']} development drafts; author review pending.")


if __name__ == "__main__":
    main()
