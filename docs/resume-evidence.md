# Resume evidence

## Proposed bullets

- Evaluated six 28-day sales forecasting methods across six retrospective periods and 20 products using Python, pandas and statsmodels; the best smoothing history achieved 104.0% pooled WAPE versus 104.5% with expanding history.
- Audited 1,067,371 UCI transaction rows and built DuckDB SQL sales rankings, comparable-period growth and weekday analysis with a three-tab Streamlit/Plotly dashboard and evidence-backed error analysis.

## Claim mapping

| Claim | Saved artifact and field |
| --- | --- |
| 1,067,371 raw rows | `outputs/sales/data_audit.json`, `raw_rows`; sum of sheet counts |
| Six 28-day retrospective periods; 20 products | `protocols/robustness_v1.json`; `outputs/robustness/split_manifest.json`, splits and selected_product_ids |
| Four methods | `outputs/robustness/overall_metrics.csv`, four model rows |
| Weekly smoothing WAPE 104.519040833% | Same file, hw_weekly row, wape |
| Strongest pooled baseline weekday_mean_4w, WAPE 103.558688134% | Same file, lowest baseline wape |
| Relative reduction -0.927351163% | `outputs/robustness/baseline_comparisons.csv`, baseline=weekday_mean_4w |
| Existing corrected 80.239848583% WAPE and 28.864142803% reduction | `archives/benchmark_corrected/test_overall_metrics.csv`, hw_weekly row; reconciled from archived predictions |
| First pre-correction 80.426316570% WAPE and 28.698831423% reduction | `archives/benchmark_pre_correction/test_overall_metrics.csv`, hw_weekly row |

Sales findings and every value used in the Overview are traceable to `outputs/sales/findings.json` and its named SQL outputs. SQL calculations use all cleaned merchandise; forecast claims use the named cohort only. Technologies executed: Python/pandas preparation, statsmodels fits, DuckDB SQL, Streamlit/Plotly dashboard and pytest verification. Installation and test evidence is stored under `outputs/verification/`.

The existing benchmark and robustness are different experiments. The corrected benchmark followed a disclosed ingestion repair after the first test had been seen. Robustness uses an earlier-selected cohort and fixed historical periods, with the family originally chosen on later-2011 validation. Do not combine their percentages, describe either rerun as a fresh holdout, call WAPE accuracy, or claim operational savings. The prior implementation is archived; current resume bullets describe the active sales analytics project.

## Training-window claim mapping

| Claim | Artifact and exact field |
| --- | --- |
| Six methods | outputs/training_windows_v1/overall_metrics.csv: six distinct model rows |
| Six origins, 28 days, 20 products | protocols/training_windows_v1.json: forecast_start_dates, horizon_days, selected_product_ids |
| 20,160 predictions, 3,360 per method | predictions.csv row count; experiment_manifest.json: prediction_rows, rows_per_method |
| Best smoothing hw_182d: 103.976879994410% WAPE | overall_metrics.csv: model=hw_182d, wape |
| Expanding smoothing: 104.519040833085% | overall_metrics.csv: model=hw_expanding, wape |
| Strongest overall baseline: 103.558688134222% | overall_metrics.csv: model=weekday_mean_4w, wape |

The proposed forecasting bullet reports the six-period pooled experiment. It does not claim that smoothing outperformed the strongest baseline. Raw-row count and the three dashboard tabs refer to the real-sales foundation, not an expanded forecasting cohort. Verified environments, tests and exact tested revisions are recorded under outputs/verification/training-windows/.
