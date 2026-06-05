# Frozen-column evidence (for the data provider)

Columns are valuable in theory but are REJECTED because the current files appear to contain a repeated point-in-time snapshot: per ticker the value is identical across all periods, so the column carries no historical T->T+1 signal.

**Verdict:** Some columns vary across periods; see per-column detail.

| column | yearly frozen | quarterly frozen | ASELS unique vals (yearly) |
|---|---|---|---|
| `pe_ratio` | 40/40 | 78/78 | 1 |
| `pb_ratio` | 40/40 | 78/78 | 1 |
| `ev_ebitda` | 40/40 | 78/78 | 1 |
| `roe` | 40/40 | 78/78 | 1 |
| `roa` | 40/40 | 78/78 | 1 |
| `gross_margin` | 40/40 | 78/78 | 1 |
| `ebitda_margin` | 40/40 | 78/78 | 1 |
| `net_margin` | 38/40 | 78/78 | 1 |
| `market_cap` | 40/40 | 78/78 | 1 |
| `enterprise_value` | 40/40 | 78/78 | 1 |
| `revenue` | 40/40 | 78/78 | 1 |
| `ebitda` | 40/40 | 78/78 | 1 |
| `net_income` | 40/40 | 78/78 | 1 |
| `price` | 40/40 | 78/78 | 1 |
| `total_assets` | 0/40 | 78/78 | 2 |

## Representative tickers (yearly values across years)

- `pe_ratio` AEFES: single value [12.55] repeated every year → frozen
- `pe_ratio` ASELS: single value [53.95] repeated every year → frozen
- `pe_ratio` BIMAS: single value [23.88] repeated every year → frozen
- `pe_ratio` THYAO: single value [3.27] repeated every year → frozen
- `pe_ratio` TUPRS: single value [17.69] repeated every year → frozen
- `pb_ratio` AEFES: single value [1.03] repeated every year → frozen
- `pb_ratio` ASELS: single value [6.82] repeated every year → frozen
- `pb_ratio` BIMAS: single value [2.69] repeated every year → frozen
- `pb_ratio` THYAO: single value [0.44] repeated every year → frozen
- `pb_ratio` TUPRS: single value [1.43] repeated every year → frozen
- `ev_ebitda` AEFES: single value [4.24] repeated every year → frozen
- `ev_ebitda` ASELS: single value [35.91] repeated every year → frozen
- `ev_ebitda` BIMAS: single value [11.12] repeated every year → frozen
- `ev_ebitda` THYAO: single value [5.65] repeated every year → frozen
- `ev_ebitda` TUPRS: single value [7.49] repeated every year → frozen
- `roe` AEFES: single value [8.19] repeated every year → frozen
- `roe` ASELS: single value [14.61] repeated every year → frozen
- `roe` BIMAS: single value [11.66] repeated every year → frozen
- `roe` THYAO: single value [15.43] repeated every year → frozen
- `roe` TUPRS: single value [8.05] repeated every year → frozen
- `roa` AEFES: single value [2.05] repeated every year → frozen
- `roa` ASELS: single value [8.47] repeated every year → frozen
- `roa` BIMAS: single value [5.76] repeated every year → frozen
- `roa` THYAO: single value [7.04] repeated every year → frozen
- `roa` TUPRS: single value [4.98] repeated every year → frozen
- `gross_margin` AEFES: single value [37.7] repeated every year → frozen
- `gross_margin` ASELS: single value [30.72] repeated every year → frozen
- `gross_margin` BIMAS: single value [19.34] repeated every year → frozen
- `gross_margin` THYAO: single value [8.36] repeated every year → frozen
- `gross_margin` TUPRS: single value [9.78] repeated every year → frozen
- `ebitda_margin` AEFES: single value [16.22] repeated every year → frozen
- `ebitda_margin` ASELS: single value [25.16] repeated every year → frozen
- `ebitda_margin` BIMAS: single value [6.03] repeated every year → frozen
- `ebitda_margin` THYAO: single value [8.24] repeated every year → frozen
- `ebitda_margin` TUPRS: single value [7.48] repeated every year → frozen
- `net_margin` AEFES: single value [3.67] repeated every year → frozen
- `net_margin` ASELS: single value [16.15] repeated every year → frozen
- `net_margin` BIMAS: single value [2.58] repeated every year → frozen
- `net_margin` THYAO: single value [3.84] repeated every year → frozen
- `net_margin` TUPRS: single value [3.56] repeated every year → frozen
- `market_cap` AEFES: single value [112381578917.4] repeated every year → frozen
- `market_cap` ASELS: single value [1916340000000.0] repeated every year → frozen
- `market_cap` BIMAS: single value [444900000000.0] repeated every year → frozen
- `market_cap` THYAO: single value [425385000000.0] repeated every year → frozen
- `market_cap` TUPRS: single value [522161607058.0] repeated every year → frozen
- `enterprise_value` AEFES: single value [167765622917.4] repeated every year → frozen
- `enterprise_value` ASELS: single value [1938424087000.0] repeated every year → frozen
- `enterprise_value` BIMAS: single value [483474474000.0] repeated every year → frozen
- `enterprise_value` THYAO: single value [955779000000.0] repeated every year → frozen
- `enterprise_value` TUPRS: single value [465173846058.0] repeated every year → frozen
- `revenue` AEFES: single value [243847131000.0] repeated every year → frozen
- `revenue` ASELS: single value [34305800000.0] repeated every year → frozen
- `revenue` BIMAS: single value [721062506000.0] repeated every year → frozen
- `revenue` THYAO: single value [257961000000.0] repeated every year → frozen
- `revenue` TUPRS: single value [830356131000.0] repeated every year → frozen
- `ebitda` AEFES: single value [39545145000.0] repeated every year → frozen
- `ebitda` ASELS: single value [8632803000.0] repeated every year → frozen
- `ebitda` BIMAS: single value [43484618000.0] repeated every year → frozen
- `ebitda` THYAO: single value [21261000000.0] repeated every year → frozen
- `ebitda` TUPRS: single value [62072685000.0] repeated every year → frozen
- `net_income` AEFES: single value [8956856000.0] repeated every year → frozen
- `net_income` ASELS: single value [5539312000.0] repeated every year → frozen
- `net_income` BIMAS: single value [18632108000.0] repeated every year → frozen
- `net_income` THYAO: single value [9915000000.0] repeated every year → frozen
- `net_income` TUPRS: single value [29523183000.0] repeated every year → frozen
- `price` AEFES: single value [18.98] repeated every year → frozen
- `price` ASELS: single value [420.25] repeated every year → frozen
- `price` BIMAS: single value [741.5] repeated every year → frozen
- `price` THYAO: single value [308.25] repeated every year → frozen
- `price` TUPRS: single value [271.0] repeated every year → frozen