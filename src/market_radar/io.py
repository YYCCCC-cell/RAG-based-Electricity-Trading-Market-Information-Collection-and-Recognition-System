"""Small, dependency-free helpers for reading and writing project data."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import Notice


NOTICE_FIELDS = list(Notice.__dataclass_fields__)


def read_notices(path: str | Path) -> list[Notice]:
    path = Path(path)
    if path.suffix == ".jsonl":
        return [Notice.from_dict(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [Notice.from_dict(row) for row in csv.DictReader(handle)]


def write_notices(path: str | Path, notices: Iterable[Notice]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [n.to_dict() for n in notices]
    if path.suffix == ".jsonl":
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=NOTICE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: str | Path, value: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

