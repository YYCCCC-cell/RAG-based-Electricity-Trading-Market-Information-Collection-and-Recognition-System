"""Shared records used by ingestion, classification, retrieval and evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Notice:
    notice_id: str
    title: str
    published_date: str
    url: str
    body: str = ""
    source: str = "Guangzhou Power Exchange Center"
    source_section: str = "latest_notices"
    fetched_at: str = ""
    gold_category: str = ""
    gold_market_impacting: bool | None = None
    label_status: str = "unlabelled"

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.body}".strip()

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "Notice":
        data = dict(row)
        value = data.get("gold_market_impacting")
        if isinstance(value, str):
            normalized = value.strip().lower()
            data["gold_market_impacting"] = (
                None if not normalized else normalized in {"1", "true", "yes"}
            )
        # Only pass fields that were actually present. This preserves dataclass
        # defaults when reading older snapshots with fewer columns.
        values = {
            name: data[name]
            for name in cls.__dataclass_fields__
            if name in data and data[name] is not None
        }
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Classification:
    category: str
    market_impacting: bool
    confidence: float
    matched_rules: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
