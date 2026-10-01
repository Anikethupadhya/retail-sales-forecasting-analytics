# Training-window experiment

The best observed smoothing history was `hw_182d` at **103.976880% pooled WAPE**, versus **104.519041%** with expanding history. This is a **0.518720% relative reduction** (0.542161 percentage points), winning in **2/6 periods** and **9/20 products** across combined periods. The strongest baseline remains `weekday_mean_4w` at **103.558688%**, below every smoothing variant. A shorter history produced a small pooled improvement, with mixed period/product results; it does not establish a generally superior model.

## Fixed design and provenance

Retrospective question: does limiting training history improve the unchanged additive weekly exponential-smoothing specification? Same fixed 20-product cohort selected exclusively before 2011-01-01; six origins January 1, March 1, May 1, July 1, September 1 and November 1, 2011; 28 consecutive calendar days per origin. Each method has **3,360 predictions**, giving **20,160 rows** across six methods. Actual units total **220,053 per method**. Calendar zeros and every valid large spike remain.

Expanding history begins 2009-12-01. For start F, the trailing histories are F−182 through F−1 and F−365 through F−1 inclusive. 182 days is exactly 26 weeks. Parameters are independently refitted at each origin, with no horizon updates; additive seasonality, seven-day period, no trend, estimated initialization, optimized fit and use_brute=False remain frozen. The three baselines use only the preceding 7, 28 and 56 calendar days respectively and are calculated once per product/origin.

Authoritative protocol: `protocols/training_windows_v1.json`; SHA-256 `58368645b26b573f1dfb22163d60d2722b877f2ec550c2a25ecf45a448613461`. Protocol commit: `c330d22855930481638a5339f8103e15b9cf5295`, preceding real-data execution. Execution revision and source/input checksums are in `experiment_manifest.json`; an initial development run may record dirty implementation inputs explicitly. Final clean verification identifies its exact tested revision separately from the final evidence-only branch head.

Expanding predictions and all baselines reconcile against the saved robustness implementation, including fit statuses, within rtol=1e-10 and atol=1e-8: `reference_reconciliation.json`. No products, periods or failures were dropped.

## Pooled outcomes

| model | mae | wape | mean_product_wape | signed_bias | percentage_bias | overprediction_units | underprediction_units |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hw_182d | 68.10 | 103.98 | 119.07 | -0.19 | -0.29 | 114,084.90 | 114,719.35 |
| hw_365d | 70.50 | 107.65 | 135.50 | 7.81 | 11.93 | 131,567.58 | 105,325.56 |
| hw_expanding | 68.45 | 104.52 | 138.18 | 3.78 | 5.77 | 121,345.33 | 108,651.95 |
| seasonal_naive | 72.31 | 110.42 | 110.18 | -22.35 | -34.13 | 83,933.00 | 159,042.00 |
| weekday_mean_4w | 67.82 | 103.56 | 112.25 | -8.00 | -12.22 | 100,495.00 | 127,389.00 |
| weekday_mean_8w | 68.71 | 104.91 | 113.78 | 0.53 | 0.82 | 116,322.25 | 114,526.75 |

WAPE is `100 × summed absolute error / summed actual units`, pooled across all six periods. It is normalized absolute error and can exceed 100%; neither WAPE nor 100−WAPE is accuracy. Mean product WAPE first combines each product's six periods, then averages defined product WAPEs. Positive signed bias means overprediction. Undefined percentage denominators are null.

## Pairwise comparisons

