# Interview guide

Use these explanations to understand and demonstrate the actual implementation; do not claim unverified experience.

<!-- generated:interview-guide:start -->
## 30-second introduction

I built a retail-sales analytics and forecasting project using the UCI Online Retail II transactions from December 2009 to December 2011. I prepared product/date aggregates, wrote DuckDB SQL, and built a three-tab dashboard. I compared 6 methods across 6 retrospective periods: a four-week weekday-average baseline reduced pooled absolute error by 6.2% against last-week repetition, though daily forecast errors remained substantial.

## Two-minute explanation

The project asks what historical sales patterns are visible and how simple forecasts compare with weekly smoothing. The audit covers 1,067,371 original rows and 4,706 merchandise products. I removed cross-sheet replicas while preserving repeated lines within a sheet, kept valid sales with missing customer IDs, and calculated value as transaction-level quantity times price. SQL produces rankings, matched-period growth and calendar-aware weekday averages.

Forecasting uses a separately defined 20-product cohort, six origins, and fixed 28-day horizons. At each origin training ends the previous day. Last-week, four-week and eight-week baselines compete with expanding, 182-day and 365-day weekly smoothing. Models share the same observations and retain difficult spikes. The strongest pooled method was the four-week baseline at 103.56% WAPE, compared with 110.42% for last-week repetition. I investigated both improvements and failures rather than treating one pooled score as universal success.

The model family was selected on later-2011 validation, and some periods overlap previously inspected evaluations. These are retrospective comparisons. The original benchmark's duplicate repair also happened after its initial test was inspected. I cannot claim an independent holdout, lost demand, or business savings. I made the results inspectable through saved artifacts, tests, and exact-commit reproduction.

## Questions I should be able to answer

- **Why this dataset?** It provides real historical retail transactions with product, quantity, price and dates; it does not supply inventory or promotion evidence.
- **What SQL did I write?** Product rankings, complete-period growth, and weekday averages using joins, aggregates and window calculations. [Findings and SQL](business-findings.md).
- **Why these baselines?** Repeating last week tests weekly persistence; weekday averages reduce sensitivity to an unusual week. Their histories are fixed at 7/28/56 days.
- **How did I prevent leakage?** Pre-January cohort selection, preorigin training cutoffs, no within-horizon actual updates, and future-value perturbation tests. These prevent mechanical leakage but do not erase retrospective selection limitations.
- **Why did the simple method win?** It had the lowest measured pooled error in this comparison. Averaging is a plausible explanation for stability, not a demonstrated causal finding or guarantee on future data.
- **Why is WAPE above 100%?** It is total absolute error divided by actual units; over/underprediction magnitudes accumulate and can exceed actual demand. It is not accuracy.
- **How is value calculated?** Quantity × Price before aggregation, in GBP, with returns excluded. It is positive-sales value, not net revenue or profit.
- **What next?** A prospectively frozen design evaluated on newly available outcomes; no further tuning on these inspected windows is independent confirmation. Real inventory questions need real inventory and lost-sales data.

## Dashboard demonstration

Sales Overview shows all merchandise and the three SQL findings. Forecast Evaluation contrasts saved actuals and forecasts; use the improvement, deterioration and spike examples in [the reproducible walkthrough](dashboard-walkthrough.md). Model Performance shows cohort scores and expanded diagnostics. Product and period scores have narrower scope than the pooled result. Selectors do not refit models.
<!-- generated:interview-guide:end -->
