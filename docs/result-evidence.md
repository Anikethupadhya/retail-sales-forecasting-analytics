# Result evidence

<!-- generated:result-evidence:start -->
## Data and evaluation scope

The audit contains 1,067,371 source transaction rows and 4,706 cleaned merchandise products. The forecasting comparison is a separate cohort: 6 methods, 20 products, and 6 retrospective 28-day periods.

## Result sources

| Measurement | Artifact and field/calculation |
| --- | --- |
| Source rows and merchandise products | [Data audit](../outputs/sales/data_audit.json): raw_rows, product_count |
| Methods, products, periods and horizon | [Evaluation summary](../outputs/portfolio/summary.json): methods, products, periods, horizon_days |
| 6.2% relative error reduction | [Overall metrics](../outputs/training_windows_v1/overall_metrics.csv): weekday_mean_4w and seasonal_naive absolute_error_sum; 100 × (comparator − candidate) / comparator |
| 103.56% versus 110.42% WAPE | Same metric rows: wape; identical pooled observations |
| 6.857893 percentage points | Comparator WAPE − candidate WAPE; distinct from relative reduction |
| Three sales findings | [Finding definitions](../outputs/sales/findings.json): values, source, row, source_fields, sql, numerator, denominator |

Full-precision relative reduction: 6.210927050108036%. The four-week weekday-average baseline is compared with last-week repetition. WAPE is total absolute error divided by actual units; it is not accuracy.

## Interpretation

The original corrected 28.86% result belongs to a different single-period cohort and followed duplicate repair after initial test inspection. Later-2011 model-family selection and overlapping inspected evaluations make the six-period comparison retrospective, rather than an untouched holdout. Positive-sales value excludes returns and is not net revenue or profit. These results do not establish operational savings or statistical significance.
<!-- generated:result-evidence:end -->
