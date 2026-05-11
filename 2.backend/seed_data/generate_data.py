"""
Deprecated: This generator is no longer used.
The app now relies solely on datasets in 3.Datasets.
"""
import csv
import os

OUT = os.path.join(os.path.dirname(__file__), "financial_data.csv")

COLS = [
    "ticker", "period", "revenue", "net_income", "total_assets",
    "total_equity", "total_liabilities", "current_assets", "current_liabilities",
    "cash", "operating_cash_flow", "operating_income", "gross_profit", "inventory",
]

def r(v): return int(round(v))

# ── Quarterly multipliers inside a year (Q4=1.0 is the base) ───────────────
QM = {1: 0.68, 2: 0.82, 3: 0.92, 4: 1.00}

# ── YoY revenue growth factors (TRY nominal; Turkish inflation era) ─────────
# year_growth[y] = multiplier from that year to next
YEAR_GROWTH = {2022: 1.72, 2023: 1.48, 2024: 1.32}

def scale_year(base_2023q4_rev, target_year):
    """Scale 2023/12 revenue to a given year's Q4 baseline."""
    v = base_2023q4_rev
    if target_year < 2023:
        for y in range(target_year, 2023):
            v /= YEAR_GROWTH[y]
    elif target_year > 2023:
        for y in range(2023, target_year):
            v *= YEAR_GROWTH[y]
    return v

def build_row(ticker, year, quarter, base):
    """
    base = dict with 2023/12 financials.
    Scale everything proportionally to revenue scale factor.
    """
    yr_rev = scale_year(base["rev"], year)
    q_rev  = yr_rev * QM[quarter]
    sf     = q_rev / base["rev"]          # scale factor relative to 2023Q4

    # Margins/ratios stay roughly stable with slight realism tweaks
    ni  = q_rev * base["ni_margin"]
    oi  = q_rev * base["oi_margin"]
    gp  = q_rev * base["gp_margin"]
    ocf = ni * base["ocf_ni_ratio"]

    # Balance sheet grows with revenue but more slowly (1-year lag)
    bs_sf = scale_year(base["rev"], year) / base["rev"]
    bs_q  = (0.75 + 0.25 * QM[quarter])   # BS doesn't swing as much quarterly
    ta  = base["ta"]  * bs_sf * bs_q
    eq  = base["eq"]  * bs_sf * bs_q
    tl  = ta - eq
    ca  = base["ca"]  * bs_sf * bs_q
    cl  = base["cl"]  * bs_sf * bs_q
    csh = base["csh"] * bs_sf * bs_q
    inv = base["inv"] * bs_sf * bs_q * QM[quarter]

    return [
        ticker, f"{year}Q{quarter}",
        r(q_rev), r(ni), r(ta), r(eq), r(tl),
        r(ca), r(cl), r(csh), r(ocf), r(oi), r(gp), r(inv),
    ]

# ── Company definitions (2023Q4 base, then ratios) ─────────────────────────
# Keys: rev=Q4 revenue, ni_margin, oi_margin, gp_margin, ocf_ni_ratio,
#       ta, eq, ca, cl, csh, inv (all 2023Q4 absolute values)