| model | baseline | relative_wape_reduction_pct | wins | losses | ties | undefined |
| --- | --- | --- | --- | --- | --- | --- |
| hw_expanding | hw_182d | -0.52 | 11 | 9 | 0 | 0 |
| hw_expanding | hw_365d | 2.91 | 12 | 8 | 0 | 0 |
| hw_expanding | seasonal_naive | 5.34 | 8 | 12 | 0 | 0 |
| hw_expanding | weekday_mean_4w | -0.93 | 12 | 8 | 0 | 0 |
| hw_expanding | weekday_mean_8w | 0.37 | 12 | 8 | 0 | 0 |
| hw_182d | hw_365d | 3.41 | 13 | 7 | 0 | 0 |
| hw_182d | hw_expanding | 0.52 | 9 | 11 | 0 | 0 |
| hw_182d | seasonal_naive | 5.83 | 10 | 10 | 0 | 0 |
| hw_182d | weekday_mean_4w | -0.40 | 11 | 9 | 0 | 0 |
| hw_182d | weekday_mean_8w | 0.89 | 14 | 6 | 0 | 0 |
| hw_365d | hw_182d | -3.54 | 7 | 13 | 0 | 0 |
| hw_365d | hw_expanding | -3.00 | 8 | 12 | 0 | 0 |
| hw_365d | seasonal_naive | 2.50 | 9 | 11 | 0 | 0 |
| hw_365d | weekday_mean_4w | -3.95 | 8 | 12 | 0 | 0 |
| hw_365d | weekday_mean_8w | -2.62 | 10 | 10 | 0 | 0 |

Each smoothing history is compared with the other two histories and all three baselines. Positive reduction favors the candidate; negative results remain. Wins use summed product absolute errors, with 1e-9 absolute-error-unit tolerance for ties and undefined cases reported separately.

## Period stability

| forecast_start | hw_182d | hw_365d | hw_expanding | seasonal_naive | weekday_mean_4w | weekday_mean_8w |
| --- | --- | --- | --- | --- | --- | --- |
| 2011-01-01 | 164.11 | 179.70 | 159.61 | 100.00 | 122.70 | 179.02 |
| 2011-03-01 | 118.77 | 118.26 | 113.95 | 106.68 | 103.69 | 97.58 |
| 2011-05-01 | 95.02 | 92.85 | 97.99 | 103.96 | 101.53 | 93.07 |
| 2011-07-01 | 101.53 | 109.99 | 112.30 | 90.75 | 103.63 | 114.46 |
| 2011-09-01 | 89.49 | 88.27 | 88.91 | 89.52 | 107.26 | 91.22 |
| 2011-11-01 | 80.91 | 87.19 | 79.79 | 154.41 | 91.74 | 83.96 |

Period outcomes are descriptive. Six historical windows do not establish statistical significance. The 182-day history improves pooled error while losing in four of the six periods and 11 of the 20 combined-product comparisons. The 365-day history has 107.652765% pooled WAPE and 7.810123 units of signed bias, exceeding expanding error.

## High-volume contributions and error direction

The five largest evaluation products account for 48.752800% of observed units and contribute -8,267.403908 units of error reduction for the best smoothing history versus expanding. Negative values mean deterioration. The small net pooled gain reflects offsetting gains and losses, rather than improvement shared by most products.

| product_id | description | actual_units | share_of_actual_units_pct | error_reduction_units |
| --- | --- | --- | --- | --- |
| 22197 | SMALL POPCORN HOLDER | 26,111.00 | 11.87 | -1,304.11 |
| 85099B | JUMBO BAG RED RETROSPOT | 23,145.00 | 10.52 | 112.78 |
| 85123A | WHITE HANGING HEART T-LIGHT HOLDER | 20,568.00 | 9.35 | -2,026.85 |
| 84077 | WORLD WAR 2 GLIDERS ASSTD DESIGNS | 19,761.00 | 8.98 | -4,549.85 |
| 21212 | PACK OF 72 RETROSPOT CAKE CASES | 17,697.00 | 8.04 | -499.37 |

Largest improvements:

| product_id | description | error_reduction_units | signed_bias |
| --- | --- | --- | --- |
| 21982 | PACK OF 12 SUKI TISSUES  | 3,256.11 | 7.24 |
| 21984 | PACK OF 12 PINK PAISLEY TISSUES  | 3,124.07 | 1.43 |
| 21981 | PACK OF 12 WOODLAND TISSUES  | 2,824.61 | -4.16 |
| 21980 | PACK OF 12 RED RETROSPOT TISSUES  | 2,280.53 | 3.26 |
| 84991 | 60 TEATIME FAIRY CAKE CASES | 709.04 | 2.98 |

