"""
Explainability Service – V3 (3-Level)
======================================
Level 1 – Feature Contribution  (raw / transition / sector-normalized / model contribution)
Level 2 – Human-readable sentence per metric
Level 3 – Counterfactual mini insight ("if X had been Y, the score would be Z")
"""
from __future__ import annotations
from typing import Any

from app.services.scoring_service import _RULE_WEIGHTS

# ── meta-data used by explanation engine ──
_METRIC_FAMILIES = {
    "roa":              {"family": "Kârlılık", "direction": "higher", "label": "ROA"},
    "roe":              {"family": "Kârlılık", "direction": "higher", "label": "ROE"},
    "operating_margin": {"family": "Kârlılık", "direction": "higher", "label": "Faaliyet Marjı"},
    "net_margin":       {"family": "Kârlılık", "direction": "higher", "label": "Net Marj"},
    "current_ratio":    {"family": "Likidite",  "direction": "ideal_range", "label": "Cari Oran"},
    "quick_ratio":      {"family": "Likidite",  "direction": "higher", "label": "Asit-Test Oranı"},
    "cash_ratio":       {"family": "Likidite",  "direction": "higher", "label": "Nakit Oranı"},
    "debt_to_equity":   {"family": "Kaldıraç",  "direction": "lower", "label": "Borç/Özkaynak"},
    "debt_to_assets":   {"family": "Kaldıraç",  "direction": "lower", "label": "Borç/Varlık"},
    "ocf_to_debt":      {"family": "Nakit Akışı", "direction": "higher", "label": "İşletme Nakit/Borç"},
    "ocf_to_assets":    {"family": "Nakit Akışı", "direction": "higher", "label": "İşletme Nakit/Varlık"},
    "cash_flow_margin": {"family": "Nakit Akışı", "direction": "higher", "label": "Nakit Akış Marjı"},
}

_IDEAL_CURRENT_RATIO = (1.5, 3.0)


def _l2_sentence(
    key: str,
    curr: float | None,
    prev: float | None,
    z_score: float | None,
    transition: float | None,
) -> str:
    """Generate a single Turkish human-readable explanation sentence."""
    meta = _METRIC_FAMILIES.get(key, {"label": key, "direction": "higher"})
    label = meta["label"]
    direction = meta["direction"]

    if curr is None:
        return f"{label} verisi mevcut değil; değerlendirme dışı bırakıldı."

    parts = []

    # absolute level
    if direction == "higher":
        if curr >= 0.10:
            parts.append(f"{label} {curr:.2%} ile güçlü seviyede.")
        elif curr >= 0.05:
            parts.append(f"{label} {curr:.2%} ile orta seviyede.")
        elif curr > 0:
            parts.append(f"{label} {curr:.2%} ile zayıf, ancak pozitif.")
        else:
            parts.append(f"{label} {curr:.2%} ile negatif; risk sinyali.")
    elif direction == "lower":
        if curr <= 0.5:
            parts.append(f"{label} {curr:.2f} ile çok iyi (düşük).")
        elif curr <= 1.5:
            parts.append(f"{label} {curr:.2f} ile kabul edilebilir.")
        else:
            parts.append(f"{label} {curr:.2f} ile yüksek risk seviyesinde.")
    else:  # ideal_range
        lo, hi = _IDEAL_CURRENT_RATIO
        if lo <= curr <= hi:
            parts.append(f"{label} {curr:.2f} – ideal aralıkta ({lo}-{hi}).")
        else:
            parts.append(f"{label} {curr:.2f} – ideal aralık ({lo}-{hi}) dışında.")

    # transition commentary
    if transition is not None:
        if direction == "higher" and transition > 0.05:
            parts.append("Bir önceki döneme göre iyileşme kaydedildi ✓")
        elif direction == "higher" and transition < -0.05:
            parts.append("Bir önceki döneme göre kötüleşme gözlemlendi ✗")
        elif direction == "lower" and transition < -0.05:
            parts.append("Bir önceki döneme göre olumlu düşüş var ✓")
        elif direction == "lower" and transition > 0.05:
            parts.append("Bir önceki döneme göre olumsuz artış var ✗")

    # sector z-score commentary
    if z_score is not None:
        if z_score > 1.0:
            parts.append(f"Sektör medyanının {z_score:.1f} standart sapma üstünde.")
        elif z_score > 0:
            parts.append("Sektör ortalamasının biraz üstünde.")
        elif z_score > -1.0:
            parts.append("Sektör ortalamasının biraz altında.")
        else:
            parts.append(f"Sektör medyanının {abs(z_score):.1f} standart sapma altında.")

    return " ".join(parts)


