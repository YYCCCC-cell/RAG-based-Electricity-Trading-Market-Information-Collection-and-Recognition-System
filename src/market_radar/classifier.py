"""Auditable four-way classifier and market-impact alert rule set.

The classifier is deliberately deterministic. It gives the reviewer a clear
baseline, produces reason codes, and avoids pretending that RAG is a
classification method. A learned model can later replace this module behind
the same ``classify`` interface.
"""

from __future__ import annotations

import re

from .models import Classification, Notice


CATEGORIES = (
    "transaction_action",
    "rules_policy",
    "results_settlement",
    "service_other",
)

RULES: dict[str, tuple[str, ...]] = {
    "results_settlement": (
        "交易结果", "认购结果", "成交结果", "出清结果", "结算结果", "成交情况", "结果的通知",
    ),
    "rules_policy": (
        "规则", "细则", "管理办法", "交易方案", "政策", "征求意见", "修编", "收费标准", "指引",
    ),
    "transaction_action": (
        "组织开展", "交易开市", "开市", "交易安排", "交易预安排", "申报", "报名", "征集", "开展交易",
        "年度交易", "月度交易", "多日交易", "连续交易", "连续组织", "交易计划",
    ),
}

SERVICE_CONTEXT_TERMS = ("培训", "答疑", "宣贯", "课件", "讲解", "算例演示", "活动成功举办")

DEADLINE_PATTERN = re.compile(
    r"(?:截止|前反馈|申报时间|交易时间|请于|定于).{0,20}(?:\d{1,2}月\d{1,2}日|\d{1,2}:\d{2}|\d{4}年)",
    re.S,
)

HIGH_IMPACT_TERMS = (
    "开市", "交易", "申报", "结算", "出清", "成交", "规则", "实施细则", "收费", "年度", "月度", "现货",
    "中长期", "绿电", "绿证", "跨省", "跨区", "暂停", "调整", "变更", "截止",
)


def _hits(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def classify(notice: Notice) -> Classification:
    title = notice.title.replace(" ", "")
    text = notice.text.replace(" ", "")
    evidence: dict[str, list[str]] = {name: _hits(title, terms) for name, terms in RULES.items()}
    service_context = notice.source_section == "market_training" or any(
        term in title for term in SERVICE_CONTEXT_TERMS
    )

    # Result notices are most specific; policy outranks a generic occurrence of
    # "交易"; action notices come next. The order is part of the model card.
    if service_context:
        category = "service_other"
    elif evidence["results_settlement"]:
        category = "results_settlement"
    elif evidence["rules_policy"]:
        category = "rules_policy"
    elif evidence["transaction_action"]:
        category = "transaction_action"
    else:
        category = "service_other"

    matched = evidence.get(category, [])
    impact_hits = _hits(text, HIGH_IMPACT_TERMS)
    deadline = bool(DEADLINE_PATTERN.search(text))
    market_impacting = category != "service_other" and bool(impact_hits)
    if deadline:
        market_impacting = True

    score = 0.56 + min(0.30, 0.07 * len(matched)) + (0.08 if deadline else 0.0)
    if service_context:
        score = 0.88
    elif category == "service_other" and not matched:
        score = 0.62
    confidence = round(min(score, 0.94), 2)

    risk_flags: list[str] = []
    if deadline:
        risk_flags.append("deadline_detected")
    if any(term in text for term in ("暂停", "调整", "变更", "异常")):
        risk_flags.append("change_or_interruption")
    if service_context:
        risk_flags.append("service_context")
    if confidence < 0.70:
        risk_flags.append("human_review")

    return Classification(category, market_impacting, confidence, matched, risk_flags)
