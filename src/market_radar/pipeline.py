"""End-to-end processing, digest generation and simple cost accounting."""

from __future__ import annotations

from collections import Counter
from datetime import date

from .classifier import classify
from .models import Notice


def process(notices: list[Notice]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for notice in notices:
        prediction = classify(notice)
        rows.append({**notice.to_dict(), **{f"pred_{k}": v for k, v in prediction.to_dict().items()}})
    return rows


def build_digest(rows: list[dict[str, object]], as_of: str | None = None) -> str:
    as_of = as_of or date.today().isoformat()
    impactful = [row for row in rows if row["pred_market_impacting"]]
    counts = Counter(str(row["pred_category"]) for row in rows)
    lines = [
        f"# Power Notice Radar digest - {as_of}",
        "",
        f"Reviewed **{len(rows)}** notices; **{len(impactful)}** were flagged market-impacting.",
        "",
        "## Category mix",
        "",
    ]
    for key in ("transaction_action", "rules_policy", "results_settlement", "service_other"):
        lines.append(f"- `{key}`: {counts[key]}")
    lines += ["", "## Priority queue", ""]
    for row in sorted(impactful, key=lambda item: str(item["published_date"]), reverse=True)[:12]:
        flags = ", ".join(row["pred_risk_flags"]) or "standard_review"
        lines.append(
            f"- **{row['published_date']} - {row['title']}** "
            f"(`{row['pred_category']}`, {flags}) [[source]]({row['url']})"
        )
    lines += [
        "",
        "> Decision support only. A trader must open the source and verify dates, eligibility and attachments before acting.",
    ]
    return "\n".join(lines) + "\n"


def estimate_cost(
    notice_count: int,
    input_tokens_per_notice: int = 900,
    output_tokens_per_notice: int = 120,
    input_usd_per_million: float = 0.15,
    output_usd_per_million: float = 0.60,
) -> dict[str, object]:
    variable = (
        input_tokens_per_notice * input_usd_per_million
        + output_tokens_per_notice * output_usd_per_million
    ) / 1_000_000
    return {
        "notice_count": notice_count,
        "offline_rules_and_bm25_usd_per_notice": 0.0,
        "optional_llm_estimate_usd_per_notice": round(variable, 6),
        "optional_llm_estimate_usd_total": round(variable * notice_count, 4),
        "scenario_inputs": {
            "input_tokens_per_notice": input_tokens_per_notice,
            "output_tokens_per_notice": output_tokens_per_notice,
            "input_usd_per_million": input_usd_per_million,
            "output_usd_per_million": output_usd_per_million,
        },
        "assumption": "Example price inputs; replace with the chosen provider's current rates before production.",
    }
