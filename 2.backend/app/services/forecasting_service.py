from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import RFE, mutual_info_regression
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

from app.models.forecasting import (
    ForecastPrediction,
    ForecastEvaluationFold,
    ForecastEvaluationRun,
    ForecastRun,
    SectorParameterRanking,
    WinnerCohortRow,
    QuarterlyFundamental,
)


_ALLOWED_PRESET_PREFIXES = ("2020", "2021", "2022", "2023", "2024", "2025")

_FEATURE_COLUMNS: dict[str, str] = {
    "period_return": "period_return",
    "day_return": "day_return",
    "volume": "volume",
    "price": "price",
    "return_1w": "return_1w",
    "return_1m": "return_1m",
    "return_3m": "return_3m",
    "return_6m": "return_6m",
    "return_ytd": "return_ytd",
    "return_1y": "return_1y",
    "return_3y": "return_3y",
    "return_5y": "return_5y",
}

_PARAMETER_CATALOG: list[dict[str, str]] = [
    {"category": "Karlilik", "ratio": "ROE", "formula": "Net Kar / Ozsermaye", "purpose": "Sermaye verimliligi"},
    {"category": "Karlilik", "ratio": "ROA", "formula": "Net Kar / Toplam Varlik", "purpose": "Varlik verimliligi"},
    {"category": "Karlilik", "ratio": "Brut Kar Marji", "formula": "Brut Kar / Ciro", "purpose": "Urun karliligi"},
    {"category": "Karlilik", "ratio": "Faaliyet Kar Marji", "formula": "Faaliyet Kari / Ciro", "purpose": "Operasyonel karlilik"},
    {"category": "Karlilik", "ratio": "Net Kar Marji", "formula": "Net Kar / Ciro", "purpose": "Nihai karlilik"},

    {"category": "Nakit Akisi", "ratio": "OCF", "formula": "Operasyonel Nakit Akisi", "purpose": "Operasyondan gelen para"},
    {"category": "Nakit Akisi", "ratio": "OCF Marji", "formula": "Operasyonel Nakit Akisi / Ciro", "purpose": "Cirodan nakit yaratma gucu"},

    {"category": "Buyume", "ratio": "Net Kar Buyumesi", "formula": "(Kar_t / Kar_t-1) - 1", "purpose": "Kar buyumesi"},
    {"category": "Buyume", "ratio": "Ciro Buyumesi", "formula": "(Ciro_t / Ciro_t-1) - 1", "purpose": "Gelir buyumesi"},

    {"category": "Borc/Risk", "ratio": "Borc / Ozsermaye", "formula": "Toplam Yukumluluk / Ozsermaye", "purpose": "Finansal kaldirac"},
    {"category": "Borc/Risk", "ratio": "Borc / Varlik", "formula": "Toplam Yukumluluk / Toplam Varlik", "purpose": "Borc seviyesi"},
    {"category": "Borc/Risk", "ratio": "Net Borc / Equity", "formula": "(Toplam Yukumluluk - Nakit) / Ozsermaye", "purpose": "Net risk seviyesi"},

    {"category": "Verimlilik", "ratio": "Asset Turnover", "formula": "Ciro / Toplam Varlik", "purpose": "Varlik kullanimi"},
    {"category": "Verimlilik", "ratio": "Inventory Turnover", "formula": "Ciro / Stok", "purpose": "Stok yonetimi"},

    {"category": "Likidite", "ratio": "Current Ratio", "formula": "Donen Varlik / Kisa Vadeli Yukumluluk", "purpose": "Kisa vadeli odeme gucu"},
    {"category": "Likidite", "ratio": "Quick Ratio", "formula": "(Donen Varlik - Stok) / Kisa Vadeli Yukumluluk", "purpose": "Siki likidite"},
    {"category": "Likidite", "ratio": "Cash Ratio", "formula": "Nakit / Kisa Vadeli Yukumluluk", "purpose": "Anlik odeme gucu"},
]


def _normalize_text(v: Any) -> str:
    if v is None:
        return ""
    return unicodedata.normalize("NFKC", str(v)).strip()


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)

    s = _normalize_text(v)
    if not s:
        return None

    s = s.replace("%", "")
    s = s.replace("₺", "")
    s = s.replace("TL", "")
    s = s.replace(" ", "")

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "")
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")

    s = re.sub(r"[^0-9+\-.eE]", "", s)
    if not s:
        return None

    try:
        return float(s)
    except ValueError:
        return None


def _infer_year_from_file_name(file_name: str) -> int:
    m = re.match(r"\s*(\d{4})", _normalize_text(file_name))
    if not m:
        raise ValueError("File name must start with year (e.g. 2024 ...xlsx).")
    return int(m.group(1))


def _resolve_preset_file(file_name: str) -> Path:
    cleaned = _normalize_text(file_name)
    if not cleaned.lower().endswith(".xlsx"):
        raise ValueError("Only .xlsx files are accepted for preset import.")
    if not cleaned.startswith(_ALLOWED_PRESET_PREFIXES):
        raise ValueError("Only 2020-2025 preset files are allowed.")

    root = Path(__file__).resolve().parents[3]
    normalized_cleaned = cleaned.replace("İ", "I").replace("ı", "i")
    direct_path = Path(cleaned)
    if direct_path.is_absolute() and direct_path.exists():
        return direct_path

    candidate_dirs = [root, root / "3.Datasets"]
    for base in candidate_dirs:
        direct = base / cleaned
        if direct.exists():
            return direct
        direct_norm = base / normalized_cleaned
        if direct_norm.exists():
            return direct_norm
        for p in base.glob("*.xlsx"):
            pn = _normalize_text(p.name)
            if pn == cleaned or pn == normalized_cleaned:
                return p
    raise FileNotFoundError(f"Preset file not found: {cleaned}")


