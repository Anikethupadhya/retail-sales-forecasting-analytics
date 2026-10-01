# Interview guide — Retail Sales Forecasting & Analytics

## Explain the business question

What happened in historical positive merchandise sales, and how well can simple
methods predict the next 28 calendar days? The project uses actual transactions
for descriptive SQL and customer-free aggregates. It forecasts observed sales;
inventory, unavailable demand and lost sales cannot be recovered from this source.

## Explain the data decisions

Both workbook sheets are inspected. The sheets overlap in December 2010; exact
cross-sheet replicas are matched using full original fields and occurrence numbers,
preserving repeated lines inside a sheet. Missing customer IDs do not exclude
valid product sales. Cancellations, negative/zero quantities, non-merchandise codes,
nonpositive prices and the final potentially truncated trading day are excluded.
Counts reconcile to the raw rows and to the corrected historical audit.

Positive-sales value is each line's Quantity × Price, summed before aggregation,
in GBP. It is not net revenue or profit. Returns are separate. All-merchandise
Overview and fixed-cohort forecasting are clearly different scopes. Calendar zeros
are observed-sales assumptions, not proof of zero demand. Daily grids include
closure days and short pre-listing periods; stock-outs cannot be identified.

## Explain the SQL

Product rankings aggregate all merchandise and use DENSE_RANK windows, joining
descriptions. Monthly trends use a calendar table and LAG to compare adjacent
complete months. Weekday averages divide by every covered calendar day, including
zero-sales dates. Comparable annual growth uses January–November in both 2010
and 2011; partial December 2011 never competes with a complete December.

## Explain the two forecasting experiments

The existing corrected benchmark contains 20 products chosen before August 19,
2011. Model family selection used three 28-day validation windows. Its final test
ran November 11–December 8. Saved predictions are immutable and reconciled to the
published 80.24% model WAPE, 112.80% baseline WAPE and 28.86% relative reduction.
The first pre-correction execution had 80.43% model WAPE and 28.70% reduction.
The cross-sheet repair was made after the first test was observed; the original
family/settings/cohort stayed fixed. Do not claim the corrected rerun was a newly
untouched test. Explain this disclosure candidly if asked.

The new robustness protocol was written and hashed before any new predictions.
It uses a separate cohort selected only before January 1, 2011, with the same
numerical eligibility criteria. Starts are January/March/May/July/September/November
1, 2011. Each history ends the previous day and expands from December 1, 2009.
Each horizon is 28 consecutive calendar days. Cohort membership differences are
saved. The model family was originally chosen using later-2011 validation and
some windows overlap prior evaluations, so this is retrospective stress testing,
not independent confirmation or a strategy chosen prospectively in January.

## Explain methods and leakage prevention

Last-week seasonal naive repeats seven observed calendar days four times. Four-
and eight-week baselines average matching weekdays over the last 28 or 56 days,
then repeat those fixed seven means throughout the horizon. The weekly smoothing
candidate uses additive seven-day seasonality without trend, estimated
initialization and optimized coefficients with use_brute=False. Its specification
stays fixed; coefficients are independently refitted at each origin. No future
parameters or within-horizon actuals enter predictions. Tests perturb future
actuals and future cohort-selection information to verify this separation.

Nonnegative clipping and the existing convergence/failure fallback rules are
prespecified. Failed fits use last-week forecasts with status and warnings saved;
difficult products and spikes are not dropped. Baseline implementation errors
abort instead of silently falling back.

## Explain the metrics

MAE is units per product-day. Pooled WAPE is 100 times summed absolute error over
summed actual units. Overall robustness pools every product-day across six periods,
never averages period WAPE percentages. Mean product WAPE weights products equally
and excludes explicitly undefined percentages. Signed bias is mean(prediction −
actual); positive values mean overprediction. Percentage bias divides summed signed
error by actual units. Zero denominators produce null percentages. Relative WAPE
reduction preserves negative values and is undefined if baseline WAPE is zero.

Each named baseline has separate product wins/losses/ties/undefined comparisons.
Wins use strictly lower absolute error; for positive actual totals this agrees
with comparing product WAPE. Ties have a fixed 1e-9-unit tolerance. WAPE can exceed
100%; neither WAPE nor 100 minus WAPE is accuracy.

## Explain the measured outcome honestly

Read the current README and outputs/robustness/overall_metrics.csv for exact
measurements. Weekly smoothing improved the preserved holiday benchmark, but
the stronger robustness comparison can favour simple weekday averages. This is
useful evidence: a more sophisticated model does not automatically add value.
Do not combine improvements across experiments with different cohorts and dates.
The resume evidence maps numerical claims to separate named artifacts.

## Explain error analysis

Five improvements and five deteriorations are ranked by baseline-minus-model
absolute-error units. Contributions reconcile to pooled error reduction, with
negative shares preserved. Signed errors distinguish over- and underprediction.
Spike thresholds are product training-history 99th percentiles through the
benchmark origin, with linear interpolation and calendar zeros. Observed spikes
remain in primary errors; promotions, wholesale motives and availability are
possible causes that these aggregates do not establish.

## Explain verification and limits

Meaningful checks cover dates, weekday arithmetic, future-information independence,
metric calculations, SQL completeness, aggregate reconciliation, archive checksums
and dashboard controls. A separate environment rebuilds from the original workbook
with empty processed caches, then reruns tests and reconciles outputs under explicit
tolerances. Browser inspection provides readable screenshots of all three tabs.

The source is historical, cohorts favour high-volume products, and six windows in
one year do not demonstrate future or universal performance. There are no actual
inventory observations, lost-sales labels, promotions or calibrated intervals.
The next experiment is proposed in the README from the measured results; this
project does not add extra models or retune the frozen comparison.

## Training-window experiment interview notes

The question was whether old history hurt the existing weekly smoothing model. I froze expanding, trailing 182 days (26 weeks), and trailing 365 days before execution. I kept the same 20 products, six origins, 28-day horizons, observed-sales target, model settings, clipping and last-week fallback. The three baselines kept their own 7/28/56-day histories.

The 182-day history reached 103.976880% pooled WAPE versus 104.519041% expanding, a 0.518720% relative reduction. It improved 2/6 periods and 9/20 combined-product comparisons. The 365-day history was worse at 107.652765%. The 4-week weekday baseline remained best at 103.558688%, so I would not claim that exponential smoothing was the strongest model. Near-zero average bias did not mean small absolute errors.

All six methods had identical 3,360-row support, or 20,160 predictions in total. Expanding and unchanged baselines reconciled against prior results. Shared preorigin expanding-history spike thresholds prevented different windows from labeling different observations. Every spike and fallback would stay in primary scores; this real run needed no fallback.

The family had been selected on later-2011 validation. These historical windows overlap inspected evaluations, so this is retrospective analysis rather than a fresh holdout. The original corrected benchmark is a separate cohort and disclosed ingestion repair; I do not blend its stronger score with these results.

Engineering evidence includes fresh committed clones, new environments, empty caches, raw checksum verification, rebuilt DuckDB SQL, numerical reconciliation, leakage/failure fixtures, saved-output integration and dashboard checks. Fast CI uses customer-free aggregates and temporary databases, while full reproduction actually reads the official workbook. Meaningful commits record completed milestones; a pushed feature branch and draft PR keep main available for review.

See training-window-experiment.md for artifacts, contributions, limitations and exact result fields. No financial savings, inventory improvement, promotion cause or demand lost during stock-outs is supported by these records.