Largest deteriorations:

| product_id | description | error_reduction_units | signed_bias |
| --- | --- | --- | --- |
| 84077 | WORLD WAR 2 GLIDERS ASSTD DESIGNS | -4,549.85 | 53.88 |
| 85123A | WHITE HANGING HEART T-LIGHT HOLDER | -2,026.85 | -20.87 |
| 15036 | ASSORTED COLOURS SILK FAN | -1,350.22 | -4.22 |
| 22197 | SMALL POPCORN HOLDER | -1,304.11 | -55.86 |
| 84879 | ASSORTED COLOUR BIRD ORNAMENT | -865.54 | -16.96 |

The best smoothing history's overall signed bias is -0.188825 units per product-day, with 114,084.896585 overpredicted units and 114,719.347149 underpredicted units. Near-zero net bias can conceal substantial errors in both directions. See product_contributions.csv for reconciled unit/error shares; actual volume and model-error shares are different denominators.

## Spikes, failures and clipping

Spikes are actual units strictly above the shared expanding-history product/origin 99th percentile, with linear interpolation and zero-sales days included. Labels are identical across all methods and do not remove observations.

| model | spike_product_days | product_days | spike_absolute_error | spike_error_share_pct |
| --- | --- | --- | --- | --- |
| hw_182d | 31 | 3360 | 31,602.73 | 13.81 |
| hw_365d | 31 | 3360 | 30,973.62 | 13.07 |
| hw_expanding | 31 | 3360 | 31,059.02 | 13.50 |
| seasonal_naive | 31 | 3360 | 32,551.00 | 13.40 |
| weekday_mean_4w | 31 | 3360 | 31,189.25 | 13.69 |
| weekday_mean_8w | 31 | 3360 | 31,022.88 | 13.44 |

There are **0 fallback fits** and **0 fits with warnings** in this execution. Fit records and model_events.json retain every fit, its history bounds, optimizer/failure status, warnings and clipping. Clipped forecast observations by smoothing history: expanding 572, 182-day 380, 365-day 408. No successful-fit-only exclusion is needed because all fits succeeded. Exceptions, nonfinite forecasts and optimizer failures are tested with deterministic fixtures and would retain complete last-week fallback forecasts in primary metrics.

The 182-day history has a higher spike-associated absolute error than expanding despite its lower overall error. This is an observed association; promotions, wholesale purchases and inventory causes are not established by these data.

## Limits and future work

The model family was chosen using later-2011 validation; some origins overlap previously inspected evaluations. This is retrospective analysis, with no untouched holdout or independent confirmation. The original corrected benchmark (80.239848583% WAPE; 28.864142803% reduction against last-week repetition) and prior robustness (104.519040833% smoothing versus 103.558688134% strongest baseline) are separately preserved. Different benchmark cohorts prevent direct causal comparisons between experiments.

Observed sales proxy demand; lost sales, inventory and promotions are unavailable. Positive-sales value is GBP transaction-level Quantity×Price, not profit, net revenue or savings. No operational benefits are inferred. A future experiment should freeze its design before newly available outcomes are inspected; this run does not justify further tuning on these same windows.

## Artifact map

All new results live in outputs/training_windows_v1/: predictions.csv; fit_records.csv; model_events.json; overall_metrics.csv; product_metrics.csv; period_metrics.csv; period_product_metrics.csv; pairwise_comparisons.csv; product_comparisons.csv; period_comparisons.csv; period_product_comparisons.csv; product_contributions.csv; spike_thresholds.csv; spike_summary.csv; spike_examples.csv; reference_reconciliation.json; experiment_manifest.json.

The dashboard loads these saved results without fitting models. Forecast Evaluation exposes the experiment, product, origin, smoothing histories and named baselines. Model Performance shows pooled/period outcomes and expandable diagnostics. [Reproduction instructions](setup-and-reproduction.md) distinguish fast CI from full raw-data execution.
