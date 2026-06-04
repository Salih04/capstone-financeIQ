"""Feature registry + leakage controls (PHASE 10).

Single declaration of every modelled column: its category, direction (is a
higher raw value "better"?), and what it may be used for. The leakage rules are
enforced here, not scattered across the codebase.

Key distinctions:
  * TARGET (annual_return_pct) is ground truth, never a feature.
  * Fundamental features: statement/valuation/growth/balance/cash-flow only.
    Never a realized return. Used for the Fundamental Score and for
    next-year prediction.
  * Market-aware features: momentum/return windows. Allowed for the
    Market-Aware Score and for next-year prediction (known by year end), but
    they OVERLAP the same-year target window, so they are NOT allowed for
    same-year explanatory scoring (would leak the target).
"""

from __future__ import annotations

from dataclasses import dataclass

LOWER_BETTER = "lower_better"
HIGHER_BETTER = "higher_better"


@dataclass(frozen=True)
class Feature:
    name: str            # column in the trusted CSV
    category: str        # display/grouping category
    direction: str       # HIGHER_BETTER | LOWER_BETTER
    fundamental: bool    # part of the Fundamental Score
    market: bool         # part of the Market-Aware Score
    same_year_explain: bool   # safe to use when explaining the same year's return
    next_year_predict: bool   # safe as a predictor of next year's return
    leakage_risk: str    # none | overlaps_target | is_target
    note: str = ""

    @property
    def positive_only(self) -> bool:
        # Valuation multiples are only meaningful when positive (negative P/E
        # etc. are excluded from ranking rather than treated as "cheap").
        return self.category == "Value"


# --- Target -----------------------------------------------------------------
TARGET = Feature(
    "annual_return_pct", "Target", HIGHER_BETTER,
    fundamental=False, market=False, same_year_explain=False,
    next_year_predict=False, leakage_risk="is_target",
    note="Realized yearly return. Ground truth, never a feature.",
)

# --- Fundamental features ---------------------------------------------------
_FUNDAMENTAL: list[Feature] = [
    # Profitability
    Feature("roe_pct", "Profitability", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("roa_pct", "Profitability", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("roic_pct", "Profitability", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("gross_margin_pct", "Profitability", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("ebitda_margin_pct", "Profitability", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("net_margin_pct", "Profitability", HIGHER_BETTER, True, False, True, True, "none"),
    # Value (lower multiple = cheaper; positive-only)
    Feature("pe", "Value", LOWER_BETTER, True, False, True, True, "none"),
    Feature("pb", "Value", LOWER_BETTER, True, False, True, True, "none"),
    Feature("ev_sales", "Value", LOWER_BETTER, True, False, True, True, "none"),
    Feature("ev_ebitda", "Value", LOWER_BETTER, True, False, True, True, "none"),
    Feature("peg", "Value", LOWER_BETTER, True, False, True, True, "none"),
    # Growth
    Feature("revenue_growth_pct", "Growth", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("gross_profit_growth_pct", "Growth", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("ebitda_growth_pct", "Growth", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("operating_income_growth_pct", "Growth", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("net_income_growth_pct", "Growth", HIGHER_BETTER, True, False, True, True, "none"),
    # Balance sheet / leverage
    Feature("current_ratio", "Balance Sheet", HIGHER_BETTER, True, False, True, True, "none"),
    Feature("leverage_ratio", "Balance Sheet", LOWER_BETTER, True, False, True, True, "none"),
    Feature("financial_debt_ratio", "Balance Sheet", LOWER_BETTER, True, False, True, True, "none"),
    Feature("net_debt_ebitda", "Balance Sheet", LOWER_BETTER, True, False, True, True, "none"),
    # Cash flow (derived margins added in scoring; raw FCF is size-dependent)
    Feature("fcf_margin_pct", "Cash Flow", HIGHER_BETTER, True, False, True, True, "none",
            "Derived: free_cash_flow / revenue * 100"),
    Feature("cfo_to_net_income", "Cash Flow", HIGHER_BETTER, True, False, True, True, "none",
            "Derived: ocf / net_income (earnings quality)"),
    # Size (log, rank-normalized)
    Feature("log_market_cap", "Size", HIGHER_BETTER, True, False, True, True, "none",
            "Derived: log(market_cap)"),
]

# --- Market-aware features (momentum) ---------------------------------------
_MARKET: list[Feature] = [
    Feature("return_3m_pct", "Momentum", HIGHER_BETTER, False, True, False, True, "overlaps_target"),
    Feature("return_6m_pct", "Momentum", HIGHER_BETTER, False, True, False, True, "overlaps_target"),
    Feature("return_ytd_pct", "Momentum", HIGHER_BETTER, False, True, False, True, "overlaps_target",
            "YTD overlaps the realized-return window; leakage for same-year."),
    Feature("return_1y_pct", "Momentum", HIGHER_BETTER, False, True, False, True, "overlaps_target",
            "Trailing 1y overlaps the realized-return window; leakage for same-year."),
    Feature("return_3y_pct", "Momentum", HIGHER_BETTER, False, True, False, True, "overlaps_target"),
    Feature("return_5y_pct", "Momentum", HIGHER_BETTER, False, True, False, True, "overlaps_target"),
]

REGISTRY: list[Feature] = [TARGET, *_FUNDAMENTAL, *_MARKET]
BY_NAME: dict[str, Feature] = {f.name: f for f in REGISTRY}

# Derived columns the scorer must compute before ranking.
DERIVED = ("fcf_margin_pct", "cfo_to_net_income", "log_market_cap")


def fundamental_features() -> list[Feature]:
    return [f for f in REGISTRY if f.fundamental]


def market_features() -> list[Feature]:
    return [f for f in REGISTRY if f.market]


def features_for_next_year_prediction() -> list[Feature]:
    """Columns usable to predict the FOLLOWING year's return (no target)."""
    return [f for f in REGISTRY if f.next_year_predict]


def registry_as_dicts() -> list[dict]:
    return [
        {
            "name": f.name,
            "category": f.category,
            "direction": f.direction,
            "fundamental": f.fundamental,
            "market": f.market,
            "same_year_explain": f.same_year_explain,
            "next_year_predict": f.next_year_predict,
            "leakage_risk": f.leakage_risk,
            "note": f.note,
        }
        for f in REGISTRY
    ]
