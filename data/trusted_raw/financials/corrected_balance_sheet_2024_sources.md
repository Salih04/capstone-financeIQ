# corrected_balance_sheet_2024_sources.md

Source basis: Values were assembled from the Claude research output provided in the chat and accepted by the user as primary source. The stated source was StockAnalysis.com / S&P Global Market Intelligence balance-sheet pages.

General unit handling:
- Most companies: StockAnalysis values stated as millions TRY; converted to raw TL by multiplying by 1,000,000.
- ENKAI and THYAO: StockAnalysis values stated as millions USD; converted to raw TL using USDTRY 35.3654, then multiplied by 1,000,000.
- TAVHL: StockAnalysis values stated as millions EUR; converted to raw TL using EURTRY 36.90, then multiplied by 1,000,000.
- MAVI: FY2025 ending Jan 31, 2025 was used as closest full fiscal year corresponding to 2024 operations, based on the user-provided Claude output.

Derived fields:
- working_capital = current_assets - short_term_liabilities
- current_ratio = current_assets / short_term_liabilities
- leverage_ratio = (short_term_liabilities + long_term_liabilities) / total_assets
- financial_debt_ratio left blank for all rows because clean total financial debt was not available consistently from the provided output.
- net_debt_to_ebitda derived only where the user-provided trusted 2024 EBITDA value was positive and available.

Caveats:
- TSKB is a bank/development bank and TURSG is an insurance company; their current/non-current balance-sheet structure may not be directly comparable with industrial companies.
- Net debt sign convention used here: net_debt = total financial debt - cash. Net cash is stored as negative net_debt.
