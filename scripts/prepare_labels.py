#!/usr/bin/env python3
"""Prepare the 100-document development label set.

These labels are an AI-assisted first pass following docs/LABELING_GUIDE.md.
They are deliberately marked ``development_draft`` until the named project
author reviews each row. The evaluation script reports that status rather than
silently presenting the set as independent human ground truth.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_radar.io import read_notices, write_notices  # noqa: E402


RESULT_TERMS = ("交易结果", "认购结果", "成交结果", "出清结果", "结算结果", "结果的通知")
RULE_TERMS = (
    "实施细则", "交易规则", "管理办法", "交易方案", "收费标准", "服务收费", "操作指引", "管理规定",
)
ACTION_TERMS = (
    "组织开展", "开市", "预安排", "交易安排", "申报", "报名", "征集", "公开征求", "征求意见", "开展交易",
    "连续组织", "交易计划",
)
MATERIAL_TERMS = (
    "交易", "申报", "开市", "结果", "结算", "规则", "细则", "方案", "收费", "调整", "变更", "暂停", "征求意见",
)
NON_MARKET_TERMS = ("招聘", "采购", "党建", "廉洁", "获奖", "会议", "培训", "宣传")


def annotate(title: str, source_section: str) -> tuple[str, bool]:
    compact = title.replace(" ", "")
    clearly_non_market = source_section == "market_training" or any(
        term in compact for term in NON_MARKET_TERMS
    )
    if clearly_non_market:
        category = "service_other"
    elif any(term in compact for term in RESULT_TERMS):
        category = "results_settlement"
    elif any(term in compact for term in RULE_TERMS):
        category = "rules_policy"
    elif any(term in compact for term in ACTION_TERMS):
        category = "transaction_action"
    else:
        category = "service_other"

    material = any(term in compact for term in MATERIAL_TERMS)
    impacting = category != "service_other" and material
    return category, impacting


def main() -> None:
    source = ROOT / "data" / "raw" / "notices_snapshot.csv"
    output = ROOT / "data" / "labels" / "notices_labeled.csv"
    notices = read_notices(source)
    for notice in notices:
        notice.gold_category, notice.gold_market_impacting = annotate(
            notice.title, notice.source_section
        )
        notice.label_status = "development_draft"
    write_notices(output, notices)
    print(f"wrote {len(notices)} development labels to {output}")


if __name__ == "__main__":
    main()
