from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.company import Company


_TURKISH_TRANSLATION = str.maketrans({
    "ı": "i",
    "İ": "i",
    "ş": "s",
    "Ş": "s",
    "ğ": "g",
    "Ğ": "g",
    "ü": "u",
    "Ü": "u",
    "ö": "o",
    "Ö": "o",
    "ç": "c",
    "Ç": "c",
})

_STOPWORDS = {
    "a",
    "s",
    "as",
    "tas",
    "ta",
    "ao",
    "t",
    "anonim",
    "sirket",
    "sirketi",
    "sanayi",
    "sanayii",
    "ticaret",
    "ve",
    "holding",
    "hizmetleri",
    "hizmetler",
    "fabrikalari",
    "fabrikasi",
    "uretim",
    "uretimi",
    "petrol",
    "rafinerileri",
    "tasimacilik",
    "yatirim",
    "yatirimlar",
    "endustri",
    "endustrisi",
    "maden",
    "madenleri",
    "isletmeleri",
    "isletmesi",
    "elektrik",
}

KAP_TICKERS = {
    "AEFES",
    "AKSA",
    "AKSEN",
    "ASELS",
    "BIMAS",
    "BRSAN",
    "BSOKE",
    "BTCIM",
    "CCOLA",
    "CIMSA",
    "CLEBI",
    "DOAS",
    "ECILC",
    "EGEEN",
    "ENJSA",
    "EREGL",
    "FROTO",
    "GENIL",
    "GRSEL",
    "GUBRF",
    "KCAER",
    "KRDMD",
    "MAGEN",
    "MAVI",
    "MGROS",
    "MIATK",
    "MPARK",
    "OTKAR",
    "OYAKC",
    "PGSUS",
    "SOKM",
    "TAVHL",
    "TCELL",
    "THYAO",
    "TOASO",
    "TRALT",
    "TRENJ",
    "TRMET",
    "TTKOM",
    "TTRAK",
    "TUPRS",
    "TUREX",
    "ULKER",
    "YEOTK",
}


_FIELD_PATTERNS = {
    "net_income": ["net donem kar", "net donem karı", "net dönem kar"],
    "equity": ["toplam ozkaynak", "ana ortakliga ait ozkaynak"],
    "total_assets": ["toplam varlik", "toplam kaynak"],
    "revenue": ["hasilat"],
    "gross_profit": ["brut kar", "ticari faaliyetlerden brut kar"],
    "ebitda": ["favok", "favok"],
    "operating_cash_flow": ["isletme faaliyetlerinden nakit akis"],
    "capex": ["maddi ve maddi olmayan duran varlik alim", "yatirim faaliyetlerinden kaynaklanan nakit akis"],
    "total_debt": ["toplam borc", "finansal borc"],
    "cash_and_equivalents": ["nakit ve nakit benzer"],
    "ebit": ["esas faaliyet kar", "faaliyet kar"],
    "interest_expense": ["finansman gider", "faiz gider"],
    "inventory": ["stoklar"],
    "receivables": ["ticari alacaklar"],
    "current_assets": ["donen varlik"],
    "current_liabilities": ["kisa vadeli yukumluluk"],
    "market_price": ["hisse fiyati"],
    "eps": ["hisse basina kazanc", "eps"],
    "market_cap": ["piyasa degeri"],
    "book_value": ["defter degeri"],
    "enterprise_value": ["firma degeri"],
    "dividend_per_share": ["temettu"],
}


