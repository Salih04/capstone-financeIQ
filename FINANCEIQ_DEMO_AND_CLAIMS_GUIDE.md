# FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md

Demo-safe narrative and claim boundaries. Every number here comes from committed repo evidence (`data/trusted_clean/data_quality_report.md`, `experiments/leaderboard.csv`, and the dated `docs/VERIFICATION_BASELINE.md`). Nothing in this guide is investment advice, and the product must never be presented as such.

## 1. One-sentence product explanation

FinanceIQ is an academic decision-support research terminal that analyzes historical fundamentals of BIST companies (2020–2025) through a leakage-safe, no-fabrication data pipeline — and transparently reports that next-year returns were **not** reliably predictable from that data.

## 2. What the project actually demonstrates

- Engineering: a full-stack system (FastAPI + Postgres backend, React research terminal, reproducible Makefile pipeline, and two green automated suites; cite `docs/VERIFICATION_BASELINE.md` for the current counts).
- Data forensics: automated detection that the vendor's "historical" fundamentals were a frozen 2025 snapshot (per-ticker evidence in `frozen_column_evidence.md`), followed by rebuilding trustworthy yearly data from corrected files, free Yahoo prices, and manual share counts.
- Methodological honesty: walk-forward, leakage-controlled evaluation whose result (Spearman IC ≈ 0, per-split range −0.17 to +0.22 across 2023–2025; baselines match or beat ML) is displayed in the product instead of hidden.
- Explainability: every ranking decomposes into named feature weights, confidence components, and data-quality caveats.

## 3. What the project does not prove

It does not prove any ability to predict stock returns, pick winners, or beat the market. It does not prove the methods would work with more data. It does not prove production readiness (deployment liveness unverified). Absence of signal in this small dataset also does not prove markets are unpredictable — the sample (≈40–81 companies, 5 yearly observations, one high-inflation Turkish macro regime) supports no such general claim in either direction.

## 4. Safe demo narrative

"We set out to test whether freely available yearly fundamentals could predict next-year BIST returns. Building the pipeline, we discovered our vendor data was largely a single frozen snapshot — our validation gates caught it automatically. We rebuilt honest yearly data from corrected sources, ran walk-forward experiments against naive baselines, and got a clear answer: no reliable predictive signal at this data scale. So the product is deliberately a *research support* tool: it ranks and explains, shows its uncertainty, and refuses to pretend precision. The negative result is the finding, and the system is built to defend it."

## 5. Unsafe demo claims to avoid