def _pick_column(df: pd.DataFrame, key: str) -> str | None:
    key_n = _normalize_text(key).lower()
    for c in df.columns:
        if key_n in _normalize_text(c).lower():
            return c
    return None


def _col_map(df: pd.DataFrame, year: int) -> dict[str, str | None]:
    period_col = None
    for c in df.columns:
        cn = _normalize_text(c)
        if "Getiri %" in cn and str(year) in cn:
            period_col = c
            break

    return {
        "stock_code": _pick_column(df, "Şirket"),
        "sector": _pick_column(df, "Sektör"),
        "period_return": period_col,
        "day_return": _pick_column(df, "Gün %"),
        "volume": _pick_column(df, "Hacim"),
        "price": _pick_column(df, "Fiyat"),
        "return_1w": _pick_column(df, "Son 1 hafta"),
        "return_1m": _pick_column(df, "Son 1 ay"),
        "return_3m": _pick_column(df, "Son 3 ay"),
        "return_6m": _pick_column(df, "Son 6 ay"),
        "return_ytd": _pick_column(df, "Yılbaşından bugüne"),
        "return_1y": _pick_column(df, "Son 1 yıl"),
        "return_3y": _pick_column(df, "Son 3 yıl"),
        "return_5y": _pick_column(df, "Son 5 yıl"),
    }


def import_winner_excel_preset(db: Session, file_name: str) -> dict[str, Any]:
    file_path = _resolve_preset_file(file_name)
    year = _infer_year_from_file_name(file_name)

    df = pd.read_excel(file_path)
    cmap = _col_map(df, year)

    if not cmap["stock_code"] or not cmap["sector"]:
        raise ValueError("File must include company code and sector columns.")

    # Apply median imputation per numeric feature column across the whole dataset
    feature_cols = {src_key: cmap.get(src_key) for src_key in _FEATURE_COLUMNS if cmap.get(src_key)}
    for col in feature_cols.values():
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            col_median = numeric.median()
            df[col] = numeric.fillna(col_median)

    imported = 0
    skipped = 0
    seen: set[str] = set()

    for _, row in df.iterrows():
        code = _normalize_text(row.get(cmap["stock_code"]))
        sector = _normalize_text(row.get(cmap["sector"]))

        if not code or not sector:
            skipped += 1
            continue

        stock_code = code.upper()
        if stock_code in seen:
            skipped += 1
            continue
        seen.add(stock_code)

        values: dict[str, float | None] = {}
        for src_key, dst_key in _FEATURE_COLUMNS.items():
            col = cmap.get(src_key)
            values[dst_key] = _to_float(row.get(col)) if col else None

        existing = (
            db.query(WinnerCohortRow)
            .filter(WinnerCohortRow.year == year, WinnerCohortRow.stock_code == stock_code)
            .first()
        )

        payload = {
            "source_file": file_name,
            "year": year,
            "sector": sector,
            "stock_code": stock_code,
            **values,
            "raw_payload_json": json.dumps({k: str(v) for k, v in row.to_dict().items()}, ensure_ascii=False),
        }

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            db.add(WinnerCohortRow(**payload))

        imported += 1

    db.commit()
    return {
        "file_name": file_name,
        "imported_rows": imported,
        "skipped_rows": skipped,
        "years": [year],
    }


def _safe_corr(a: list[float], b: list[float]) -> float:
    if len(a) < 2 or len(b) < 2:
        return 0.0
    s1 = pd.Series(a)
    s2 = pd.Series(b)
    val = s1.corr(s2)
    if pd.isna(val):
        return 0.0
    return float(val)


def _normalize_method_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    if not raw_scores:
        return {}
    vals = list(raw_scores.values())
    lo = min(vals)
    hi = max(vals)
    span = hi - lo
    if span <= 1e-12:
        return {k: 0.5 for k in raw_scores}
    return {k: float((v - lo) / span) for k, v in raw_scores.items()}


def _zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    s = pd.Series(values)
    std = float(s.std(ddof=0))
    if std == 0:
        return [0.0 for _ in values]
    mean = float(s.mean())
    return [float((v - mean) / std) for v in values]


def _build_sector_dataframe(rows: list[WinnerCohortRow], sector: str) -> pd.DataFrame:
    data = []
    for r in rows:
        if r.sector != sector:
            continue
        rec = {
            "stock_code": r.stock_code,
            "year": r.year,
            "sector": r.sector,
            "period_return": r.period_return,
        }
        for f in _FEATURE_COLUMNS.values():
            rec[f] = getattr(r, f)
        data.append(rec)
    return pd.DataFrame(data)


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    b2 = b.replace(0, np.nan)
    return a / b2