_RATIO_SPECS = [
    {
        "category": "Profitability",
        "ratio_name": "ROE",
        "formula": "net_income / equity",
        "interpretation": "Capital efficiency",
    },
    {
        "category": "Profitability",
        "ratio_name": "ROA",
        "formula": "net_income / total_assets",
        "interpretation": "Asset efficiency",
    },
    {
        "category": "Profitability",
        "ratio_name": "Gross Profit Margin",
        "formula": "gross_profit / revenue",
        "interpretation": "Product profitability",
    },
    {
        "category": "Profitability",
        "ratio_name": "EBITDA Margin",
        "formula": "ebitda / revenue",
        "interpretation": "Operating profitability",
    },
    {
        "category": "Profitability",
        "ratio_name": "Net Profit Margin",
        "formula": "net_income / revenue",
        "interpretation": "Bottom-line profitability",
    },
    {
        "category": "Cash Flow",
        "ratio_name": "FCF",
        "formula": "operating_cash_flow - capex",
        "interpretation": "Free cash flow",
    },
    {
        "category": "Cash Flow",
        "ratio_name": "OCF",
        "formula": "operating_cash_flow",
        "interpretation": "Operating cash flow",
    },
    {
        "category": "Growth",
        "ratio_name": "Net Income Growth",
        "formula": "(net_income_current / net_income_previous) - 1",
        "interpretation": "Earnings growth",
    },
    {
        "category": "Growth",
        "ratio_name": "EBITDA Growth",
        "formula": "(ebitda_current / ebitda_previous) - 1",
        "interpretation": "Operating earnings growth",
    },
    {
        "category": "Growth",
        "ratio_name": "FCF Growth",
        "formula": "(fcf_current / fcf_previous) - 1",
        "interpretation": "Cash generation growth",
    },
    {
        "category": "Debt / Risk",
        "ratio_name": "Net Debt / EBITDA",
        "formula": "(total_debt - cash_and_equivalents) / ebitda",
        "interpretation": "Debt payback capacity",
    },
    {
        "category": "Debt / Risk",
        "ratio_name": "Debt / Equity",
        "formula": "total_debt / equity",
        "interpretation": "Financial leverage",
    },
    {
        "category": "Debt / Risk",
        "ratio_name": "Interest Coverage",
        "formula": "ebit / interest_expense",
        "interpretation": "Interest servicing capacity",
    },
    {
        "category": "Debt / Risk",
        "ratio_name": "Net Debt / Equity",
        "formula": "(total_debt - cash_and_equivalents) / equity",
        "interpretation": "Balance sheet leverage",
    },
    {
        "category": "Efficiency",
        "ratio_name": "Asset Turnover",
        "formula": "revenue / total_assets",
        "interpretation": "Asset utilization",
    },
    {
        "category": "Efficiency",
        "ratio_name": "Inventory Turnover",
        "formula": "revenue / inventory",
        "interpretation": "Inventory efficiency",
    },
    {
        "category": "Efficiency",
        "ratio_name": "Receivables Turnover",
        "formula": "revenue / receivables",
        "interpretation": "Collections efficiency",
    },
    {
        "category": "Efficiency",
        "ratio_name": "Working Capital Turnover",
        "formula": "revenue / (current_assets - current_liabilities)",
        "interpretation": "Working capital efficiency",
    },
    {
        "category": "Valuation",
        "ratio_name": "P/E",
        "formula": "market_price / eps",
        "interpretation": "Earnings valuation",
    },
    {
        "category": "Valuation",
        "ratio_name": "P/B",
        "formula": "market_cap / book_value",
        "interpretation": "Book value valuation",
    },
    {
        "category": "Valuation",
        "ratio_name": "EV/EBITDA",
        "formula": "enterprise_value / ebitda",
        "interpretation": "Enterprise valuation",
    },
    {
        "category": "Valuation",
        "ratio_name": "PEG",
        "formula": "pe_ratio / net_income_growth",
        "interpretation": "Growth-adjusted valuation",
    },
    {
        "category": "Liquidity",
        "ratio_name": "Current Ratio",
        "formula": "current_assets / current_liabilities",
        "interpretation": "Short-term liquidity",
    },
    {
        "category": "Liquidity",
        "ratio_name": "Quick Ratio",
        "formula": "(current_assets - inventory) / current_liabilities",
        "interpretation": "Liquid coverage",
    },
    {
        "category": "Liquidity",
        "ratio_name": "Cash Ratio",
        "formula": "cash_and_equivalents / current_liabilities",
        "interpretation": "Immediate liquidity",
    },
    {
        "category": "Dividend",
        "ratio_name": "Dividend Yield",
        "formula": "dividend_per_share / market_price",
        "interpretation": "Shareholder yield",
    },
]


