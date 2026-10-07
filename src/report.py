"""Documentation and interactive error charts derived from saved measured outputs."""
import json

import pandas as pd
import plotly.express as px

from .common import ROOT, OUT
from .evidence import BENCHMARK
from .documents import update_section


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


def generate(*, root=ROOT, outputs=OUT):
    OUT = outputs
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
    figures = root / "docs/figures"
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
    update_section(root / "docs/error-analysis.md", "benchmark-error-analysis", f'''## Corrected benchmark error analysis

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
''', title="Forecast error analysis")
    from .portfolio import generate as generate_portfolio
    generate_portfolio(root=root, outputs=outputs)

    if (OUT / "training_windows_v1/experiment_manifest.json").exists():
        from .training_report import generate as generate_training_report
        generate_training_report(root=root, outputs=outputs)


if __name__ == "__main__":
    generate()