- "The model predicts / identifies winning stocks." (It doesn't; IC ≈ 0.)
- Any accuracy/hit-rate number as an achievement — precision@5 at n=40 moves 20 points per stock; per-split positive ICs are noise.
- "Trained an AI on financial data to forecast prices." (The LLM layer is explanation-only; the numeric models showed no edge.)
- "With more data this will predict returns." (Say: "the pipeline is *ready* for more data" — capability of the pipeline, not a promised result.)
- "Deployed in production / ready for investors." (Unverified / false.)
- Any suggested buy/sell/hold, any named stock as "a good pick."

## 6. Recommended Turkish explanation (jury/demo)

"FinanceIQ, Borsa İstanbul şirketlerinin 2020–2025 yıllık finansal verileri üzerinde çalışan akademik bir karar destek prototipidir. Projenin temel katkısı yöntemseldir: veri doğrulama hattımız, satıcı verisinin büyük kısmının tek bir dondurulmuş anlık görüntü olduğunu otomatik tespit etti; güvenilir veriyi düzeltilmiş kaynaklardan yeniden inşa ettik. Sızıntı korumalı, ileriye dönük (walk-forward) deneylerimizin sonucu net: bu ölçekteki veriyle gelecek yıl getirileri güvenilir şekilde tahmin edilemiyor (Spearman korelasyonu sıfıra yakın). Bu 'olumsuz' sonucu gizlemek yerine ürünün merkezine koyduk — sistem tahmin motoru değil, her skoru bileşenleriyle ve belirsizliğiyle birlikte açıklayan bir araştırma destek aracıdır. Yatırım tavsiyesi değildir."

## 7. Recommended English explanation (portfolio/CV)

"Built FinanceIQ, a full-stack equity-research platform (FastAPI, PostgreSQL, React) with a reproducible, leakage-safe data pipeline for Turkish (BIST) equities. The pipeline's validation gates automatically detected that vendor fundamentals were a frozen snapshot; I rebuilt trustworthy yearly data from corrected sources and free price data. Walk-forward experiments against naive baselines produced a defensible negative result (rank IC ≈ 0), which the product reports transparently — the system is designed as explainable decision support with explicit uncertainty, not as a return predictor."

## 8. Recommended UI disclaimer text

Primary (already the API's hardcoded pattern; keep consistent): **"Experimental ranking signal — research support only, NOT investment advice. Do not use for buy/sell/hold decisions."**
Secondary scope line for ranking views (task UI-02): **"Based on ~40 public BIST companies, yearly data 2020–2025, nominal TRY returns during a high-inflation period. Historical patterns; no validated predictive skill (walk-forward IC ≈ 0)."**

## 9. Recommended README wording

Keep the existing "research support, not investment advice" framing (already present). If the README's top section is revised, lead with: "An honest, leakage-safe equity-research system whose headline finding is negative: free yearly fundamentals did not reliably predict next-year BIST returns. The product demonstrates the pipeline, the validation, and the transparent reporting — not a predictive edge."

## 10. How to explain the limited dataset

"Yearly statements only, 2020–2025, for 40 public companies plus an 81-ticker internal training universe — 321 usable company-year observations with targets. That is far below what return-prediction ML normally requires, which is precisely why we evaluate against naive baselines and report the signal as weak. We chose depth of validation over breadth of data: every value is real, sourced, and auditable."

## 11. How to explain model uncertainty

"Our headline metric, Spearman rank correlation between predicted and realized next-year returns, remains weak and swings roughly from −0.17 to +0.22 across test years. The persisted evaluation has 80 tickers per model and year but only three test years. At 80% power and two-sided α=0.05, the committed Fisher-z analysis could detect about |IC| 0.309 in one 80-row year or 0.182 across the three-year design; the seeded simulation gives 0.802 and 0.810 power at those thresholds. The public-40 sensitivity is coarser: about 0.431 for one year and 0.260 across three. Those are design limits, not estimates of the true IC, hard significance cutoffs, or evidence of investment relevance. After correcting the six-model search, no ML model is statistically distinguishable from the within-year null. So instead of point forecasts we show rankings with confidence components, flag inference-only rows, and down-weight our own scores for the weak backtest." (Numbers: `experiments/results/significance_report.md` and `.json`. The power calculation is for one prespecified α=0.05 test; it is not Bonferroni-adjusted family-wise power.)

## 12. How to explain the rule-based fallback

"The serving layer is deliberately deterministic: it measures which fundamental characteristics historically co-occurred with top-quartile performers and produces an explainable weighted ranking — no black box. The optional LLM layer only writes explanations, never numbers, and the system runs fully without it (`RESEARCH_LLM_PROVIDER=none` gives a deterministic fallback). If any component fails, the honest baseline still works." (This is implemented, per `forecasting_csv_service.py` and the research-agent fallback — not just recommended.)

## 13. How to explain success criteria

"Success was defined as methodological, not financial: a reproducible pipeline with all validation gates passing, no fabricated values anywhere, leakage-controlled evaluation, and every surfaced score carrying its components and caveats. Against those criteria the project succeeds — including succeeding at honestly measuring that predictive power is absent."

## 14. How to answer "Is this investment advice?"

"No, categorically. The system's own evaluation shows no reliable predictive edge, and every surface says 'research support, not investment advice.' It's an academic prototype for exploring and explaining historical data. No one should make buy or sell decisions with it, and it refuses to produce buy/sell/hold signals or price targets by design."

## 15. Final presentation checklist

- [ ] `make data-validate` matches the current result in `docs/VERIFICATION_BASELINE.md`.
- [ ] Root and backend suites match the current green results in `docs/VERIFICATION_BASELINE.md`.
- [ ] Backend running with real CSV data — confirm a page shows live data, not demo fallback.
- [ ] Frontend production build re-run before presenting (the production build was verified green during Phase 2).
- [ ] Frozen-snapshot evidence page ready to show (best "wow" moment: the pipeline catching bad vendor data).
- [ ] IC ≈ 0 chart ready, with the §11 uncertainty explanation rehearsed.
- [ ] §14 answer rehearsed; §5 forbidden claims reviewed by everyone presenting.
- [ ] No slide or sentence promises future predictive performance.
