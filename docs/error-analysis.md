# Corrected benchmark error analysis

Scope: the preserved 20-product benchmark, 2011-11-11 through 2011-12-08; 560 product-days per method. Inputs are immutable saved predictions, not newly tuned fits.

The selected weekly smoothing model has 80.24% pooled WAPE versus 112.80% for last-week seasonal naive, a 28.86% relative reduction. Only 10/20 products improved. This is the corrected existing benchmark; its initial test had already been observed before the cross-sheet repair. The first pre-correction result was 80.43% WAPE and 28.70% reduction. Both executions remain archived.

## Five largest improvements

Rank by reduction in summed absolute error units, not by percentage alone.

| product_id | description | baseline_wape | wape | error_reduction_units | share_of_net_error_reduction_pct |
| --- | --- | --- | --- | --- | --- |
| 22197 | POPCORN HOLDER | 110.23 | 66.33 | 6,102.03 | 39.03 |
| 84879 | ASSORTED COLOUR BIRD ORNAMENT | 176.46 | 72.01 | 4,294.74 | 27.47 |
| 85099B | JUMBO BAG RED RETROSPOT | 192.66 | 83.77 | 4,286.79 | 27.42 |
| 84077 | WORLD WAR 2 GLIDERS ASSTD DESIGNS | 84.11 | 51.47 | 1,368.30 | 8.75 |
| 20725 | LUNCH BAG RED RETROSPOT | 102.26 | 44.85 | 912.88 | 5.84 |

## Five largest deteriorations

| product_id | description | baseline_wape | wape | error_reduction_units | share_of_net_error_reduction_pct |
| --- | --- | --- | --- | --- | --- |
| 17003 | BROCADE RING PURSE  | 93.02 | 142.50 | -623.46 | -3.99 |
| 21982 | PACK OF 12 SUKI TISSUES  | 72.90 | 213.56 | -602.03 | -3.85 |
| 84568 | GIRLS ALPHABET IRON ON PATCHES  | 98.10 | 146.55 | -561.55 | -3.59 |
| 21213 | PACK OF 72 SKULL CAKE CASES | 100.66 | 147.06 | -279.31 | -1.79 |
| 15036 | ASSORTED COLOURS SILK FAN | 100.37 | 133.47 | -177.05 | -1.13 |

## Contributions and direction

Each product's model-error contribution is its absolute error divided by total model absolute error. Its reduction contribution is `(baseline error − model error) / overall net reduction`. Negative shares are retained; positive shares can exceed 100% when other products deteriorate. Contributions reconcile to saved sums and appear in `outputs/benchmark_analysis/product_error_analysis.csv`.

| model | absolute_error_sum | signed_bias | percentage_bias | overprediction_units | underprediction_units |
| --- | --- | --- | --- | --- | --- |
| hw_weekly | 38,533.58 | -1.16 | -1.36 | 18,941.09 | 19,592.49 |
| seasonal_naive | 54,169.00 | 10.46 | 12.20 | 30,013.00 | 24,156.00 |

Signed bias is mean(prediction − actual), positive for overprediction. Overprediction and underprediction totals separately sum the positive and negative magnitudes; their sum reconciles to absolute error. Their difference reconciles to signed error.

[Interactive contribution chart](figures/benchmark-contributions.html): bars to the right reduce error; negative bars identify deterioration.

## Spikes and their influence

Define a spike as observed daily units **strictly above the product's training-history 99th percentile**, computed through 2011-11-10 with linear interpolation and zero-sales days included. The thresholds are saved before labelling test days. No spike is removed from primary results.

| model | spike_product_days | product_days | spike_absolute_error | total_absolute_error | spike_error_share_pct |
| --- | --- | --- | --- | --- | --- |
| hw_weekly | 3 | 560 | 4,834.28 | 38,533.58 | 12.55 |
| seasonal_naive | 3 | 560 | 3,566.00 | 54,169.00 | 6.58 |

The largest observed daily test sale was 3,111 units for 22197 (POPCORN HOLDER) on 2011-12-08. [Interactive example](figures/benchmark-spike-example.html) compares its actual and both forecast series. The spike/error associations are observed patterns. Wholesale orders, promotions or stock availability are possible explanations that these aggregate data do not establish.

Saved calculations: `daily_errors.csv`, `spike_thresholds.csv`, `spike_summary.csv`, `largest_improvements.csv`, `largest_deteriorations.csv` and `reconciliation.json` in `outputs/benchmark_analysis/`.

## Training-window diagnostics

The best observed smoothing history was `hw_182d` at **103.976880% pooled WAPE**, versus **104.519041%** with expanding history. This is a **0.518720% relative reduction** (0.542161 percentage points), winning in **2/6 periods** and **9/20 products** across combined periods. The strongest baseline remains `weekday_mean_4w` at **103.558688%**, below every smoothing variant. A shorter history produced a small pooled improvement, with mixed period/product results; it does not establish a generally superior model.

[Full window analysis](training-window-experiment.md) includes shared spike labels, high-volume contributions, signed bias and fit status. Historical benchmark diagnostics above retain their original threshold and scope.