def _fundamentals_to_exact_ratios(fdf: pd.DataFrame) -> pd.DataFrame:
    df = fdf.copy()
    if df.empty:
        return df

    df = df.sort_values(["stock_code", "period"]).reset_index(drop=True)

    df["ROE"] = _safe_div(df["net_income"], df["equity"])
    df["ROA"] = _safe_div(df["net_income"], df["total_assets"])
    df["Brut Kar Marji"] = _safe_div(df["gross_profit"], df["revenue"])
    df["Faaliyet Kar Marji"] = _safe_div(df["ebit"], df["revenue"])
    df["Net Kar Marji"] = _safe_div(df["net_income"], df["revenue"])

    df["OCF"] = df["ocf"]
    df["OCF Marji"] = _safe_div(df["ocf"], df["revenue"])

    df["Net Kar Buyumesi"] = df.groupby("stock_code")["net_income"].pct_change()
    df["Ciro Buyumesi"] = df.groupby("stock_code")["revenue"].pct_change()

    df["Borc / Ozsermaye"] = _safe_div(df["total_debt"], df["equity"])
    df["Borc / Varlik"] = _safe_div(df["total_debt"], df["total_assets"])
    df["Net Borc / Equity"] = _safe_div(df["total_debt"] - df["cash"], df["equity"])

    df["Asset Turnover"] = _safe_div(df["revenue"], df["total_assets"])
    df["Inventory Turnover"] = _safe_div(df["revenue"], df["inventory"])

    df["Current Ratio"] = _safe_div(df["current_assets"], df["current_liabilities"])
    df["Quick Ratio"] = _safe_div(df["current_assets"] - df["inventory"], df["current_liabilities"])
    df["Cash Ratio"] = _safe_div(df["cash"], df["current_liabilities"])

    return df

def _fundamentals_df_for_sector(db: Session, sector: str, year: int | None = None) -> pd.DataFrame:
    q = db.query(QuarterlyFundamental).filter(QuarterlyFundamental.sector == sector)
    if year is not None:
        q = q.filter(QuarterlyFundamental.year == year)
    rows = q.all()
    if not rows:
        return pd.DataFrame()

    data = []
    for r in rows:
        data.append(
            {
                "stock_code": r.stock_code,
                "sector": r.sector,
                "year": r.year,
                "quarter": r.quarter,
                "period": r.period,
                "net_income": r.net_income,
                "equity": r.equity,
                "total_assets": r.total_assets,
                "revenue": r.revenue,
                "gross_profit": r.gross_profit,
                "ebitda": r.ebitda,
                "ocf": r.ocf,
                "capex": r.capex,
                "total_debt": r.total_debt,
                "cash": r.cash,
                "ebit": r.ebit,
                "interest_expense": r.interest_expense,
                "inventory": r.inventory,
                "receivables": r.receivables,
                "net_working_capital": r.net_working_capital,
                "market_cap": r.market_cap,
                "book_value": r.book_value,
                "enterprise_value": r.enterprise_value,
                "eps": r.eps,
                "growth_rate": r.growth_rate,
                "current_assets": r.current_assets,
                "current_liabilities": r.current_liabilities,
                "dividend_per_share": r.dividend_per_share,
                "price": r.price,
            }
        )
    return pd.DataFrame(data)


