#!/usr/bin/env python3
"""Build the browser-only public demo from versioned project inputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from market_radar.classifier import classify
from market_radar.io import read_notices


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data" / "labels" / "notices_labeled.csv"


def main() -> None:
    DIST.mkdir(exist_ok=True)
    for name in ("index.html", "styles.css", "app.js"):
        shutil.copyfile(ROOT / "web" / name, DIST / name)

    rows = []
    for notice in read_notices(DATA):
        public = {
            key: value
            for key, value in notice.to_dict().items()
            if key not in {"gold_category", "gold_market_impacting", "label_status"}
        }
        public["prediction"] = classify(notice).to_dict()
        rows.append(public)

    (DIST / "notices.json").write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"built public static demo with {len(rows)} notices in {DIST}")


if __name__ == "__main__":
    main()
