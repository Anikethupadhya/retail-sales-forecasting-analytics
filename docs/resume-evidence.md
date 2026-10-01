# Resume evidence

Proposed wording and numerical claim mappings are generated from authoritative artifacts.

<!-- generated:resume-evidence:start -->
## Proposed bullets

- Audited 1,067,371 UCI transaction rows and built a Python/pandas and DuckDB pipeline covering 4,706 products, with SQL sales analysis and a three-tab Streamlit/Plotly dashboard.
- Compared 6 sales forecasting methods across 20 products and 6 retrospective 28-day periods; the four-week weekday-average baseline reduced pooled absolute error by 6.2% versus last-week repetition.

Optional engineering alternative: Built a reproducible retail-sales portfolio with mandatory fixture, saved-output integration, and dashboard checks; verified an exact committed implementation in a fresh environment against protected historical evidence.

## Claim mapping

| Claim | Artifact, key and field/calculation |
| --- | --- |
| 1,067,371 rows; 4,706 products | outputs/sales/data_audit.json: raw_rows, product_count |
| Three dashboard tabs | app.py; tests/test_dashboard.py: test_tabs_experiments_products_periods_and_scopes |
| Six methods; 20 products; six 28-day periods | outputs/portfolio/summary.json: methods, products, periods, horizon_days; underlying frozen protocols and predictions |
| 6.2% relative error reduction | outputs/training_windows_v1/overall_metrics.csv: model=weekday_mean_4w / seasonal_naive, absolute_error_sum; 100 × (comparator − candidate) / comparator |
| 103.56% versus 110.42% WAPE | Same rows: wape; pooled identical observations |
| 6.857893 percentage points | comparator wape − candidate wape; distinct from relative reduction |
| Business findings | outputs/sales/findings.json: values, source, row, source_fields, sql, numerator, denominator |

Full-precision relative reduction: 6.210927050108036%. [Machine-readable claim summary](../outputs/portfolio/summary.json). Technologies actually executed: Python, pandas, DuckDB, statsmodels, Streamlit, Plotly and pytest.

The original corrected 28.86% result belongs to a different single-period cohort and followed duplicate repair after initial test inspection. Later-2011 model-family selection and overlapping inspected evaluations make the six-period comparison retrospective, not an untouched holdout. Neither WAPE nor 100 − WAPE is accuracy. No deployment, net revenue, inventory management, savings or significance is claimed. Current verification lives in outputs/verification/portfolio; older evidence remains dated and separate.
<!-- generated:resume-evidence:end -->
