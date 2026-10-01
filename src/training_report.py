"""Measured documentation for the frozen training-window experiment."""
import json
import pandas as pd
from .common import ROOT, OUT
from .report import markdown_table


def generate():
    folder = OUT/"training_windows_v1"
    read = lambda n: pd.read_csv(folder/f"{n}.csv", dtype={"product_id": str})
    overall = read("overall_metrics")
    by = overall.set_index("model")
    winner = overall[overall.model.str.startswith("hw_")].sort_values("wape").iloc[0]
    best_baseline = overall[~overall.model.str.startswith("hw_")].sort_values("wape").iloc[0]
    pairs, period_pairs, products, fits = [read(n) for n in ["pairwise_comparisons", "period_comparisons", "product_contributions", "fit_records"]]
    main = pairs[(pairs.model==winner.model)&(pairs.baseline=="hw_expanding")].iloc[0] if winner.model!="hw_expanding" else None
    matched = period_pairs[(period_pairs.model==winner.model)&(period_pairs.baseline=="hw_expanding")]
    contribution = products[(products.model==winner.model)&(products.baseline=="hw_expanding")]
    volume = contribution.sort_values("actual_units",ascending=False).head(5)
    events = json.loads((folder/"model_events.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder/"experiment_manifest.json").read_text(encoding="utf-8"))
    warning_fits = sum(bool(f["warnings"]) for f in events)
    fallbacks = int(fits.status.ne("ok").sum())
    period = read("period_metrics").pivot(index="forecast_start",columns="model",values="wape").reset_index()
    conclusion = f"The best observed smoothing history was `{winner.model}` at **{winner.wape:.6f}% pooled WAPE**, versus **{by.loc['hw_expanding','wape']:.6f}%** with expanding history."
    if main is not None:
        conclusion += f" This is a **{main.relative_wape_reduction_pct:.6f}% relative reduction** ({by.loc['hw_expanding','wape']-winner.wape:.6f} percentage points), winning in **{int(matched.relative_wape_reduction_pct.gt(0).sum())}/6 periods** and **{int(main.wins)}/20 products** across combined periods."
    conclusion += f" The strongest baseline remains `{best_baseline.model}` at **{best_baseline.wape:.6f}%**, below every smoothing variant. A shorter history produced a small pooled improvement, with mixed period/product results; it does not establish a generally superior model."
    text = f'''# Training-window experiment

{conclusion}

## Fixed design and provenance

Retrospective question: does limiting training history improve the unchanged additive weekly exponential-smoothing specification? Same fixed 20-product cohort selected exclusively before 2011-01-01; six origins January 1, March 1, May 1, July 1, September 1 and November 1, 2011; 28 consecutive calendar days per origin. Each method has **3,360 predictions**, giving **20,160 rows** across six methods. Actual units total **{by.actual_units.iloc[0]:,.0f} per method**. Calendar zeros and every valid large spike remain.

Expanding history begins 2009-12-01. For start F, the trailing histories are F−182 through F−1 and F−365 through F−1 inclusive. 182 days is exactly 26 weeks. Parameters are independently refitted at each origin, with no horizon updates; additive seasonality, seven-day period, no trend, estimated initialization, optimized fit and use_brute=False remain frozen. The three baselines use only the preceding 7, 28 and 56 calendar days respectively and are calculated once per product/origin.

Authoritative protocol: `protocols/training_windows_v1.json`; SHA-256 `{manifest['protocol_sha256']}`. Protocol commit: `{manifest['protocol_commit']}`, preceding real-data execution. Execution revision and source/input checksums are in `experiment_manifest.json`; an initial development run may record dirty implementation inputs explicitly. Final clean verification identifies its exact tested revision separately from the final evidence-only branch head.

Expanding predictions and all baselines reconcile against the saved robustness implementation, including fit statuses, within rtol=1e-10 and atol=1e-8: `reference_reconciliation.json`. No products, periods or failures were dropped.

## Pooled outcomes

{markdown_table(overall, ['model','mae','wape','mean_product_wape','signed_bias','percentage_bias','overprediction_units','underprediction_units'])}

WAPE is `100 × summed absolute error / summed actual units`, pooled across all six periods. It is normalized absolute error and can exceed 100%; neither WAPE nor 100−WAPE is accuracy. Mean product WAPE first combines each product's six periods, then averages defined product WAPEs. Positive signed bias means overprediction. Undefined percentage denominators are null.

## Pairwise comparisons

{markdown_table(pairs, ['model','baseline','relative_wape_reduction_pct','wins','losses','ties','undefined'])}

Each smoothing history is compared with the other two histories and all three baselines. Positive reduction favors the candidate; negative results remain. Wins use summed product absolute errors, with 1e-9 absolute-error-unit tolerance for ties and undefined cases reported separately.

## Period stability

{markdown_table(period, list(period.columns))}

Period outcomes are descriptive. Six historical windows do not establish statistical significance. The 182-day history improves pooled error while losing in four of the six periods and 11 of the 20 combined-product comparisons. The 365-day history has {by.loc['hw_365d','wape']:.6f}% pooled WAPE and {by.loc['hw_365d','signed_bias']:.6f} units of signed bias, exceeding expanding error.

## High-volume contributions and error direction

The five largest evaluation products account for {volume.share_of_actual_units_pct.sum():.6f}% of observed units and contribute {volume.error_reduction_units.sum():+,.6f} units of error reduction for the best smoothing history versus expanding. Negative values mean deterioration. The small net pooled gain reflects offsetting gains and losses, rather than improvement shared by most products.

{markdown_table(volume, ['product_id','description','actual_units','share_of_actual_units_pct','error_reduction_units'])}

Largest improvements:

{markdown_table(contribution.nlargest(5,'error_reduction_units'), ['product_id','description','error_reduction_units','signed_bias'])}

Largest deteriorations:

{markdown_table(contribution.nsmallest(5,'error_reduction_units'), ['product_id','description','error_reduction_units','signed_bias'])}

The best smoothing history's overall signed bias is {winner.signed_bias:+.6f} units per product-day, with {winner.overprediction_units:,.6f} overpredicted units and {winner.underprediction_units:,.6f} underpredicted units. Near-zero net bias can conceal substantial errors in both directions. See product_contributions.csv for reconciled unit/error shares; actual volume and model-error shares are different denominators.

## Spikes, failures and clipping

Spikes are actual units strictly above the shared expanding-history product/origin 99th percentile, with linear interpolation and zero-sales days included. Labels are identical across all methods and do not remove observations.

{markdown_table(read('spike_summary'), ['model','spike_product_days','product_days','spike_absolute_error','spike_error_share_pct'])}

There are **{fallbacks} fallback fits** and **{warning_fits} fits with warnings** in this execution. Fit records and model_events.json retain every fit, its history bounds, optimizer/failure status, warnings and clipping. Clipped forecast observations by smoothing history: expanding {int(fits[fits.model=='hw_expanding'].negative_predictions_clipped.sum())}, 182-day {int(fits[fits.model=='hw_182d'].negative_predictions_clipped.sum())}, 365-day {int(fits[fits.model=='hw_365d'].negative_predictions_clipped.sum())}. No successful-fit-only exclusion is needed because all fits succeeded. Exceptions, nonfinite forecasts and optimizer failures are tested with deterministic fixtures and would retain complete last-week fallback forecasts in primary metrics.

The 182-day history has a higher spike-associated absolute error than expanding despite its lower overall error. This is an observed association; promotions, wholesale purchases and inventory causes are not established by these data.

## Limits and future work

The model family was chosen using later-2011 validation; some origins overlap previously inspected evaluations. This is retrospective analysis, with no untouched holdout or independent confirmation. The original corrected benchmark (80.239848583% WAPE; 28.864142803% reduction against last-week repetition) and prior robustness (104.519040833% smoothing versus 103.558688134% strongest baseline) are separately preserved. Different benchmark cohorts prevent direct causal comparisons between experiments.

Observed sales proxy demand; lost sales, inventory and promotions are unavailable. Positive-sales value is GBP transaction-level Quantity×Price, not profit, net revenue or savings. No operational benefits are inferred. A future experiment should freeze its design before newly available outcomes are inspected; this run does not justify further tuning on these same windows.

## Artifact map

All new results live in outputs/training_windows_v1/: predictions.csv; fit_records.csv; model_events.json; overall_metrics.csv; product_metrics.csv; period_metrics.csv; period_product_metrics.csv; pairwise_comparisons.csv; product_comparisons.csv; period_comparisons.csv; period_product_comparisons.csv; product_contributions.csv; spike_thresholds.csv; spike_summary.csv; spike_examples.csv; reference_reconciliation.json; experiment_manifest.json.

The dashboard loads these saved results without fitting models. Forecast Evaluation exposes the experiment, product, origin, smoothing histories and named baselines. Model Performance shows pooled/period outcomes and expandable diagnostics. [Reproduction instructions](setup-and-reproduction.md) distinguish fast CI from full raw-data execution.
'''
    (ROOT/"docs/training-window-experiment.md").write_text(text,encoding="utf-8",newline="\n")
    readme = ROOT/"README.md"
    s=readme.read_text(encoding="utf-8").replace("## Limitations and one next experiment", "## Limitations and future work")
    section=f"\n## Training-window experiment\n\n{conclusion}\n\nSame 20 products, six periods, 28 days and weekly model; six methods and 20,160 prediction rows. [Full experiment, contributions and limitations](docs/training-window-experiment.md). [Repeatable clean verification and CI](docs/setup-and-reproduction.md).\n\n![Training-window forecast inspection](docs/screenshots/forecast-training-windows.png)\n"
    s=s.replace("## Measured results",section+"\n## Measured results",1)
    s=s.replace("The historical benchmark is loaded and reconciled, not retrained.","The historical benchmark is loaded and reconciled, not retrained. The same command also executes the committed expanding/182/365-day experiment and reconciles its expanding forecasts and baselines.")
    readme.write_text(s,encoding="utf-8",newline="\n")
    path=ROOT/"docs/error-analysis.md"
    path.write_text(path.read_text(encoding="utf-8")+f"\n## Training-window diagnostics\n\n{conclusion}\n\n[Full window analysis](training-window-experiment.md) includes shared spike labels, high-volume contributions, signed bias and fit status. Historical benchmark diagnostics above retain their original threshold and scope.\n",encoding="utf-8",newline="\n")
    path=ROOT/"docs/resume-evidence.md"
    path.write_text(path.read_text(encoding="utf-8")+f'''\n## Training-window claim mapping

| Claim | Artifact and exact field |
| --- | --- |
| Six methods | outputs/training_windows_v1/overall_metrics.csv: six distinct model rows |
| Six origins, 28 days, 20 products | protocols/training_windows_v1.json: forecast_start_dates, horizon_days, selected_product_ids |
| 20,160 predictions, 3,360 per method | predictions.csv row count; experiment_manifest.json: prediction_rows, rows_per_method |
| Best smoothing {winner.model}: {winner.wape:.12f}% WAPE | overall_metrics.csv: model={winner.model}, wape |
| Expanding smoothing: {by.loc['hw_expanding','wape']:.12f}% | overall_metrics.csv: model=hw_expanding, wape |
| Strongest overall baseline: {best_baseline.wape:.12f}% | overall_metrics.csv: model={best_baseline.model}, wape |

The proposed forecasting bullet reports the six-period pooled experiment. It does not claim that smoothing outperformed the strongest baseline. Raw-row count and the three dashboard tabs refer to the real-sales foundation, not an expanded forecasting cohort. Verified environments, tests and exact tested revisions are recorded under outputs/verification/training-windows/.\n''',encoding="utf-8",newline="\n")


if __name__ == "__main__":
    generate()
