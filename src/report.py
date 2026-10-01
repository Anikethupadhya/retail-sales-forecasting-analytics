"""Documentation and interactive error charts derived from saved measured outputs."""
import json

import pandas as pd
import plotly.express as px

from .common import ROOT, OUT
from .evidence import BENCHMARK


def markdown_table(frame, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"]*len(columns)) + " |"]
    for _, row in frame.iterrows():
        cells = []
        for name in columns:
            value = row[name]
            cells.append("undefined" if pd.isna(value) else (f"{value:,.2f}" if isinstance(value, float) else str(value)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def clean_html(path):
    # Match the existing exported assets while making generated IDs/whitespace stable.
    path.write_bytes("\r\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()).encode("utf-8"))


def generate():
    read = lambda name: pd.read_csv(OUT / name, dtype={"product_id": str})
    audit = json.loads((OUT / "sales/data_audit.json").read_text(encoding="utf-8"))
    findings = json.loads((OUT / "sales/findings.json").read_text(encoding="utf-8"))["findings"]
    run = json.loads((OUT / "run_manifest.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / "robustness/split_manifest.json").read_text(encoding="utf-8"))
    overall = read("robustness/overall_metrics.csv")
    compare = read("robustness/baseline_comparisons.csv")
    period = read("robustness/period_metrics.csv")
    period_compare = read("robustness/period_comparisons.csv")
    events = json.loads((OUT / "robustness/model_events.json").read_text(encoding="utf-8"))
    original = pd.read_csv(BENCHMARK / "test_overall_metrics.csv").set_index("model")
    selected = overall.set_index("model").loc["hw_weekly"]
    strongest = overall[overall.model.ne("hw_weekly")].sort_values("wape").iloc[0]
    strongest_compare = compare[compare.baseline.eq(strongest.model)].iloc[0]
    errors = read("benchmark_analysis/product_error_analysis.csv")
    improvements = read("benchmark_analysis/largest_improvements.csv")
    deteriorations = read("benchmark_analysis/largest_deteriorations.csv")
    spikes = read("benchmark_analysis/spike_summary.csv")
    days = read("benchmark_analysis/daily_errors.csv")
    benchmark_metrics = read("benchmark_analysis/overall_metrics.csv")
    figures = ROOT / "docs/figures"
    figures.mkdir(parents=True, exist_ok=True)
    fig = px.bar(errors.sort_values("error_reduction_units"), x="error_reduction_units", y="product_id", orientation="h",
                 hover_data=["description", "relative_wape_reduction_pct"], color="error_reduction_units", color_continuous_scale="RdBu", color_continuous_midpoint=0,
                 title="Corrected benchmark: product contributions to absolute-error reduction")
    fig.update_layout(xaxis_title="Baseline absolute error minus model absolute error (units)", yaxis_title="Product code", yaxis_type="category", height=650)
    fig.write_html(figures / "benchmark-contributions.html", include_plotlyjs=True, div_id="benchmark-contributions")
    clean_html(figures / "benchmark-contributions.html")
    biggest = days[days.model.eq("hw_weekly")].nlargest(1, "actual").iloc[0]
    sample = days[days.product_id.eq(biggest.product_id)]
    actual = sample[sample.model.eq("hw_weekly")][["date", "actual"]].rename(columns={"actual": "units"}).assign(series="Observed sales")
    forecasts = sample[["date", "prediction", "model"]].rename(columns={"prediction": "units", "model": "series"})
    fig = px.line(pd.concat([actual, forecasts]), x="date", y="units", color="series", title=f"Largest observed benchmark daily spike: {biggest.product_id} — {biggest.description}")
    fig.update_layout(yaxis_title="Units", xaxis_title="Historical test date")
    fig.write_html(figures / "benchmark-spike-example.html", include_plotlyjs=True, div_id="benchmark-spike-example")
    clean_html(figures / "benchmark-spike-example.html")
    shared = len(manifest["cohort_comparison"]["shared"])
    n = len(manifest["selected_product_ids"])
    fallback = sum(e["status"] != "ok" for e in events)
    clipped = sum(e.get("negative_predictions_clipped", 0) for e in events)
    windows_won = int(period_compare[period_compare.baseline.eq(strongest.model)].relative_wape_reduction_pct.gt(0).sum())
    if strongest_compare.relative_wape_reduction_pct > 0:
        bullet1 = f"Reduced pooled 28-day sales forecast WAPE by {strongest_compare.relative_wape_reduction_pct:.1f}% versus the strongest tested baseline across six retrospective periods and {n} products using Python, pandas and statsmodels ({strongest.wape:.1f}% to {selected.wape:.1f}%)."
    else:
        bullet1 = f"Benchmarked four 28-day sales forecasting methods across six retrospective periods and {n} products using Python, pandas and statsmodels; reported {selected.wape:.1f}% smoothing-model WAPE versus {strongest.wape:.1f}% for the strongest baseline."
    bullet2 = f"Audited {audit['raw_rows']:,} UCI transaction rows and built DuckDB SQL sales rankings, comparable-period growth and weekday analysis with a three-tab Streamlit/Plotly dashboard and evidence-backed error analysis."
    if (OUT/"training_windows_v1/overall_metrics.csv").exists():
        windows = read("training_windows_v1/overall_metrics.csv")
        winner = windows[windows.model.isin(["hw_expanding","hw_182d","hw_365d"])].sort_values("wape").iloc[0]
        expanding = windows[windows.model.eq("hw_expanding")].iloc[0]
        bullet1 = f"Evaluated six 28-day sales forecasting methods across six retrospective periods and {n} products using Python, pandas and statsmodels; the best smoothing history achieved {winner.wape:.1f}% pooled WAPE versus {expanding.wape:.1f}% with expanding history."
    next_experiment = "The prespecified expanding/182/365-day training-window experiment is complete; see [measured results](docs/training-window-experiment.md). A future evaluation should use a prospectively frozen design on newly available data. No further tuning is justified as independent confirmation using these inspected periods."
    findings_text = "\n".join(f"- {f['text']} ([evidence](../{f['source']}), {f['row']})." for f in findings)
    (ROOT / "docs/error-analysis.md").write_text(f'''# Corrected benchmark error analysis

Scope: the preserved 20-product benchmark, 2011-11-11 through 2011-12-08; 560 product-days per method. Inputs are immutable saved predictions, not newly tuned fits.

The selected weekly smoothing model has {original.loc['hw_weekly','wape']:.2f}% pooled WAPE versus {original.loc['seasonal_naive','wape']:.2f}% for last-week seasonal naive, a {original.loc['hw_weekly','relative_wape_reduction_pct']:.2f}% relative reduction. Only 10/20 products improved. This is the corrected existing benchmark; its initial test had already been observed before the cross-sheet repair. The first pre-correction result was 80.43% WAPE and 28.70% reduction. Both executions remain archived.

## Five largest improvements

Rank by reduction in summed absolute error units, not by percentage alone.

{markdown_table(improvements, ['product_id','description','baseline_wape','wape','error_reduction_units','share_of_net_error_reduction_pct'])}

## Five largest deteriorations

{markdown_table(deteriorations, ['product_id','description','baseline_wape','wape','error_reduction_units','share_of_net_error_reduction_pct'])}

## Contributions and direction

Each product's model-error contribution is its absolute error divided by total model absolute error. Its reduction contribution is `(baseline error − model error) / overall net reduction`. Negative shares are retained; positive shares can exceed 100% when other products deteriorate. Contributions reconcile to saved sums and appear in `outputs/benchmark_analysis/product_error_analysis.csv`.

{markdown_table(benchmark_metrics, ['model','absolute_error_sum','signed_bias','percentage_bias','overprediction_units','underprediction_units'])}

Signed bias is mean(prediction − actual), positive for overprediction. Overprediction and underprediction totals separately sum the positive and negative magnitudes; their sum reconciles to absolute error. Their difference reconciles to signed error.

[Interactive contribution chart](figures/benchmark-contributions.html): bars to the right reduce error; negative bars identify deterioration.

## Spikes and their influence

Define a spike as observed daily units **strictly above the product's training-history 99th percentile**, computed through 2011-11-10 with linear interpolation and zero-sales days included. The thresholds are saved before labelling test days. No spike is removed from primary results.

{markdown_table(spikes, ['model','spike_product_days','product_days','spike_absolute_error','total_absolute_error','spike_error_share_pct'])}

The largest observed daily test sale was {biggest.actual:,.0f} units for {biggest.product_id} ({biggest.description}) on {biggest.date}. [Interactive example](figures/benchmark-spike-example.html) compares its actual and both forecast series. The spike/error associations are observed patterns. Wholesale orders, promotions or stock availability are possible explanations that these aggregate data do not establish.

Saved calculations: `daily_errors.csv`, `spike_thresholds.csv`, `spike_summary.csv`, `largest_improvements.csv`, `largest_deteriorations.csv` and `reconciliation.json` in `outputs/benchmark_analysis/`.
''', encoding="utf-8")
    (ROOT / "README.md").write_text(f'''# Retail Sales Forecasting & Analytics

A reproducible portfolio project using real historical transactions, customer-free merchandise aggregates, meaningful DuckDB SQL, fixed-origin forecasting comparisons, and a three-tab Streamlit/Plotly dashboard. Forecasts describe **observed positive sales**. Actual inventory and lost demand are unavailable.

## Measured results

All-merchandise coverage: **2009-12-01 to 2011-12-08**, {audit['raw_rows']:,} raw rows across both workbook sheets; **{audit['retained_rows']:,} retained merchandise lines**, **{audit['product_count']:,} products**, **{audit['positive_units']:,.0f} positive units**, and **£{audit['positive_sales_gbp']:,.2f} positive-sales value**. Value is transaction-level Quantity × Price summed before aggregation; it is not net revenue or profit. All countries are pooled.

{findings_text.replace('../outputs/', 'outputs/')}

Retrospective robustness: **{n} products**, six 28-day windows. Weekly smoothing achieved **{selected.wape:.2f}% pooled WAPE**, versus **{strongest.wape:.2f}%** for the strongest pooled baseline, `{strongest.model}`. Relative reduction against that baseline: **{strongest_compare.relative_wape_reduction_pct:+.2f}%**. Smoothing beat that baseline in **{windows_won}/6 windows**. The cohort shares {shared} products with the existing benchmark; cohort differences prevent attributing cross-experiment differences solely to models.

{markdown_table(overall, ['model','mae','wape','mean_product_wape','signed_bias','percentage_bias'])}

{markdown_table(compare, ['baseline','relative_wape_reduction_pct','wins','losses','ties','undefined','win_pct'])}

The **existing corrected benchmark** is separately preserved: 20 products, 28 days, **112.80% baseline WAPE**, **80.24% smoothing WAPE**, **28.86% relative reduction**, and 10/20 product wins. The first pre-correction execution reported **80.43%** and **28.70%** respectively. The correction removed 22,523 cross-sheet replicas after the first test was observed, without changing the selected family or cohort. This repaired rerun is not a newly untouched holdout. Historical artifacts and titles are immutable and exempt from the current project renaming.

## Setup and full reproduction

Tested Python {run['python']}; installed versions, raw-file and protocol checksums are recorded in `outputs/run_manifest.json`. All Python requirements are pinned.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r requirements.txt
.\\.venv\\Scripts\\python -m src.pipeline
.\\.venv\\Scripts\\python -m pytest -q --junitxml=outputs/verification/tests.xml
.\\.venv\\Scripts\\python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```

**Full analysis command: `python -m src.pipeline`** using the installed environment. It audits the workbook, builds sales SQL outputs, reconciles and explains saved benchmark predictions, evaluates the frozen robustness protocol, and regenerates documentation from measured outputs. The historical benchmark is loaded and reconciled, not retrained. The dashboard loads saved aggregates and predictions and does not fit models. Open http://localhost:8501. Rebuild the ignored DuckDB binary by running the pipeline.

Original data: [Chen, D. (2012), Online Retail II, UCI](https://archive.ics.uci.edu/dataset/502/online+retail+ii), [DOI:10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D), CC BY 4.0. Raw workbook: `data/raw/online_retail_II.xlsx`; SHA-256 `{audit['sha256']}`. [Manual download instructions](docs/data-download.md) are available if official acquisition fails. Raw data, local workbook caches and database binaries stay outside Git and the review ZIP.

## Data rules and scope

Preserve the existing cleaning rules: exclude invalid dates, missing invoice/product IDs, exact cross-sheet replicas, cancellations, nonpositive/invalid quantities, non-merchandise codes, nonpositive prices and the potentially truncated final trading day. Both sheet schemas are inspected explicitly. Source sheet overlap is matched on full original fields and within-sheet occurrence number, preserving repeated lines inside each sheet. Missing customer IDs alone do not exclude valid sales. Audit counts reconcile in `outputs/sales/data_audit.json`; the retained count agrees with the corrected historical audit. Returns are not netted against positive units or value. No outliers are trimmed.

December 2011 is partial, with only December 1–8 retained. SQL computes monthly growth only for adjacent complete calendar months; annual comparison uses January–November 2010 versus the same months in 2011. Complete coverage means within extract bounds, not proof the merchant had no missing transactions. Weekday averages use covered calendar-day denominators and include zero-sale days. Product rankings cover **all cleaned merchandise**; forecast results cover their named **fixed cohort**; individual product metrics are displayed separately.

## Fixed robustness protocol

`protocols/robustness_v1.json` and its SHA-256 were saved before computing new forecasts. Starts are January 1, March 1, May 1, July 1, September 1 and November 1, 2011. Training ends the previous day; horizon day 1 equals forecast_start. Training windows expand from December 1, 2009.

{markdown_table(pd.DataFrame(manifest['splits']), ['forecast_start','train_end','forecast_end','training_days'])}

Eligibility uses only dates before January 1, 2011: at least 365 initial calendar days, first sale within 90 days of grid start, active on at least 25% of initial days and 30% of the last 90 days. Rank descending initial positive units with ascending product-ID ties; select up to 20 without relaxing thresholds. Initial metadata descriptions also use that period. Save all eligibility decisions, IDs, and differences from the existing August-selected cohort.

Methods: last-week seasonal naive; averages of matching weekdays from the preceding 28 or 56 calendar days, fixed and repeated throughout the horizon; and the existing additive weekly Holt-Winters specification without trend. Refit the same specification at each origin with estimated initialization, optimized coefficients and `use_brute=False`. No later fitted parameters or within-horizon observations are reused. Negative predictions are clipped at zero. Model exceptions, nonfinite predictions and optimizer failures use a recorded last-week fallback. This run recorded {fallback} fallback fits and {clipped} clipped horizon predictions. Full warnings and failures are in `outputs/robustness/model_events.json`.

**Retrospective limitation:** the model family was chosen on later-2011 validation before this experiment. Earlier windows stress-test that specification and are not a strategy chosen prospectively in January. September and November overlap existing evaluation dates. These comparisons are not independent confirmation or a fresh untouched holdout.

## Metrics and error analysis

MAE is mean absolute error in units per product-day. Pooled WAPE is `100 × sum(abs(prediction − actual)) / sum(actual)`; overall robustness uses all six windows together, not a mean of window percentages. Mean product WAPE averages defined per-product WAPEs. Signed bias is `mean(prediction − actual)`, positive for overprediction; percentage bias is `100 × sum(prediction − actual) / sum(actual)`. Zero actual denominators produce null percentage metrics; zero baseline WAPE produces null relative reduction. WAPE can exceed 100%; **WAPE and 100 − WAPE are not accuracy**.

Product comparisons report wins, losses, ties within 1e-9 absolute-error units and undefined cases against **each baseline**. Positive-sales denominators must be defined for percentage-based comparisons. Relative reduction preserves negative outcomes. Summed product errors and contributions reconcile to pooled results. [Error-analysis report and interactive charts](docs/error-analysis.md) show five largest improvements/deteriorations, direction of error, and training-defined spikes without dropping observations or asserting unverified causes.

## Dashboard and SQL

Exactly three tabs: **Sales Overview**, **Forecast Evaluation**, **Model Performance**. Overview shows all-merchandise units/value, trends, rankings, weekday averages and three measured findings. Evaluation selects experiment, historical period and product, displaying actual versus baseline/model forecasts, origin dates, and product/cohort metrics. Performance shows original validation evidence, robustness methods and periods, pairwise wins/losses, error contributions and spike examples. Technical audit details are in expanders. Historical archives preserve the prior implementation; the active project contains no supplier or inventory scenarios.

![Sales Overview](docs/screenshots/sales-overview.png)
![Forecast Evaluation](docs/screenshots/forecast-evaluation.png)
![Model Performance](docs/screenshots/model-performance.png)

Standalone SQL: `product_rankings.sql`, `monthly_trends.sql`, `weekday_seasonality.sql`, `comparable_growth.sql`. Tables: `sales` (customer-free product-date aggregates), `product_metadata`, `calendar`, `daily_totals`. Queries demonstrate aggregation, joins, rankings and lag windows. Outputs are saved in `outputs/sales/`.

## Verification and deliverables

Tests cover chronology, future-information perturbations, weekday-baseline arithmetic, cohort independence, metrics and zero denominators, pairwise comparisons, SQL growth/weekday arithmetic, transaction-value aggregation, archive integrity and output reconciliation. Streamlit tests and rendered browser inspection exercise tabs, experiment/product/period controls, scope labels and charts. Evidence is in `outputs/verification/`, including test reports, browser screenshots and clean-environment reproduction status. A fresh environment with empty workbook caches must reproduce measured outputs to absolute tolerance 1e-8 and relative tolerance 1e-10 for forecasts/metrics (GBP sales aggregates: absolute 1e-6, relative 1e-10).

Folders: `src/` analysis modules; `sql/` standalone queries; `protocols/` frozen experiment; `archives/` immutable historical evidence; `outputs/sales/`, `outputs/robustness/`, `outputs/benchmark_analysis/` separate results; `docs/` explanations, evidence and screenshots. `scripts/package_review.py` creates an allowlisted review ZIP and manifest, excluding raw/customer-level extracts, environments, caches and database binaries. [Version control and portfolio evidence](docs/version-control.md) explains the private repository, backup scope, and workflow for recording future improvements.

## Limitations and one next experiment

Sales proxy demand; actual inventory, lost sales and promotions are unavailable. Calendar zeros cannot distinguish closures, absent records or stock-outs. Merchandise-code and price rules can exclude unconventional valid records. Bulk-order spikes remain. Six non-overlapping robustness windows in one year do not demonstrate universal or future performance. No prediction intervals are supplied. Cohorts are high-volume subsets, not the full catalogue.

{next_experiment}

## Proposed resume entry

- {bullet1}
- {bullet2}

[Numerical claim evidence](docs/resume-evidence.md) separates existing corrected benchmark claims from retrospective robustness outcomes. [Interview guide](docs/interview-guide.md) explains the methods and limitations.
''', encoding="utf-8")
    (ROOT / "docs/resume-evidence.md").write_text(f'''# Resume evidence

## Proposed bullets

- {bullet1}
- {bullet2}

## Claim mapping

| Claim | Saved artifact and field |
| --- | --- |
| {audit['raw_rows']:,} raw rows | `outputs/sales/data_audit.json`, `raw_rows`; sum of sheet counts |
| Six 28-day retrospective periods; {n} products | `protocols/robustness_v1.json`; `outputs/robustness/split_manifest.json`, splits and selected_product_ids |
| Four methods | `outputs/robustness/overall_metrics.csv`, four model rows |
| Weekly smoothing WAPE {selected.wape:.9f}% | Same file, hw_weekly row, wape |
| Strongest pooled baseline {strongest.model}, WAPE {strongest.wape:.9f}% | Same file, lowest baseline wape |
| Relative reduction {strongest_compare.relative_wape_reduction_pct:+.9f}% | `outputs/robustness/baseline_comparisons.csv`, baseline={strongest.model} |
| Existing corrected 80.239848583% WAPE and 28.864142803% reduction | `archives/benchmark_corrected/test_overall_metrics.csv`, hw_weekly row; reconciled from archived predictions |
| First pre-correction 80.426316570% WAPE and 28.698831423% reduction | `archives/benchmark_pre_correction/test_overall_metrics.csv`, hw_weekly row |

Sales findings and every value used in the Overview are traceable to `outputs/sales/findings.json` and its named SQL outputs. SQL calculations use all cleaned merchandise; forecast claims use the named cohort only. Technologies executed: Python/pandas preparation, statsmodels fits, DuckDB SQL, Streamlit/Plotly dashboard and pytest verification. Installation and test evidence is stored under `outputs/verification/`.

The existing benchmark and robustness are different experiments. The corrected benchmark followed a disclosed ingestion repair after the first test had been seen. Robustness uses an earlier-selected cohort and fixed historical periods, with the family originally chosen on later-2011 validation. Do not combine their percentages, describe either rerun as a fresh holdout, call WAPE accuracy, or claim operational savings. The prior implementation is archived; current resume bullets describe the active sales analytics project.
''', encoding="utf-8")

    if (OUT / "training_windows_v1/experiment_manifest.json").exists():
        from .training_report import generate as generate_training_report
        generate_training_report()


if __name__ == "__main__":
    generate()