def get_kap_financial_ratios(db: Session) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    data_dir = root / "docs" / "DATA_Financial"
    if not data_dir.exists():
        raise ValueError("docs/DATA_Financial not found.")

    companies = db.query(Company).all()
    items: list[dict[str, Any]] = []
    errors: list[str] = []

    for file_path in sorted(data_dir.glob("*.xls")):
        stock_code = _match_company_to_stock_code(file_path.stem, companies)
        if not stock_code:
            errors.append(f"No company match for file: {file_path.name}")
            continue
        if stock_code not in KAP_TICKERS:
            continue

        try:
            year_inputs = _extract_company_year_inputs(file_path)
        except Exception as exc:
            errors.append(f"Failed to parse {file_path.name}: {exc}")
            continue

        for year in sorted(year_inputs.keys()):
            data = year_inputs.get(year, {})
            prev_data = year_inputs.get(year - 1)
            ratios = _compute_ratios(data, prev_data)
            items.append({
                "stock_code": stock_code,
                "year": year,
                "ratios": ratios,
            })

    return {"items": items, "errors": errors}


def get_kap_company_tickers(db: Session) -> set[str]:
    return set(KAP_TICKERS)


def _normalize_text(text: str) -> str:
    s = (text or "").strip().translate(_TURKISH_TRANSLATION).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def _tokenize(text: str) -> list[str]:
    tokens = [t for t in _normalize_text(text).split() if t and t not in _STOPWORDS]
    return tokens


def _match_company_to_stock_code(file_stem: str, companies: list[Company]) -> str | None:
    target_tokens = _tokenize(file_stem)
    target_norm = " ".join(target_tokens)
    if not target_tokens:
        return None

    best_code = None
    best_score = 0.0

    for c in companies:
        cname_tokens = _tokenize(c.company_name)
        if not cname_tokens:
            continue
        cname_norm = " ".join(cname_tokens)

        overlap = len(set(target_tokens) & set(cname_tokens))
        ratio = 0.0
        if target_norm and cname_norm:
            ratio = _sequence_ratio(target_norm, cname_norm)

        score = (overlap * 1.5) + (ratio * 5.0)
        if score > best_score:
            best_score = score
            best_code = c.ticker

    if best_score < 3.0:
        return None
    return best_code


def _sequence_ratio(a: str, b: str) -> float:
    from difflib import SequenceMatcher

    return SequenceMatcher(None, a, b).ratio()


def _extract_company_year_inputs(file_path: Path) -> dict[int, dict[str, float | None]]:
    tables = _read_html_tables(file_path)
    year_inputs: dict[int, dict[str, float | None]] = {}

    for df in tables:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        period_cols = [c for c in df.columns if re.fullmatch(r"20\d{2}/\d{2}", str(c).strip())]
        if not period_cols:
            continue

        label_col = df.columns[0]
        for _, row in df.iterrows():
            label_raw = str(row.get(label_col, "")).strip()
            if not label_raw:
                continue
            label_norm = _normalize_text(label_raw)
            if label_norm in {"sunum para birimi", "finansal tablo niteligi"}:
                continue
            field = _map_label_to_field(label_norm)
            if not field:
                continue

            for period in period_cols:
                year = int(str(period).split("/")[0])
                year_inputs.setdefault(year, {})
                if year_inputs[year].get(field) is not None:
                    continue
                value = _parse_turkish_number(row.get(period))
                year_inputs[year][field] = value

    return year_inputs


def _map_label_to_field(label_norm: str) -> str | None:
    for field, patterns in _FIELD_PATTERNS.items():
        for p in patterns:
            if p in label_norm:
                return field
    return None