def _l3_counterfactual(
    key: str,
    curr: float | None,
    contribution: float,
    weight: float,
    score: float,
) -> str | None:
    """
    Generate a counterfactual hint: 'if this metric were X better, the score
    would cross the next band'.
    Returns None if no meaningful insight can be generated.
    """
    if curr is None or weight <= 0:
        return None

    meta = _METRIC_FAMILIES.get(key, {})
    label = meta.get("label", key)
    direction = meta.get("direction", "higher")

    # How much contribution headroom is there?
    headroom = weight - contribution
    if headroom < weight * 0.20:
        return None  # already near max

    # Estimate what value change is needed to cross a score band
    # Score bands: <45 (weak), 45-70 (medium), >=70 (strong)
    next_band = 70 if score < 70 else None
    if next_band is None:
        return None

    gap_to_band = next_band - score
    if gap_to_band <= 0 or gap_to_band > headroom * 1.5:
        return None

    if direction == "higher":
        needed_delta = gap_to_band * 0.15  # rough estimate
        if curr + needed_delta <= 0:
            return None
        return (
            f"{label} yaklaşık %{needed_delta * 100:.1f} puan iyileşseydi, "
            f"toplam skor 'Güçlü' bandına girebilirdi."
        )
    elif direction == "lower":
        needed_delta = gap_to_band * 0.15
        return (
            f"{label} yaklaşık {needed_delta:.2f} azalsaydı, "
            f"toplam skor bir üst kategoriye yükselebilirdi."
        )

    return None


def build_rich_explanations(
    score_result: dict[str, Any],
    current_metrics: dict[str, float | None],
    previous_metrics: dict[str, float | None] | None,
    sector_z_scores: dict[str, float | None] | None = None,
) -> dict[str, Any]:
    """
    Enrich a scoring result dict with V3 3-level explanations.

    Input `score_result` must have 'details' list (from scoring_service.run_score).
    Returns the same dict with each detail enhanced + a top-level 'rich_explanation' block.
    """
    prev = previous_metrics or {}
    zs = sector_z_scores or {}
    score = score_result.get("total_score", 0)

    # Map metric labels back to keys for lookup
    _label_to_key = {v: k for k, v in {
        k: _METRIC_FAMILIES[k]["label"] for k in _METRIC_FAMILIES
    }.items()}
    # Also handle English labels from scoring_service
    from app.services.scoring_service import _METRIC_LABELS as _eng_labels
    _eng_to_key = {v: k for k, v in _eng_labels.items()}

    enhanced_details = []
    counterfactuals = []
    family_summary: dict[str, dict] = {}

    for detail in score_result.get("details", []):
        mname = detail["metric_name"]
        # resolve key
        key = _label_to_key.get(mname) or _eng_to_key.get(mname)

        curr_val = detail.get("metric_value")
        prev_val = prev.get(key) if key else None
        z_val = zs.get(key) if key else None
        transition_val = (curr_val - prev_val) if (curr_val is not None and prev_val is not None) else None
        contribution = float(detail.get("contribution") or 0.0)
        weight = float(detail.get("weight") or 0.0)

        # Level 2: human-readable sentence
        l2 = _l2_sentence(key or mname, curr_val, prev_val, z_val, transition_val) if key else detail.get("comment", "")

        # Level 3: counterfactual
        l3 = _l3_counterfactual(key or mname, curr_val, contribution, weight, score) if key else None
        if l3:
            counterfactuals.append(l3)

        # Family aggregation
        if key:
            fam = _METRIC_FAMILIES[key]["family"]
            if fam not in family_summary:
                family_summary[fam] = {"total_weight": 0, "total_contribution": 0, "metrics": []}
            family_summary[fam]["total_weight"] += weight
            family_summary[fam]["total_contribution"] += contribution
            family_summary[fam]["metrics"].append(mname)

        enhanced_details.append({
            **detail,
            "transition_value": round(transition_val, 4) if transition_val is not None else None,
            "sector_z_score": round(z_val, 4) if z_val is not None else None,
            "l2_explanation": l2,
            "l3_counterfactual": l3,
        })

    # Build family performance summary
    family_perf = []
    for fam, data in family_summary.items():
        pct = (data["total_contribution"] / data["total_weight"] * 100) if data["total_weight"] > 0 else 0
        family_perf.append({
            "family": fam,
            "score_pct": round(pct, 1),
            "metrics": data["metrics"],
        })
    family_perf.sort(key=lambda x: -x["score_pct"])

    # Strongest & weakest drivers at family level
    drivers_pos = [
        d for d in enhanced_details
        if (d.get("contribution") or 0.0) >= (d.get("weight") or 0.0) * 0.6]
    drivers_neg = [
        d for d in enhanced_details
        if (d.get("contribution") or 0.0) < (d.get("weight") or 0.0) * 0.3]
    drivers_pos.sort(key=lambda x: -(x.get("contribution") or 0.0))
    drivers_neg.sort(key=lambda x: (x.get("contribution") or 0.0))

    total_metrics = len(enhanced_details)
    available_metrics = sum(1 for d in enhanced_details if d.get("metric_value") is not None)
    excluded_metrics = [d["metric_name"] for d in enhanced_details if d.get("metric_value") is None]

    score_mode = score_result.get("label_used", "rule_based")
    if "logistic" in score_mode:
        method_note = "This probability is generated using a logistic regression model."
    else:
        method_note = "This score is a rule-based financial health indicator."

    rich = {
        "family_performance": family_perf,
        "strongest_drivers": [d["metric_name"] for d in drivers_pos[:3]],
        "weakest_drivers": [d["metric_name"] for d in drivers_neg[:3]],
        "counterfactuals": counterfactuals[:3],
        "data_completeness": round(available_metrics / max(total_metrics, 1), 2),
        "data_completeness_label": f"{available_metrics} / {total_metrics} metrics",
        "excluded_metrics": excluded_metrics,
        "method_note": method_note,
    }

    return {
        **score_result,
        "details": enhanced_details,
        "rich_explanation": rich,
    }
