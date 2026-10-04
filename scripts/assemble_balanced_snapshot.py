#!/usr/bin/env python3
"""Assemble a transparent 100-document development snapshot.

Collect up to 44 latest notices, 40 market-training notices and 20 rules
indexed by the same official centre. The checked-in snapshot contains
44/36/20 records because 36 training records were available when collected.
Record availability and the resulting count may change on subsequent runs.
"""

from __future__ import annotations

import ast
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_radar.crawler import _fetch, crawl, discover_section, parse_article  # noqa: E402
from market_radar.io import write_notices  # noqa: E402
from market_radar.models import Notice  # noqa: E402


TRAINING_URL = "http://www.gzpec.cn/service/scpx/"
RULES_URL = "http://www.gzpec.cn/law/jygz/"


def fetch_training(limit: int = 40) -> list[Notice]:
    found = discover_section(TRAINING_URL, page_count=4, limit=limit, delay_seconds=0.03)
    stamp = datetime.now(timezone.utc).isoformat()
    rows: list[Notice] = []
    for url, fallback_title in found:
        try:
            title, published, body = parse_article(url, fallback_title)
        except Exception:
            title, published, body = fallback_title, "", fallback_title
        rows.append(
            Notice("", title, published, url, body, source_section="market_training", fetched_at=stamp)
        )
        time.sleep(0.03)
    return rows


def fetch_rules(limit: int = 20) -> list[Notice]:
    html = _fetch(RULES_URL)
    match = re.search(r'<div id="Data"[^>]*>\s*(\[.*?\])\s*</div>', html, re.S)
    if not match:
        raise RuntimeError("rules data block not found")
    data = ast.literal_eval(match.group(1))
    priority = {"广东": 0, "区域": 1, "国家": 2}
    data.sort(key=lambda item: (priority.get(item.get("适用范围", ""), 9), item.get("发布时间", "")), reverse=False)
    selected = data[:limit]
    stamp = datetime.now(timezone.utc).isoformat()
    rows: list[Notice] = []
    for item in selected:
        title = item.get("标题", "")
        url = item.get("url", "")
        metadata = (
            f"类型：{item.get('类型', '')}。适用范围：{item.get('适用范围', '')}。"
            f"发布单位：{item.get('发布单位', '')}。实施日期：{item.get('实施日期', '')}。"
        )
        rows.append(
            Notice(
                "",
                title,
                item.get("发布时间", ""),
                url,
                metadata,
                source_section="rules_and_policy",
                fetched_at=stamp,
            )
        )
    return rows


def main() -> None:
    latest = crawl(limit=44, delay_seconds=0.03)
    for row in latest:
        row.source_section = "latest_notices"
    combined = latest + fetch_training(40) + fetch_rules(20)
    for index, notice in enumerate(combined, 1):
        notice.notice_id = f"GZPEC-{index:03d}"
    output = ROOT / "data" / "raw" / "notices_snapshot.csv"
    write_notices(output, combined)
    print(f"assembled {len(combined)} official records in {output}")


if __name__ == "__main__":
    main()
