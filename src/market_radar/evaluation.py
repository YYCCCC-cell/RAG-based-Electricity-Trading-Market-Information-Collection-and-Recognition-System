"""Reproducible classification, retrieval, latency and cost evaluation."""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from .classifier import CATEGORIES, classify
from .models import Notice
from .pipeline import estimate_cost
from .retriever import BM25Index


def _safe_div(num: int, den: int) -> float:
    return num / den if den else 0.0


def evaluate_classification(notices: list[Notice]) -> dict[str, object]:
    labelled = [
        n
        for n in notices
        if n.label_status != "unlabelled"
        and n.gold_category in CATEGORIES
        and n.gold_market_impacting is not None
    ]
    if not labelled:
        raise ValueError("no valid labelled notices were found")
    confusion = {gold: {pred: 0 for pred in CATEGORIES} for gold in CATEGORIES}
    impact = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    latencies: list[float] = []
    errors: list[dict[str, object]] = []
    for notice in labelled:
        start = time.perf_counter()
        pred = classify(notice)
        latencies.append((time.perf_counter() - start) * 1000)
        confusion[notice.gold_category][pred.category] += 1
        gold_impact = bool(notice.gold_market_impacting)
        if pred.market_impacting and gold_impact:
            impact["tp"] += 1
        elif pred.market_impacting and not gold_impact:
            impact["fp"] += 1
        elif not pred.market_impacting and gold_impact:
            impact["fn"] += 1
        else:
            impact["tn"] += 1
        if pred.category != notice.gold_category or pred.market_impacting != gold_impact:
            errors.append({
                "notice_id": notice.notice_id,
                "title": notice.title,
                "url": notice.url,
                "gold_category": notice.gold_category,
                "predicted_category": pred.category,
                "gold_market_impacting": gold_impact,
                "predicted_market_impacting": pred.market_impacting,
                "matched_rules": pred.matched_rules,
                "label_status": notice.label_status,
            })

    per_category: dict[str, dict[str, float | int]] = {}
    for category in CATEGORIES:
        tp = confusion[category][category]
        fp = sum(confusion[g][category] for g in CATEGORIES if g != category)
        fn = sum(confusion[category][p] for p in CATEGORIES if p != category)
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        per_category[category] = {
            "support": sum(confusion[category].values()),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(_safe_div(2 * precision * recall, precision + recall), 3),
        }

    p = _safe_div(impact["tp"], impact["tp"] + impact["fp"])
    r = _safe_div(impact["tp"], impact["tp"] + impact["fn"])
    specificity = _safe_div(impact["tn"], impact["tn"] + impact["fp"])
    accuracy = _safe_div(
        sum(confusion[c][c] for c in CATEGORIES),
        len(labelled),
    )
    positives = impact["tp"] + impact["fn"]
    flag_all_precision = _safe_div(positives, len(labelled))
    return {
        "evaluated_documents": len(labelled),
        "label_status_counts": {
            status: sum(n.label_status == status for n in notices)
            for status in sorted({n.label_status for n in notices})
        },
        "four_way_accuracy": round(accuracy, 3),
        "macro_f1": round(
            statistics.mean(float(values["f1"]) for values in per_category.values()), 3
        ),
        "per_category": per_category,
        "market_impacting": {
            **impact,
            "precision": round(p, 3),
            "recall": round(r, 3),
            "f1": round(_safe_div(2 * p * r, p + r), 3),
            "specificity": round(specificity, 3),
            "alerts_per_100_notices": round(
                100 * _safe_div(impact["tp"] + impact["fp"], len(labelled)), 1
            ),
        },
        "classification_latency_ms_p50": round(statistics.median(latencies), 3) if latencies else 0.0,
        "confusion_matrix": confusion,
        "baselines": {
            "flag_everything": {
                "precision": round(flag_all_precision, 3),
                "recall": 1.0 if positives else 0.0,
                "f1": round(_safe_div(2 * positives, len(labelled) + positives), 3),
                "alerts": len(labelled),
                "false_alerts": len(labelled) - positives,
            },
            "always_majority_category": {
                "accuracy": round(max(sum(row.values()) for row in confusion.values()) / len(labelled), 3),
            },
        },
        "errors": errors,
    }


def evaluate_retrieval(notices: list[Notice], questions_path: str | Path) -> dict[str, object]:
    questions = [json.loads(line) for line in Path(questions_path).read_text(encoding="utf-8").splitlines() if line]
    if not questions:
        raise ValueError("retrieval evaluation requires at least one question")
    available = {notice.notice_id for notice in notices}
    for item in questions:
        expected = set(item["relevant_notice_ids"])
        if not item.get("question", "").strip() or not expected or not expected <= available:
            raise ValueError("each retrieval question needs text and relevant IDs present in the corpus")
    index = BM25Index(notices)
    hits_at_3 = 0
    hits_at_1 = 0
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    details: list[dict[str, object]] = []
    for item in questions:
        start = time.perf_counter()
        hits = index.search(item["question"], top_k=3)
        latencies.append((time.perf_counter() - start) * 1000)
        ids = [hit.notice.notice_id for hit in hits]
        expected = set(item["relevant_notice_ids"])
        rank = next((i + 1 for i, notice_id in enumerate(ids) if notice_id in expected), None)
        hits_at_3 += int(rank is not None)
        hits_at_1 += int(rank == 1)
        reciprocal_ranks.append(1 / rank if rank else 0.0)
        details.append({"question": item["question"], "retrieved": ids, "rank": rank})
    return {
        "questions": len(questions),
        "citation_hit_rate_at_1": round(_safe_div(hits_at_1, len(questions)), 3),
        "citation_hit_rate_at_3": round(_safe_div(hits_at_3, len(questions)), 3),
        "mean_reciprocal_rank": round(statistics.mean(reciprocal_ranks), 3) if reciprocal_ranks else 0.0,
        "retrieval_latency_ms_p50": round(statistics.median(latencies), 3) if latencies else 0.0,
        "details": details,
    }


def evaluate_all(notices: list[Notice], questions_path: str | Path) -> dict[str, object]:
    return {
        "classification": evaluate_classification(notices),
        "retrieval": evaluate_retrieval(notices, questions_path),
        "cost": estimate_cost(len(notices)),
        "crawl_sla": {
            "target_minutes": 30,
            "interpretation": "Elapsed time from source publication becoming observable to successful ingestion; not model latency.",
            "status": "not measured by the offline snapshot",
        },
    }