COMPANIES = {
    # ── Already in CSV ──────────────────────────────────────────────────────
    "ASELS": dict(rev=12.5e9, ni_margin=0.150, oi_margin=0.180, gp_margin=0.280,
                  ocf_ni_ratio=1.20, ta=25e9, eq=12.5e9, ca=8.75e9, cl=5.0e9,
                  csh=2.5e9, inv=2.625e9),
    "THYAO": dict(rev=95e9,  ni_margin=0.100, oi_margin=0.120, gp_margin=0.220,
                  ocf_ni_ratio=1.50, ta=180e9, eq=55e9, ca=45e9, cl=38e9,
                  csh=12e9, inv=4.5e9),
    "EREGL": dict(rev=42e9,  ni_margin=0.150, oi_margin=0.170, gp_margin=0.240,
                  ocf_ni_ratio=1.20, ta=85e9, eq=52e9, ca=28e9, cl=14e9,
                  csh=9.5e9, inv=9.8e9),
    "BIMAS": dict(rev=65e9,  ni_margin=0.035, oi_margin=0.060, gp_margin=0.180,
                  ocf_ni_ratio=1.50, ta=32e9, eq=12e9, ca=18e9, cl=15e9,
                  csh=3.5e9, inv=9.0e9),
    "KCHOL": dict(rev=285e9, ni_margin=0.100, oi_margin=0.120, gp_margin=0.200,
                  ocf_ni_ratio=1.50, ta=650e9, eq=210e9, ca=120e9, cl=90e9,
                  csh=35e9, inv=18e9),
    "SISE":  dict(rev=38e9,  ni_margin=0.150, oi_margin=0.170, gp_margin=0.260,
                  ocf_ni_ratio=1.20, ta=92e9, eq=58e9, ca=26e9, cl=12e9,
                  csh=8.5e9, inv=6.5e9),
    "GARAN": dict(rev=48e9,  ni_margin=0.300, oi_margin=0.350, gp_margin=0.600,
                  ocf_ni_ratio=1.50, ta=850e9, eq=95e9, ca=320e9, cl=290e9,
                  csh=45e9, inv=0),
    "FROTO": dict(rev=55e9,  ni_margin=0.120, oi_margin=0.140, gp_margin=0.200,
                  ocf_ni_ratio=1.50, ta=95e9, eq=38e9, ca=32e9, cl=22e9,
                  csh=8.0e9, inv=12.8e9),
    "AKBNK": dict(rev=42e9,  ni_margin=0.300, oi_margin=0.350, gp_margin=0.600,
                  ocf_ni_ratio=1.50, ta=780e9, eq=88e9, ca=295e9, cl=268e9,
                  csh=38e9, inv=0),
    # ── New companies ───────────────────────────────────────────────────────
    "TTKOM": dict(rev=48e9,  ni_margin=0.140, oi_margin=0.220, gp_margin=0.380,
                  ocf_ni_ratio=2.50, ta=105e9, eq=32e9, ca=22e9, cl=18e9,
                  csh=6.0e9, inv=1.5e9),
    "TCELL": dict(rev=52e9,  ni_margin=0.160, oi_margin=0.230, gp_margin=0.400,
                  ocf_ni_ratio=2.50, ta=115e9, eq=38e9, ca=25e9, cl=20e9,
                  csh=7.5e9, inv=2.0e9),
    "TUPRS": dict(rev=320e9, ni_margin=0.060, oi_margin=0.080, gp_margin=0.120,
                  ocf_ni_ratio=1.80, ta=180e9, eq=75e9, ca=85e9, cl=65e9,
                  csh=18e9, inv=38e9),
    "PETKM": dict(rev=65e9,  ni_margin=0.080, oi_margin=0.110, gp_margin=0.180,
                  ocf_ni_ratio=1.40, ta=95e9, eq=42e9, ca=32e9, cl=28e9,
                  csh=8.5e9, inv=14e9),
    "MGROS": dict(rev=78e9,  ni_margin=0.030, oi_margin=0.055, gp_margin=0.200,
                  ocf_ni_ratio=1.60, ta=42e9, eq=15e9, ca=22e9, cl=19e9,
                  csh=4.5e9, inv=11e9),
    "TOASO": dict(rev=62e9,  ni_margin=0.110, oi_margin=0.130, gp_margin=0.190,
                  ocf_ni_ratio=1.40, ta=88e9, eq=34e9, ca=28e9, cl=20e9,
                  csh=7.2e9, inv=14.5e9),
    "ARCLK": dict(rev=115e9, ni_margin=0.055, oi_margin=0.085, gp_margin=0.280,
                  ocf_ni_ratio=1.20, ta=185e9, eq=68e9, ca=92e9, cl=72e9,
                  csh=12e9, inv=32e9),
    "VESTL": dict(rev=95e9,  ni_margin=0.045, oi_margin=0.075, gp_margin=0.240,
                  ocf_ni_ratio=1.10, ta=145e9, eq=48e9, ca=72e9, cl=58e9,
                  csh=9.5e9, inv=28e9),
    "ULKER": dict(rev=42e9,  ni_margin=0.095, oi_margin=0.130, gp_margin=0.290,
                  ocf_ni_ratio=1.30, ta=68e9, eq=28e9, ca=25e9, cl=18e9,
                  csh=5.5e9, inv=8.5e9),
    "AEFES": dict(rev=55e9,  ni_margin=0.090, oi_margin=0.140, gp_margin=0.450,
                  ocf_ni_ratio=1.60, ta=92e9, eq=38e9, ca=28e9, cl=20e9,
                  csh=7.0e9, inv=12e9),
    "PGSUS": dict(rev=58e9,  ni_margin=0.110, oi_margin=0.130, gp_margin=0.250,
                  ocf_ni_ratio=1.80, ta=95e9, eq=22e9, ca=32e9, cl=28e9,
                  csh=14e9, inv=2.5e9),
    "ENKAI": dict(rev=72e9,  ni_margin=0.200, oi_margin=0.230, gp_margin=0.380,
                  ocf_ni_ratio=1.10, ta=205e9, eq=145e9, ca=62e9, cl=22e9,
                  csh=28e9, inv=4.5e9),
    "LOGO":  dict(rev=4.5e9, ni_margin=0.220, oi_margin=0.270, gp_margin=0.700,
                  ocf_ni_ratio=1.20, ta=9.5e9, eq=6.5e9, ca=5.2e9, cl=2.8e9,
                  csh=2.2e9, inv=0),
    "TAVHL": dict(rev=38e9,  ni_margin=0.180, oi_margin=0.250, gp_margin=0.550,
                  ocf_ni_ratio=1.80, ta=95e9, eq=32e9, ca=22e9, cl=18e9,
                  csh=10e9, inv=0),
    "SASA":  dict(rev=48e9,  ni_margin=0.130, oi_margin=0.180, gp_margin=0.320,
                  ocf_ni_ratio=1.30, ta=125e9, eq=58e9, ca=42e9, cl=32e9,
                  csh=8.0e9, inv=18e9),
    "KRDMD": dict(rev=28e9,  ni_margin=0.110, oi_margin=0.140, gp_margin=0.220,
                  ocf_ni_ratio=1.20, ta=55e9, eq=28e9, ca=18e9, cl=12e9,
                  csh=4.5e9, inv=7.5e9),
}

YEARS   = [2022, 2023, 2024, 2025]
QUARTERS = [1, 2, 3, 4]

rows = []
for ticker, base in COMPANIES.items():
    for year in YEARS:
        for quarter in QUARTERS:
            if year == 2025 and quarter > 2:
                continue   # only 2025Q1–Q2 available
            rows.append(build_row(ticker, year, quarter, base))

# Sort: ticker → year → quarter
rows.sort(key=lambda r: (r[0], r[1]))

with open(OUT, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(COLS)
    writer.writerows(rows)

print(f"✅ Wrote {len(rows)} rows to {OUT}")
print(f"   Companies: {len(COMPANIES)}")
print(f"   Periods per company: up to {len(YEARS)*4 - 2} quarters")