def _parse_turkish_number(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        return None

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]

    s = s.replace(" ", "").replace("TL", "").replace("₺", "")
    s = s.replace(".", "")
    s = s.replace(",", ".")
    s = re.sub(r"[^0-9+\-.eE]", "", s)
    if not s:
        return None
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def _read_html_tables(file_path: Path) -> list[pd.DataFrame]:
    try:
        return pd.read_html(file_path)
    except Exception:
        text = _read_file_text(file_path)
        return _read_tables_with_bs4(text)


def _read_file_text(file_path: Path) -> str:
    for encoding in ("utf-8", "iso-8859-9"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _read_tables_with_bs4(text: str) -> list[pd.DataFrame]:
    soup = BeautifulSoup(text, "html.parser")
    tables: list[pd.DataFrame] = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if not rows:
            continue
        max_len = max(len(r) for r in rows)
        padded = [r + [""] * (max_len - len(r)) for r in rows]
        header = padded[0]
        df = pd.DataFrame(padded[1:], columns=header)
        tables.append(df)
    return tables


def _compute_ratios(data: dict[str, float | None], prev_data: dict[str, float | None] | None) -> list[dict[str, Any]]:
    ratios: list[dict[str, Any]] = []

    fcf_val, fcf_missing = _fcf(data)
    net_income_growth, net_income_growth_missing = _growth(data, prev_data, "net_income")
    ebitda_growth, ebitda_growth_missing = _growth(data, prev_data, "ebitda")
    fcf_growth, fcf_growth_missing = _growth_value(data, prev_data, fcf_val, "fcf")

    ratio_values = {
        "ROE": _ratio_div(data, "net_income", "equity"),
        "ROA": _ratio_div(data, "net_income", "total_assets"),
        "Gross Profit Margin": _ratio_div(data, "gross_profit", "revenue"),
        "EBITDA Margin": _ratio_div(data, "ebitda", "revenue"),
        "Net Profit Margin": _ratio_div(data, "net_income", "revenue"),
        "FCF": (fcf_val, fcf_missing),
        "OCF": _ratio_value(data, "operating_cash_flow"),
        "Net Income Growth": (net_income_growth, net_income_growth_missing),
        "EBITDA Growth": (ebitda_growth, ebitda_growth_missing),
        "FCF Growth": (fcf_growth, fcf_growth_missing),
        "Net Debt / EBITDA": _net_debt_ratio(data, "ebitda"),
        "Debt / Equity": _ratio_div(data, "total_debt", "equity"),
        "Interest Coverage": _ratio_div(data, "ebit", "interest_expense"),
        "Net Debt / Equity": _net_debt_ratio(data, "equity"),
        "Asset Turnover": _ratio_div(data, "revenue", "total_assets"),
        "Inventory Turnover": _ratio_div(data, "revenue", "inventory"),
        "Receivables Turnover": _ratio_div(data, "revenue", "receivables"),
        "Working Capital Turnover": _working_capital_turnover(data),
        "P/E": _ratio_div(data, "market_price", "eps"),
        "P/B": _ratio_div(data, "market_cap", "book_value"),
        "EV/EBITDA": _ratio_div(data, "enterprise_value", "ebitda"),
        "PEG": _peg_ratio(data, prev_data),
        "Current Ratio": _ratio_div(data, "current_assets", "current_liabilities"),
        "Quick Ratio": _quick_ratio(data),
        "Cash Ratio": _ratio_div(data, "cash_and_equivalents", "current_liabilities"),
        "Dividend Yield": _ratio_div(data, "dividend_per_share", "market_price"),
    }

    for spec in _RATIO_SPECS:
        val, missing = ratio_values.get(spec["ratio_name"], (None, ["not_available"]))
        ratios.append(
            {
                "category": spec["category"],
                "ratio_name": spec["ratio_name"],
                "value": val,
                "formula": spec["formula"],
                "interpretation": spec["interpretation"],
                "missing_fields": missing,
            }
        )

    return ratios


def _ratio_div(data: dict[str, float | None], numerator: str, denominator: str) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    n = data.get(numerator)
    d = data.get(denominator)
    if n is None:
        missing.append(numerator)
    if d is None:
        missing.append(denominator)
    elif d == 0:
        missing.append(f"{denominator} (zero)")
    if missing:
        return None, missing
    return n / d, []


def _ratio_value(data: dict[str, float | None], field: str) -> tuple[float | None, list[str]]:
    v = data.get(field)
    if v is None:
        return None, [field]
    return v, []


def _fcf(data: dict[str, float | None]) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    ocf = data.get("operating_cash_flow")
    capex = data.get("capex")
    if ocf is None:
        missing.append("operating_cash_flow")
    if capex is None:
        missing.append("capex")
    if missing:
        return None, missing
    return ocf - capex, []


def _growth(
    data: dict[str, float | None],
    prev_data: dict[str, float | None] | None,
    field: str,
) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    current = data.get(field)
    if current is None:
        missing.append(field)
    if not prev_data:
        missing.append(f"{field}_previous")
        return None, missing
    prev = prev_data.get(field)
    if prev is None:
        missing.append(f"{field}_previous")
    elif prev == 0:
        missing.append(f"{field}_previous (zero)")
    if missing:
        return None, missing
    return (current / prev) - 1, []


def _growth_value(
    data: dict[str, float | None],
    prev_data: dict[str, float | None] | None,
    current_value: float | None,
    field_label: str,
) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    if current_value is None:
        missing.append(field_label)
    if not prev_data:
        missing.append(f"{field_label}_previous")
        return None, missing
    prev = None
    if field_label == "fcf":
        prev_fcf, _ = _fcf(prev_data)
        prev = prev_fcf
    if prev is None:
        missing.append(f"{field_label}_previous")
    elif prev == 0:
        missing.append(f"{field_label}_previous (zero)")
    if missing:
        return None, missing
    return (current_value / prev) - 1, []


def _net_debt_ratio(data: dict[str, float | None], denominator_field: str) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    total_debt = data.get("total_debt")
    cash = data.get("cash_and_equivalents")
    d = data.get(denominator_field)
    if total_debt is None:
        missing.append("total_debt")
    if cash is None:
        missing.append("cash_and_equivalents")
    if d is None:
        missing.append(denominator_field)
    elif d == 0:
        missing.append(f"{denominator_field} (zero)")
    if missing:
        return None, missing
    return (total_debt - cash) / d, []


def _working_capital_turnover(data: dict[str, float | None]) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    revenue = data.get("revenue")
    current_assets = data.get("current_assets")
    current_liabilities = data.get("current_liabilities")
    if revenue is None:
        missing.append("revenue")
    if current_assets is None:
        missing.append("current_assets")
    if current_liabilities is None:
        missing.append("current_liabilities")
    if missing:
        return None, missing
    working_capital = current_assets - current_liabilities
    if working_capital == 0:
        return None, ["working_capital (zero)"]
    return revenue / working_capital, []


def _quick_ratio(data: dict[str, float | None]) -> tuple[float | None, list[str]]:
    missing: list[str] = []
    current_assets = data.get("current_assets")
    inventory = data.get("inventory")
    current_liabilities = data.get("current_liabilities")
    if current_assets is None:
        missing.append("current_assets")
    if inventory is None:
        missing.append("inventory")
    if current_liabilities is None:
        missing.append("current_liabilities")
    if missing:
        return None, missing
    denom = current_liabilities
    if denom == 0:
        return None, ["current_liabilities (zero)"]
    return (current_assets - inventory) / denom, []


def _peg_ratio(
    data: dict[str, float | None],
    prev_data: dict[str, float | None] | None,
) -> tuple[float | None, list[str]]:
    pe, pe_missing = _ratio_div(data, "market_price", "eps")
    growth, growth_missing = _growth(data, prev_data, "net_income")
    missing = pe_missing + [m.replace("net_income", "net_income_growth") for m in growth_missing]
    if missing:
        return None, missing
    if growth == 0:
        return None, ["net_income_growth (zero)"]
    return pe / growth, []