def _compute_ml_method_scores(df_year: pd.DataFrame, features: list[str]) -> dict[str, dict[str, float]]:
    usable = df_year[[*features, "period_return"]].copy()
    if usable.empty:
        return {
            "rf": {}, "rfe": {}, "lasso": {}, "shap": {}, "mi": {},
            "spearman": {}, "pearson": {}, "cluster": {},
        }

    for f in features:
        usable[f] = pd.to_numeric(usable[f], errors="coerce")
        if usable[f].isna().all():
            usable[f] = 0.0
        else:
            usable[f] = usable[f].fillna(float(usable[f].median()))

    y_ret = pd.to_numeric(usable["period_return"], errors="coerce")
    y_ret = y_ret.fillna(float(y_ret.median()) if not y_ret.isna().all() else 0.0)

    X = usable[features].to_numpy(dtype=float)
    y_reg = y_ret.to_numpy(dtype=float)
    y_cls = (y_reg >= np.median(y_reg)).astype(int)

    spearman_raw: dict[str, float] = {}
    pearson_raw: dict[str, float] = {}
    cluster_raw: dict[str, float] = {}
    mi_raw: dict[str, float] = {}
    rf_raw: dict[str, float] = {}
    rfe_raw: dict[str, float] = {}
    lasso_raw: dict[str, float] = {}
    shap_raw: dict[str, float] = {}

    for i, f in enumerate(features):
        xs = usable[f].tolist()
        spearman_raw[f] = abs(_safe_corr(pd.Series(xs).rank().tolist(), pd.Series(y_reg).rank().tolist()))
        pearson_raw[f] = abs(_safe_corr(xs, y_reg.tolist()))

        try:
            if len(xs) >= 6 and len(set(xs)) > 1:
                km = KMeans(n_clusters=2, n_init=10, random_state=42)
                lbl = km.fit_predict(np.array(xs).reshape(-1, 1))
                if len(set(lbl)) == 2:
                    sil = silhouette_score(np.array(xs).reshape(-1, 1), lbl)
                    cluster_raw[f] = max(0.0, float((sil + 1.0) / 2.0))
                else:
                    cluster_raw[f] = 0.0
            else:
                cluster_raw[f] = 0.0
        except Exception:
            cluster_raw[f] = 0.0

    try:
        mi_vals = mutual_info_regression(X, y_reg, random_state=42)
        for i, f in enumerate(features):
            mi_raw[f] = float(max(mi_vals[i], 0.0))
    except Exception:
        for f in features:
            mi_raw[f] = 0.0

    try:
        rf = RandomForestClassifier(n_estimators=300, random_state=42)
        rf.fit(X, y_cls)
        for i, f in enumerate(features):
            rf_raw[f] = float(max(rf.feature_importances_[i], 0.0))
    except Exception:
        for f in features:
            rf_raw[f] = 0.0

    try:
        rfe_est = LogisticRegression(max_iter=500, solver="liblinear")
        n_select = max(1, len(features) // 2)
        rfe = RFE(estimator=rfe_est, n_features_to_select=n_select)
        rfe.fit(X, y_cls)
        for i, f in enumerate(features):
            rfe_raw[f] = float(1.0 if rfe.support_[i] else 0.0)
    except Exception:
        for f in features:
            rfe_raw[f] = 0.0

    try:
        scaler = StandardScaler()
        Xs = scaler.fit_transform(X)
        lasso = Lasso(alpha=0.01, random_state=42, max_iter=5000)
        lasso.fit(Xs, y_reg)
        for i, f in enumerate(features):
            lasso_raw[f] = float(abs(lasso.coef_[i]))
    except Exception:
        for f in features:
            lasso_raw[f] = 0.0

    shap_available = False
    try:
        import shap

        rf_reg = RandomForestRegressor(n_estimators=250, random_state=42)
        rf_reg.fit(X, y_reg)
        explainer = shap.TreeExplainer(rf_reg)
        shap_vals = explainer.shap_values(X)
        shap_abs = np.abs(shap_vals).mean(axis=0)
        for i, f in enumerate(features):
            shap_raw[f] = float(shap_abs[i])
        shap_available = True
    except Exception:
        for f in features:
            shap_raw[f] = rf_raw.get(f, 0.0)

    return {
        "rf": _normalize_method_scores(rf_raw),
        "rfe": _normalize_method_scores(rfe_raw),
        "lasso": _normalize_method_scores(lasso_raw),
        "shap": _normalize_method_scores(shap_raw),
        "mi": _normalize_method_scores(mi_raw),
        "spearman": _normalize_method_scores(spearman_raw),
        "pearson": _normalize_method_scores(pearson_raw),
        "cluster": _normalize_method_scores(cluster_raw),
        "meta": {"shap_available": shap_available},
    }


def _fundamentals_df_for_sector(db: Session, sector: str, year: int | None = None) -> pd.DataFrame:
    q = db.query(QuarterlyFundamental).filter(QuarterlyFundamental.sector == sector)
    if year is not None:
        q = q.filter(QuarterlyFundamental.year == year)
    rows = q.all()
    if not rows:
        return pd.DataFrame()
    data = []
    for r in rows:
        data.append(
            {
                "stock_code": r.stock_code,
                "sector": r.sector,
                "year": r.year,
                "quarter": r.quarter,
                "period": r.period,
                "net_income": r.net_income,
                "equity": r.equity,
                "total_assets": r.total_assets,
                "revenue": r.revenue,
                "gross_profit": r.gross_profit,
                "ebitda": r.ebitda,
                "ocf": r.ocf,
                "capex": r.capex,
                "total_debt": r.total_debt,
                "cash": r.cash,
                "ebit": r.ebit,
                "interest_expense": r.interest_expense,
                "inventory": r.inventory,
                "receivables": r.receivables,
                "net_working_capital": r.net_working_capital,
                "market_cap": r.market_cap,
                "book_value": r.book_value,
                "enterprise_value": r.enterprise_value,
                "eps": r.eps,
                "growth_rate": r.growth_rate,
                "current_assets": r.current_assets,
                "current_liabilities": r.current_liabilities,
                "dividend_per_share": r.dividend_per_share,
                "price": r.price,
            }
        )
    return pd.DataFrame(data)


def _parameter_scores(db: Session, year: int, sector: str) -> list[dict[str, Any]]:
    fdf = _fundamentals_df_for_sector(db, sector=sector)
    df_year = _fundamentals_to_exact_ratios(fdf)
    if not df_year.empty:
        df_year = df_year[(df_year["year"] == year) & (df_year["quarter"] == 4)].copy()
    if df_year.empty:
        raise ValueError("No exact fundamentals found for selected sector/year (need quarterly fundamentals up to Q4).")

    target = df_year["Net Kar Buyumesi"].copy()
    target = target.fillna(df_year["ROE"])
    target = target.fillna(df_year["ROA"])
    df_year["period_return"] = target.fillna(0.0)

    by_stock: dict[str, list[pd.Series]] = {}
    for _, r in _fundamentals_to_exact_ratios(fdf).iterrows():
        by_stock.setdefault(str(r["stock_code"]).upper(), []).append(r)

    features = [p["ratio"] for p in _PARAMETER_CATALOG if p["ratio"] in df_year.columns]
    ml_scores = _compute_ml_method_scores(df_year, features)

    scores: list[dict[str, Any]] = []
    for f in features:
        year_vals = [float(v) for v in df_year[f].tolist() if v is not None and not pd.isna(v)]
        if len(year_vals) < 2:
            continue

        s = pd.Series(year_vals)
        mean = float(s.mean())
        std = float(s.std(ddof=0))
        cv = (std / abs(mean)) if mean != 0 else std
        cross_score = 1.0 / (1.0 + max(cv, 0.0))

        temporal_parts: list[float] = []
        for stock_rows in by_stock.values():
            vals = [float(sr[f]) for sr in stock_rows if f in sr and sr[f] is not None and not pd.isna(sr[f])]
            if len(vals) < 2:
                continue
            sv = pd.Series(vals)
            m = float(sv.mean())
            st = float(sv.std(ddof=0))
            stock_cv = (st / abs(m)) if m != 0 else st
            temporal_parts.append(1.0 / (1.0 + max(stock_cv, 0.0)))
        temporal_score = float(pd.Series(temporal_parts).mean()) if temporal_parts else 0.0

        z = _zscore(year_vals)
        transition_score = float(pd.Series([max(v, 0.0) for v in z]).mean()) if z else 0.0

        ensemble_score = (
            (0.14 * ml_scores["spearman"].get(f, 0.0))
            + (0.08 * ml_scores["pearson"].get(f, 0.0))
            + (0.14 * ml_scores["mi"].get(f, 0.0))
            + (0.14 * ml_scores["rf"].get(f, 0.0))
            + (0.10 * ml_scores["rfe"].get(f, 0.0))
            + (0.14 * ml_scores["lasso"].get(f, 0.0))
            + (0.14 * ml_scores["shap"].get(f, 0.0))
            + (0.12 * ml_scores["cluster"].get(f, 0.0))
        )

        score = round(
            (0.30 * cross_score) + (0.20 * temporal_score) + (0.10 * transition_score) + (0.40 * ensemble_score),
            6,
        )
        scores.append(
            {
                "parameter_name": f,
                "score": score,
                "cross_score": round(cross_score, 6),
                "temporal_score": round(temporal_score, 6),
                "transition_score": round(transition_score, 6),
                "spearman": round(ml_scores["spearman"].get(f, 0.0), 6),
                "pearson": round(ml_scores["pearson"].get(f, 0.0), 6),
                "mutual_info": round(ml_scores["mi"].get(f, 0.0), 6),
                "rf_importance": round(ml_scores["rf"].get(f, 0.0), 6),
                "rfe": round(ml_scores["rfe"].get(f, 0.0), 6),
                "lasso": round(ml_scores["lasso"].get(f, 0.0), 6),
                "shap": round(ml_scores["shap"].get(f, 0.0), 6),
                "cluster": round(ml_scores["cluster"].get(f, 0.0), 6),
                "shap_available": bool(ml_scores.get("meta", {}).get("shap_available", False)),
            }
        )

    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores


def train_sector_success_model(
    db: Session,
    year: int,
    sector: str,
    top_n_parameters: int = 8,
) -> dict[str, Any]:
    ranked = _parameter_scores(db, year=year, sector=sector)
    top = ranked[:max(1, top_n_parameters)]

    (
        db.query(SectorParameterRanking)
        .filter(SectorParameterRanking.year == year, SectorParameterRanking.sector == sector)
        .delete(synchronize_session=False)
    )

    for i, item in enumerate(top, start=1):
        db.add(
            SectorParameterRanking(
                year=year,
                sector=sector,
                parameter_name=item["parameter_name"],
                score=item["score"],
                rank=i,
                details_json=json.dumps(
                    {
                        "cross_score": item["cross_score"],
                        "temporal_score": item["temporal_score"],
                        "transition_score": item["transition_score"],
                        "spearman": item["spearman"],
                        "pearson": item["pearson"],
                        "mutual_info": item["mutual_info"],
                        "rf_importance": item["rf_importance"],
                        "rfe": item["rfe"],
                        "lasso": item["lasso"],
                        "shap": item["shap"],
                        "cluster": item["cluster"],
                        "shap_available": item["shap_available"],
                    }
                ),
            )
        )

    db.commit()
    return {
        "year": year,
        "sector": sector,
        "parameter_count": len(top),
        "top_parameters": [
            {"parameter_name": item["parameter_name"], "score": item["score"], "rank": i}
            for i, item in enumerate(top, start=1)
        ],
    }


def get_ranked_parameters(db: Session, year: int, sector: str) -> list[dict[str, Any]]:
    rows = (
        db.query(SectorParameterRanking)
        .filter(SectorParameterRanking.year == year, SectorParameterRanking.sector == sector)
        .order_by(SectorParameterRanking.rank.asc())
        .all()
    )
    return [
        {
            "parameter_name": r.parameter_name,
            "score": r.score,
            "rank": r.rank,
        }
        for r in rows
    ]


def run_forecast_for_sector(
    db: Session,
    year: int,
    sector: str,
    created_by_user_id: int | None = None,
    user_type: str | None = None,
    risk_level: str | None = None,
    investment_scope: float | None = None,
    model_type: str = "scoring",
) -> dict[str, Any]:
    if year < 2020 or year > 2025:
        raise ValueError("Year must be between 2020 and 2025 for this dataset scope.")

    params = get_ranked_parameters(db, year=year, sector=sector)
    if not params:
        trained = train_sector_success_model(db, year=year, sector=sector)
        params = trained["top_parameters"]

    selected_params = [p["parameter_name"] for p in params]
    weights = {p["parameter_name"]: p["score"] for p in params}
    weight_sum = sum(weights.values()) or 1.0

    rows = (
        db.query(WinnerCohortRow)
        .filter(WinnerCohortRow.year == year, WinnerCohortRow.sector == sector)
        .all()
    )
    if not rows:
        raise ValueError("No stocks found for selected year/sector.")

    fdf = _fundamentals_df_for_sector(db, sector=sector)
    ratios_df = _fundamentals_to_exact_ratios(fdf)
    ratios_df = ratios_df[(ratios_df["year"] == year) & (ratios_df["quarter"] == 4)].copy()
    if ratios_df.empty:
        raise ValueError("No exact quarterly fundamentals for selected sector/year (Q4 required).")

    row_by_stock = {str(r["stock_code"]).upper(): r for _, r in ratios_df.iterrows()}

    feature_values: dict[str, list[float]] = {}
    for p in selected_params:
        vals = []
        for r in rows:
            rr = row_by_stock.get(r.stock_code.upper())
            if rr is None:
                continue
            v = rr.get(p)
            if v is None or pd.isna(v):
                continue
            vals.append(float(v))
        feature_values[p] = vals

    normalized: dict[str, dict[str, float]] = {}
    for p in selected_params:
        vals = feature_values.get(p, [])
        if not vals:
            normalized[p] = {}
            continue
        min_v = min(vals)
        max_v = max(vals)
        span = (max_v - min_v) or 1.0
        p_map: dict[str, float] = {}
        for r in rows:
            rr = row_by_stock.get(r.stock_code.upper())
            if rr is None:
                continue
            v = rr.get(p)
            if v is None or pd.isna(v):
                continue
            p_map[r.stock_code] = (float(v) - min_v) / span
        normalized[p] = p_map

    scored: list[dict[str, Any]] = []

    risk_multipliers = {
        "low": 0.85,
        "medium": 1.0,
        "high": 1.15,
    }
    risk_factor = risk_multipliers.get((risk_level or "medium").lower(), 1.0)

    for r in rows:
        contribs: list[dict[str, float]] = []
        valid_count = 0
        total = 0.0
        for p in selected_params:
            w = weights[p]
            val = normalized[p].get(r.stock_code)
            if val is None:
                continue
            raw = val
            if model_type == "dbscan":
                raw = 1.0 - abs(val - 0.5) * 2.0
            elif model_type == "gmm":
                raw = np.exp(-((val - 0.6) ** 2) / 0.08)
            elif model_type == "xgboost":
                raw = (val ** 1.15)
            elif model_type == "arima":
                rr2 = row_by_stock.get(r.stock_code.upper())
                mom = 0.0
                if rr2 is not None:
                    m3 = rr2.get("Net Kar Buyumesi")
                    m1 = rr2.get("Ciro Buyumesi")
                    if m3 is not None and not pd.isna(m3) and m1 is not None and not pd.isna(m1):
                        mom = float(m3) - float(m1)
                raw = max(0.0, min(1.0, (val * 0.7) + (0.3 * (0.5 + np.tanh(mom / 100.0) / 2.0))))
            elif model_type == "prophet":
                rr3 = row_by_stock.get(r.stock_code.upper())
                trend_hint = 0.0
                if rr3 is not None:
                    vals = [rr3.get("ROE"), rr3.get("ROA"), rr3.get("Net Kar Marji")]
                    vals = [float(v) for v in vals if v is not None and not pd.isna(v)]
                    trend_hint = float(np.mean(vals)) if vals else 0.0
                raw = max(0.0, min(1.0, (0.65 * val) + (0.35 * (0.5 + np.tanh(trend_hint / 120.0) / 2.0))))

            c = raw * w
            contribs.append({"parameter_name": p, "contribution": round(c, 6)})
            total += c
            valid_count += 1

        score = (total / weight_sum) * 100.0 * risk_factor
        score = max(0.0, min(100.0, score))
        confidence = valid_count / max(1, len(selected_params))
        contribs.sort(key=lambda x: x["contribution"], reverse=True)

        trend = "flat"
        rr4 = row_by_stock.get(r.stock_code.upper())
        if rr4 is not None:
            g1 = rr4.get("Net Kar Buyumesi")
            g2 = rr4.get("Ciro Buyumesi")
            if g1 is not None and g2 is not None and not pd.isna(g1) and not pd.isna(g2):
                delta = float(g1) - float(g2)
                if delta > 0:
                    trend = "up"
                elif delta < 0:
                    trend = "down"

        scored.append(
            {
                "stock_code": r.stock_code,
                "sector": r.sector,
                "year": r.year,
                "score": round(score, 4),
                "confidence": round(confidence, 4),
                "trend": trend,
                "top_contributors": contribs[:5],
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    for i, item in enumerate(scored, start=1):
        item["rank"] = i

    run = ForecastRun(
        created_by_user_id=created_by_user_id,
        year=year,
        sector=sector,
        model_version="success_dna_mvp_v1",
        notes=f"Winner-only sector scoring run | model={model_type} | user_type={user_type or 'unknown'} | risk={risk_level or 'unknown'} | scope={investment_scope}",
    )
    db.add(run)
    db.flush()

    for item in scored:
        db.add(
            ForecastPrediction(
                forecast_run_id=run.id,
                year=item["year"],
                sector=item["sector"],
                stock_code=item["stock_code"],
                score=item["score"],
                confidence=item["confidence"],
                rank=item["rank"],
                explanation_json=json.dumps(
                    {
                        "summary": "Score is built from sector/year success parameter profile.",
                        "top_contributors": item["top_contributors"],
                    }
                ),
            )
        )

    db.commit()

    return {
        "run_id": run.id,
        "year": year,
        "sector": sector,
        "user_type": user_type,
        "risk_level": risk_level,
        "investment_scope": investment_scope,
        "model_type": model_type,
        "items": [
            {
                "stock_code": x["stock_code"],
                "sector": x["sector"],
                "year": x["year"],
                "score": x["score"],
                "rank": x["rank"],
                "confidence": x["confidence"],
                "trend": x["trend"],
            }
            for x in scored
        ],
    }


def get_parameters_for_sector(db: Session, year: int, sector: str) -> dict[str, Any]:
    params = get_ranked_parameters(db, year=year, sector=sector)
    if not params:
        train_sector_success_model(db, year=year, sector=sector)
        params = get_ranked_parameters(db, year=year, sector=sector)
    return {"year": year, "sector": sector, "parameters": params}


def _rank_map(items: list[dict[str, Any]], top_n: int = 10) -> dict[str, int]:
    return {it["stock_code"]: it["rank"] for it in items[:top_n]}


def _compute_rank_stability(prev_items: list[dict[str, Any]], curr_items: list[dict[str, Any]], top_n: int = 10) -> float | None:
    prev = _rank_map(prev_items, top_n=top_n)
    curr = _rank_map(curr_items, top_n=top_n)
    common = set(prev).intersection(curr)
    if not common:
        return None
    diffs = [abs(prev[s] - curr[s]) for s in common]
    max_diff = float(top_n)
    return float(max(0.0, 1.0 - (np.mean(diffs) / max_diff)))


def _compute_overlap_at_k(prev_items: list[dict[str, Any]], curr_items: list[dict[str, Any]], k: int = 10) -> float | None:
    a = {it["stock_code"] for it in prev_items[:k]}
    b = {it["stock_code"] for it in curr_items[:k]}
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    return float(len(a.intersection(b)) / max(1, min(len(a), len(b))))


def run_time_cv_evaluation(
    db: Session,
    sector: str,
    model_type: str = "scoring",
    window_size: int = 2,
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    years = sorted({r[0] for r in db.query(WinnerCohortRow.year).filter(WinnerCohortRow.sector == sector).distinct().all()})
    years = [y for y in years if 2020 <= int(y) <= 2025]
    if len(years) < max(3, window_size + 1):
        raise ValueError("Not enough years for rolling-window evaluation.")

    eval_run = ForecastEvaluationRun(
        created_by_user_id=created_by_user_id,
        sector=sector,
        model_type=model_type,
        window_size=window_size,
        total_folds=0,
    )
    db.add(eval_run)
    db.flush()

    folds_out = []
    stability_vals = []
    overlap_vals = []

    for idx in range(window_size, len(years)):
        train_years = years[idx - window_size:idx]
        test_year = years[idx]

        for ty in train_years:
            train_sector_success_model(db, year=ty, sector=sector, top_n_parameters=8)

        prev_year = years[idx - 1]
        prev_pred = run_forecast_for_sector(
            db,
            year=prev_year,
            sector=sector,
            created_by_user_id=created_by_user_id,
            user_type="evaluation",
            risk_level="medium",
            model_type=model_type,
        )
        curr_pred = run_forecast_for_sector(
            db,
            year=test_year,
            sector=sector,
            created_by_user_id=created_by_user_id,
            user_type="evaluation",
            risk_level="medium",
            model_type=model_type,
        )

        rank_stability = _compute_rank_stability(prev_pred["items"], curr_pred["items"], top_n=10)
        overlap_at_k = _compute_overlap_at_k(prev_pred["items"], curr_pred["items"], k=10)

        if rank_stability is not None:
            stability_vals.append(rank_stability)
        if overlap_at_k is not None:
            overlap_vals.append(overlap_at_k)

        fold = ForecastEvaluationFold(
            evaluation_run_id=eval_run.id,
            fold_index=(idx - window_size + 1),
            train_year_start=min(train_years),
            train_year_end=max(train_years),
            test_year=test_year,
            rank_stability=rank_stability,
            overlap_at_k=overlap_at_k,
            metrics_json=json.dumps(
                {
                    "train_years": train_years,
                    "test_year": test_year,
                    "prev_year": prev_year,
                }
            ),
        )
        db.add(fold)
        folds_out.append(
            {
                "fold_index": fold.fold_index,
                "train_year_start": fold.train_year_start,
                "train_year_end": fold.train_year_end,
                "test_year": fold.test_year,
                "rank_stability": rank_stability,
                "overlap_at_k": overlap_at_k,
            }
        )

    eval_run.total_folds = len(folds_out)
    eval_run.mean_rank_stability = float(np.mean(stability_vals)) if stability_vals else None
    eval_run.mean_overlap_at_k = float(np.mean(overlap_vals)) if overlap_vals else None
    eval_run.notes = "Rolling-window time CV for forecasting endpoint family"
    db.commit()

    return {
        "run_id": eval_run.id,
        "sector": sector,
        "model_type": model_type,
        "window_size": window_size,
        "total_folds": eval_run.total_folds,
        "mean_rank_stability": eval_run.mean_rank_stability,
        "mean_overlap_at_k": eval_run.mean_overlap_at_k,
        "folds": folds_out,
    }


def get_predict_history(db: Session, limit: int = 30, sector: str | None = None) -> dict[str, Any]:
    q = db.query(ForecastRun)
    if sector:
        q = q.filter(ForecastRun.sector == sector)
    rows = q.order_by(ForecastRun.created_at.desc()).limit(limit).all()
    return {
        "items": [
            {
                "run_id": r.id,
                "year": r.year,
                "sector": r.sector,
                "model_version": r.model_version,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    }


def get_yearly_trend_series(db: Session, stock_code: str, sector: str | None = None) -> dict[str, Any]:
    q = db.query(WinnerCohortRow).filter(WinnerCohortRow.stock_code == stock_code.upper())
    if sector:
        q = q.filter(WinnerCohortRow.sector == sector)
    rows = q.order_by(WinnerCohortRow.year.asc()).all()
    if not rows:
        return {"stock_code": stock_code.upper(), "series": []}

    out = []
    for r in rows:
        out.append(
            {
                "year": r.year,
                "period_return": r.period_return,
                "return_1y": r.return_1y,
                "return_6m": r.return_6m,
                "return_3m": r.return_3m,
                "return_1m": r.return_1m,
            }
        )
    return {"stock_code": stock_code.upper(), "series": out}


def get_sector_heatmap_data(db: Session, year: int) -> dict[str, Any]:
    if year < 2020 or year > 2025:
        return {"year": year, "heatmap": []}
    rows = db.query(WinnerCohortRow).filter(WinnerCohortRow.year == year).all()
    if not rows:
        return {"year": year, "heatmap": []}

    sector_map: dict[str, list[WinnerCohortRow]] = {}
    for r in rows:
        sector_map.setdefault(r.sector, []).append(r)

    feature_keys = ["period_return", "return_1y", "return_6m", "return_3m", "return_1m", "day_return"]
    heatmap = []
    for sector, items in sector_map.items():
        for f in feature_keys:
            vals = [getattr(i, f) for i in items if getattr(i, f) is not None]
            avg = float(np.mean(vals)) if vals else 0.0
            heatmap.append({"sector": sector, "feature": f, "value": round(avg, 4)})
    return {"year": year, "heatmap": heatmap}


def analyze_portfolio(
    db: Session,
    year: int,
    sector: str,
    stock_codes: list[str],
    created_by_user_id: int | None = None,
) -> dict[str, Any]:
    result = run_forecast_for_sector(
        db,
        year=year,
        sector=sector,
        created_by_user_id=created_by_user_id,
        user_type="corporate",
        risk_level="medium",
        investment_scope=None,
    )
    items = result["items"]
    wanted = {c.strip().upper() for c in stock_codes if c.strip()}
    scoped = [i for i in items if i["stock_code"] in wanted]

    if not scoped:
        return {
            "run_id": result["run_id"],
            "year": year,
            "sector": sector,
            "weak_stocks": [],
            "strong_stocks": [],
            "optimization_actions": ["No provided portfolio stocks found in selected sector/year."],
        }

    weak = sorted(scoped, key=lambda x: x["score"])[:3]
    strong = sorted(scoped, key=lambda x: x["score"], reverse=True)[:3]

    weak_items = [
        {
            "stock_code": w["stock_code"],
            "score": w["score"],
            "rank": w["rank"],
            "action": "reduce",
        }
        for w in weak
    ]
    strong_items = [
        {
            "stock_code": s["stock_code"],
            "score": s["score"],
            "rank": s["rank"],
            "action": "increase",
        }
        for s in strong
    ]

    actions = []
    for s in strong_items:
        actions.append(f"Increase exposure to {s['stock_code']} (score={s['score']:.2f}).")
    for w in weak_items:
        actions.append(f"Review or reduce {w['stock_code']} (score={w['score']:.2f}).")

    return {
        "run_id": result["run_id"],
        "year": year,
        "sector": sector,
        "weak_stocks": weak_items,
        "strong_stocks": strong_items,
        "optimization_actions": actions,
    }


def get_stock_detail(db: Session, run_id: int, stock_code: str) -> dict[str, Any] | None:
    pred = (
        db.query(ForecastPrediction)
        .filter(
            ForecastPrediction.forecast_run_id == run_id,
            ForecastPrediction.stock_code == stock_code.upper(),
        )
        .first()
    )
    if not pred:
        return None

    parsed = json.loads(pred.explanation_json) if pred.explanation_json else {}
    return {
        "stock_code": pred.stock_code,
        "sector": pred.sector,
        "year": pred.year,
        "score": pred.score,
        "rank": pred.rank,
        "confidence": pred.confidence,
        "top_contributors": parsed.get("top_contributors", []),
    }


def get_stock_explanation(db: Session, run_id: int, stock_code: str) -> dict[str, Any] | None:
    pred = (
        db.query(ForecastPrediction)
        .filter(
            ForecastPrediction.forecast_run_id == run_id,
            ForecastPrediction.stock_code == stock_code.upper(),
        )
        .first()
    )
    if not pred:
        return None
    parsed = json.loads(pred.explanation_json) if pred.explanation_json else {}
    return {
        "stock_code": pred.stock_code,
        "summary": parsed.get("summary", "No explanation available."),
        "top_contributors": parsed.get("top_contributors", []),
    }


def get_available_filters(db: Session) -> dict[str, Any]:
    rows = db.query(WinnerCohortRow.year, WinnerCohortRow.sector).distinct().all()
    years = sorted({int(r[0]) for r in rows if r[0] is not None})
    years = [y for y in years if 2020 <= y <= 2025]
    sectors = sorted({str(r[1]) for r in rows if r[1]})
    return {"years": years, "sectors": sectors}


def get_parameter_catalog() -> dict[str, Any]:
    return {"items": _PARAMETER_CATALOG}
