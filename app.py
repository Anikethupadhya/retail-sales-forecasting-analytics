"""Saved-output dashboard; no model training or simulated operational inputs."""
import json

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.common import ROOT, OUT
from src.evidence import BENCHMARK

COLORS = {"actual": "#485e78", "hw_weekly": "#087f8c", "seasonal_naive": "#df8f2d", "weekday_mean_4w": "#7755a3", "weekday_mean_8w": "#be5368"}
COLORS.update({"hw_expanding":"#087f8c","hw_182d":"#2c6bb0","hw_365d":"#ab5279"})
LABELS = {"hw_weekly": "Weekly smoothing", "seasonal_naive": "Last-week baseline", "weekday_mean_4w": "4-week weekday average", "weekday_mean_8w": "8-week weekday average"}
LABELS.update({"hw_expanding":"Smoothing · expanding history","hw_182d":"Smoothing · 182 days","hw_365d":"Smoothing · 365 days"})
st.set_page_config(page_title="Retail Sales Forecasting & Analytics", layout="wide")
st.title("Retail Sales Forecasting & Analytics")
st.caption("UCI Online Retail II · December 1, 2009–December 8, 2011 · Historical observed positive sales · GBP")
st.markdown("**Start here:** Sales Overview answers what sold and when across all merchandise. Forecast Evaluation lets you inspect one product and historical period. Model Performance compares the fixed cohort across all six periods. All charts use saved results.")
if not (OUT / "run_manifest.json").exists():
    st.info("Run python -m src.pipeline to create the saved results.")
    st.stop()


@st.cache_data
def load_data(version):
    def read(path):
        return pd.read_csv(path, dtype={"product_id": str})
    d = {}
    for folder, names in {
        "sales": ["daily_totals", "product_rankings", "monthly_trends", "weekday_seasonality", "comparable_growth"],
        "robustness": ["predictions", "product_metadata", "daily_sales", "overall_metrics", "product_metrics", "period_metrics", "period_product_metrics", "baseline_comparisons", "period_comparisons", "product_comparisons"],
        "training_windows_v1": ["predictions", "overall_metrics", "product_metrics", "period_metrics", "period_product_metrics", "pairwise_comparisons", "product_comparisons", "period_comparisons", "product_contributions", "spike_summary", "spike_examples", "fit_records"],
        "benchmark_analysis": ["product_error_analysis", "largest_improvements", "largest_deteriorations", "daily_errors", "spike_summary", "overall_metrics"],
    }.items():
        for name in names:
            frame = read(OUT / folder / f"{name}.csv")
            for col in ["date", "month_start"]:
                if col in frame:
                    frame[col] = pd.to_datetime(frame[col])
            d[f"{folder}/{name}"] = frame
    for name in ["test_predictions", "test_overall_metrics", "test_product_metrics", "validation_overall_metrics", "daily_sales", "product_metadata"]:
        frame = read(BENCHMARK / f"{name}.csv")
        if "date" in frame:
            frame["date"] = pd.to_datetime(frame.date)
        d[f"benchmark/{name}"] = frame
    for name in ["sales/data_audit", "sales/findings", "robustness/split_manifest", "robustness/model_events", "portfolio/summary", "portfolio/walkthrough_examples"]:
        d[name] = json.loads((OUT / f"{name}.json").read_text(encoding="utf-8"))
    return d


try:
    d = load_data(tuple((OUT / name).stat().st_mtime_ns for name in ["run_manifest.json", "sales/findings.json", "portfolio/summary.json", "portfolio/walkthrough_examples.json"]))
except FileNotFoundError:
    st.info("Saved results are incomplete. Run python -m src.pipeline to rebuild all outputs.")
    st.stop()
overview, evaluation, performance = st.tabs(["Sales Overview", "Forecast Evaluation", "Model Performance"])
with overview:
    st.subheader("All cleaned merchandise · all countries")
    st.caption("Analysed dates: December 1, 2009–December 8, 2011. December 2011 is partial. Totals are positive sales; returns are excluded rather than netted.")
    audit = d["sales/data_audit"]
    columns = st.columns(3)
    columns[0].metric("Positive units sold", f"{audit['positive_units']:,.0f}")
    columns[1].metric("Positive-sales value (GBP)", f"£{audit['positive_sales_gbp']:,.0f}")
    columns[2].metric("Merchandise products", f"{audit['product_count']:,}")
    st.subheader("Three measured findings")
    for finding in d["sales/findings"]["findings"]:
        st.write(finding["text"])
    monthly = d["sales/monthly_trends"].copy()
    monthly["coverage"] = monthly.complete_month.map({True: "Complete month", False: "Partial month"})
    fig = px.bar(monthly, x="month_start", y="positive_sales_gbp", color="coverage", color_discrete_map={"Complete month": "#087f8c", "Partial month": "#df8f2d"}, hover_data=["covered_calendar_days"])
    fig.update_layout(height=300, xaxis_title="Month", yaxis_title="Positive-sales value (GBP)", legend={"orientation": "h", "y": 1.15}, margin={"t": 30, "b": 30})
    st.plotly_chart(fig, width="stretch")
    st.caption("Monthly totals cover all merchandise; the amber December 2011 bar contains eight days and is excluded from growth comparisons.")
    left, right = st.columns(2)
    with left:
        ranking = st.selectbox("Rank products by", ["Positive-sales value (GBP)", "Positive units sold"], key="ranking")
        metric = "positive_sales_gbp" if ranking.startswith("Positive-sales") else "positive_units"
        rank = d["sales/product_rankings"].nlargest(8, metric).sort_values(metric)
        fig = px.bar(rank, x=metric, y="description", orientation="h", hover_data=["product_id"], color_discrete_sequence=["#087f8c"])
        fig.update_layout(height=340, xaxis_title=ranking, yaxis_title="Product", margin={"t": 10})
        st.plotly_chart(fig, width="stretch")
        st.caption("The eight largest products are ranked over the entire analysed extract; codes appear on hover.")
    with right:
        weekdays = d["sales/weekday_seasonality"]
        fig = px.bar(weekdays, x="weekday", y="average_daily_sales_gbp", hover_data=["covered_calendar_days"], color_discrete_sequence=["#485e78"])
        fig.update_layout(height=340, xaxis_title="Weekday", yaxis_title="Average daily positive-sales value (GBP)", margin={"t": 10})
        st.plotly_chart(fig, width="stretch")
        st.caption("Weekday averages include every covered calendar date, including dates with zero observed sales.")
    with st.expander("Comparable growth, SQL outputs and data audit"):
        st.write("Annual comparison uses January–November in both years; monthly changes require complete adjacent months.")
        st.dataframe(d["sales/comparable_growth"], hide_index=True)
        st.dataframe(monthly[["month_start", "complete_month", "positive_sales_gbp", "comparable_monthly_growth_pct"]], hide_index=True)
        st.json(audit)

with evaluation:
    st.subheader("Historical fixed-origin backtests")
    walkthrough = {e["id"].title(): e for e in d["portfolio/walkthrough_examples"]["examples"]}
    def apply_walkthrough():
        example = walkthrough.get(st.session_state.walkthrough_example)
        if example:
            st.session_state.experiment = "Training-window experiment"
            st.session_state.period = next(s for s in d["robustness/split_manifest"]["splits"] if s["forecast_start"] == example["forecast_start"])
            st.session_state.product_robustness = example["product_id"]
            st.session_state.window_methods = []
            st.session_state.window_baselines = example["selectors"]["Baseline comparisons"]
    st.selectbox("Walkthrough example", ["Explore freely", *walkthrough], key="walkthrough_example", on_change=apply_walkthrough)
    example = walkthrough.get(st.session_state.walkthrough_example)
    if example:
        matches = (st.session_state.get("experiment") == "Training-window experiment"
                   and st.session_state.get("period", {}).get("forecast_start") == example["forecast_start"]
                   and st.session_state.get("product_robustness") == example["product_id"]
                   and st.session_state.get("window_methods") == []
                   and st.session_state.get("window_baselines") == example["selectors"]["Baseline comparisons"])
        if matches:
            st.caption(f"Illustrative example selected after inspecting results: {example['product_id']} — {example['description']}. {example['interpretation']} Manual selectors remain available.")
        else:
            st.caption("Manual selections differ from the walkthrough preset. The chart and scores reflect the current selectors; reselect an example to apply its saved settings.")
    experiment = st.selectbox("Evaluation experiment", ["Existing corrected benchmark", "Retrospective robustness", "Training-window experiment"], key="experiment")
    original = experiment.startswith("Existing")
    windows = experiment == "Training-window experiment"
    if original:
        predictions = d["benchmark/test_predictions"]
        history = d["benchmark/daily_sales"]
        metadata = d["benchmark/product_metadata"].set_index("product_id")
        product_metrics = d["benchmark/test_product_metrics"]
        cohort_metrics = d["benchmark/test_overall_metrics"]
        date = "2011-11-11"
        st.caption("20 products selected before August 19, 2011. The cross-sheet repair followed the first test observation; original model family and cohort were preserved.")
    else:
        date = st.selectbox("Forecast start", d["robustness/split_manifest"]["splits"], format_func=lambda s: s["forecast_start"], key="period")["forecast_start"]
        folder = "training_windows_v1" if windows else "robustness"
        predictions = d[f"{folder}/predictions"].query("forecast_start == @date")
        history = d["robustness/daily_sales"]
        metadata = d["robustness/product_metadata"].set_index("product_id")
        product_metrics = d[f"{folder}/period_product_metrics"].query("forecast_start == @date")
        cohort_metrics = d[f"{folder}/period_metrics"].query("forecast_start == @date")
        st.caption("Fixed cohort selected before January 1, 2011. Family chosen on later-2011 validation; some periods overlap the existing benchmark. Retrospective comparison, not independent confirmation.")
    pid = st.selectbox("Product", metadata.index.tolist(), format_func=lambda p: f"{p} — {metadata.loc[p, 'description']}", key="product_" + ("benchmark" if original else "robustness"))
    part = predictions.query("product_id == @pid")
    origin = pd.Timestamp(part.origin.iloc[0])
    start, end = part.date.min(), part.date.max()
    st.write(f"Training cutoff: {origin:%Y-%m-%d} · Forecast start: {start:%Y-%m-%d} · Evaluation end: {end:%Y-%m-%d} · 28 calendar days")
    hist = history.query("product_id == @pid")
    fig = go.Figure()
    before = hist[hist.date.between(origin-pd.Timedelta(days=90), origin)]
    fig.add_trace(go.Scatter(x=before.date, y=before.units, name="Observed history", line={"color": COLORS["actual"]}))
    actual = part[part.model.eq("hw_expanding" if windows else "hw_weekly")]
    visible_methods = set(part.model)
    if windows:
        left, right = st.columns(2)
        with left:
            smoothing = st.multiselect("Smoothing histories", ["hw_expanding","hw_182d","hw_365d"], default=["hw_expanding"], format_func=lambda m: LABELS[m], key="window_methods")
        with right:
            baselines = st.multiselect("Baseline comparisons", ["seasonal_naive","weekday_mean_4w","weekday_mean_8w"], default=["weekday_mean_4w"], format_func=lambda m: LABELS[m], key="window_baselines")
        visible_methods = set(smoothing+baselines)
        st.caption("The method controls change saved chart series only. Expanding starts December 1, 2009; trailing histories end at the same cutoff and contain exactly 182 or 365 calendar days.")
    fig.add_trace(go.Scatter(x=actual.date, y=actual.actual, name="Observed evaluation sales", line={"color": COLORS["actual"]}))
    for model, series in part.groupby("model"):
        if model not in visible_methods:
            continue
        fig.add_trace(go.Scatter(x=series.date, y=series.prediction, name=LABELS[model], line={"color": COLORS[model], "dash": "solid" if model == "hw_weekly" else "dash"}))
    fig.add_vrect(x0=str(start.date()), x1=str((end+pd.Timedelta(days=1)).date()), fillcolor="#eab96b", opacity=0.13, line_width=0)
    fig.add_annotation(x=str(start.date()), y=1, yref="paper", text="28-day evaluation", showarrow=False, xanchor="left")
    fig.update_layout(height=410, xaxis_title="Historical date", yaxis_title="Positive units sold", legend={"orientation": "h", "y": -0.2}, margin={"t": 30})
    st.plotly_chart(fig, width="stretch")
    st.caption("The shaded region is evaluation; each forecast uses the training cutoff only and never incorporates actual sales within that horizon.")
    product = product_metrics.query("product_id == @pid").copy()
    col1, col2 = st.columns(2)
    shown = ["model", "mae", "wape"]
    with col1:
        st.markdown("**Selected product only**")
        st.dataframe(product[shown], hide_index=True, width="stretch", column_config={"mae": st.column_config.NumberColumn("MAE (units)", format="%.2f"), "wape": st.column_config.NumberColumn("Product WAPE (%)", format="%.2f")})
    with col2:
        st.markdown(f"**Whole {len(metadata)}-product cohort, this period**")
        st.dataframe(cohort_metrics[shown].assign(model=lambda f:f.model.map(LABELS)), hide_index=True, width="stretch", column_config={"mae": st.column_config.NumberColumn("MAE (units)", format="%.2f"), "wape": st.column_config.NumberColumn("Pooled WAPE (%)", format="%.2f")})
    with st.expander("Cohort membership and historical coverage"):
        st.write(f"Grid coverage: {hist.date.min():%Y-%m-%d} to {hist.date.max():%Y-%m-%d}; {int(hist.units.gt(0).sum())} positive-sales days.")
        st.dataframe(metadata.reset_index(), hide_index=True)
        if not original:
            st.json(d["robustness/split_manifest"]["cohort_comparison"])

with performance:
    st.subheader("Training-window experiment · six periods pooled")
    summary = d["portfolio/summary"]
    st.info(f"Lowest pooled error among tested methods: four-week weekday average, {summary['candidate_wape']:.2f}% WAPE versus {summary['comparator_wape']:.2f}% for last-week repetition. Relative error reduction: {summary['relative_error_reduction_pct']:.1f}% across {summary['products']} products and {summary['periods']} retrospective {summary['horizon_days']}-day periods. Errors remain substantial.")
    st.caption("20 fixed products; 3,360 product-days per method. WAPE is normalized absolute error, not accuracy. Retrospective analysis; lower is better.")
    window_metrics = d["training_windows_v1/overall_metrics"]
    shown_metrics = window_metrics[["model","mae","wape","mean_product_wape","signed_bias","percentage_bias"]].copy()
    shown_metrics["model"] = shown_metrics.model.map(LABELS)
    st.dataframe(shown_metrics, hide_index=True, width="stretch", column_config={"model":"Method", "wape":st.column_config.NumberColumn("Pooled WAPE (%)",format="%.2f"), "mae":st.column_config.NumberColumn("MAE (units)",format="%.2f"), "mean_product_wape":st.column_config.NumberColumn("Mean product WAPE (%)",format="%.2f"), "signed_bias":st.column_config.NumberColumn("Bias (units)",format="%+.2f"), "percentage_bias":st.column_config.NumberColumn("Bias (%)",format="%+.2f")})
    window_candidate = st.selectbox("Compare smoothing history", ["hw_expanding","hw_182d","hw_365d"],format_func=lambda m:LABELS[m],key="window_candidate")
    window_pairs = d["training_windows_v1/pairwise_comparisons"].query("model == @window_candidate")
    pair_display = window_pairs[["baseline","relative_wape_reduction_pct","wins","losses","ties","undefined"]].copy()
    pair_display["baseline"] = pair_display.baseline.map(LABELS)
    st.dataframe(pair_display,hide_index=True,width="stretch",column_config={"baseline":"Comparator","relative_wape_reduction_pct":st.column_config.NumberColumn("Relative WAPE reduction (%)",format="%+.2f")})
    window_period = d["training_windows_v1/period_metrics"].copy()
    window_period["method"] = window_period.model.map(LABELS)
    fig = px.line(window_period[window_period.model.isin(["hw_expanding","hw_182d","hw_365d"])],x="forecast_start",y="wape",color="method",markers=True,color_discrete_map={LABELS[m]:COLORS[m] for m in ["hw_expanding","hw_182d","hw_365d"]})
    fig.update_layout(height=290,xaxis_title="Historical forecast start",yaxis_title="Period pooled WAPE (%)",legend={"orientation":"h","y":-0.25,"title":""},margin={"t":10})
    st.plotly_chart(fig,width="stretch")
    st.caption("Each point is one 28-day evaluation; six-period WAPE pools errors and actual units. Period differences are descriptive and do not establish statistical significance.")
    with st.expander("Training-window product contributions, bias, spikes and fit records"):
        contribution = d["training_windows_v1/product_contributions"].query("model == @window_candidate and baseline == 'hw_expanding'")
        if contribution.empty:
            contribution = d["training_windows_v1/product_contributions"].query("model == @window_candidate and baseline == 'weekday_mean_4w'")
        st.dataframe(contribution.sort_values("actual_units",ascending=False),hide_index=True,width="stretch")
        st.write("Common spikes: actual units strictly above the product/origin expanding-history 99th percentile, including zeros and using linear interpolation. All spikes remain in primary metrics.")
        st.dataframe(d["training_windows_v1/spike_summary"],hide_index=True,width="stretch")
        st.dataframe(d["training_windows_v1/spike_examples"],hide_index=True,width="stretch")
        st.dataframe(d["training_windows_v1/fit_records"],hide_index=True,width="stretch")
        st.dataframe(d["training_windows_v1/period_comparisons"],hide_index=True,width="stretch")
    st.subheader("Retrospective robustness · six periods pooled")
    st.caption(f"Scope: {len(d['robustness/product_metadata'])} fixed products selected before January 1, 2011; all four methods use the same observations.")
    st.caption("Lower WAPE is better; MAE is units per product-day, and positive bias means overprediction.")
    metrics = d["robustness/overall_metrics"]
    display_metrics = metrics[["model", "mae", "wape", "mean_product_wape", "signed_bias", "percentage_bias"]].copy()
    display_metrics["model"] = display_metrics.model.map(LABELS)
    st.dataframe(display_metrics, hide_index=True, width="stretch", column_config={
        "model": "Method", "mae": st.column_config.NumberColumn("MAE (units)", format="%.2f"),
        "wape": st.column_config.NumberColumn("Pooled WAPE (%)", format="%.2f"),
        "mean_product_wape": st.column_config.NumberColumn("Mean product WAPE (%)", format="%.2f"),
        "signed_bias": st.column_config.NumberColumn("Bias (units)", format="%+.2f"),
        "percentage_bias": st.column_config.NumberColumn("Bias (%)", format="%+.2f")})
    st.markdown("**Weekly smoothing versus each baseline**")
    comparison_table = d["robustness/baseline_comparisons"][["baseline", "relative_wape_reduction_pct", "wins", "losses", "ties", "undefined"]].copy()
    comparison_table["baseline"] = comparison_table.baseline.map(LABELS)
    st.dataframe(comparison_table, hide_index=True, width="stretch", column_config={"baseline": "Baseline", "relative_wape_reduction_pct": st.column_config.NumberColumn("Relative WAPE reduction (%)", format="%+.2f"), "wins": "Wins", "losses": "Losses", "ties": "Ties", "undefined": "Undefined"})
    period = d["robustness/period_metrics"].copy()
    period["method"] = period.model.map(LABELS)
    fig = px.line(period, x="forecast_start", y="wape", color="method", markers=True, color_discrete_map={LABELS[k]:v for k,v in COLORS.items() if k in LABELS})
    fig.update_layout(height=290, xaxis_title="Historical forecast start", yaxis_title="Pooled WAPE (%)", legend={"orientation": "h", "y": -0.25, "title": ""}, margin={"t": 10})
    st.plotly_chart(fig, width="stretch")
    st.caption("Each point evaluates a fixed 28-day forecast; overall WAPE is calculated from summed errors and sales, rather than averaging these percentages.")
    baseline_choice = st.selectbox("Product wins/losses against", ["seasonal_naive", "weekday_mean_4w", "weekday_mean_8w"], format_func=lambda b: LABELS[b], key="comparison")
    with st.expander("Product comparisons and period results"):
        st.dataframe(d["robustness/product_comparisons"].query("baseline == @baseline_choice"), hide_index=True, width="stretch")
        st.dataframe(d["robustness/period_comparisons"], hide_index=True, width="stretch")
    st.subheader("Existing corrected benchmark · error analysis")
    st.caption("Separate experiment: 20 products, November 11–December 8, 2011; corrected WAPE 80.24% versus 112.80% baseline, with 10/20 product wins.")
    errors = d["benchmark_analysis/product_error_analysis"].sort_values("error_reduction_units")
    fig = px.bar(errors, x="error_reduction_units", y="product_id", orientation="h", hover_data=["description"], color="error_reduction_units", color_continuous_scale="RdBu", color_continuous_midpoint=0)
    fig.update_layout(height=600, xaxis_title="Baseline absolute error minus model absolute error (units)", yaxis_title="Product code", yaxis_type="category", margin={"t": 10}, coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")
    st.caption("Positive bars identify improvement; negative bars show deterioration, with every product retained in the pooled result.")
    with st.expander("Five largest improvements/deteriorations, bias and spike examples"):
        for name in ["largest_improvements", "largest_deteriorations"]:
            st.dataframe(d[f"benchmark_analysis/{name}"][["product_id", "description", "error_reduction_units", "share_of_net_error_reduction_pct"]], hide_index=True)
        st.dataframe(d["benchmark_analysis/overall_metrics"][["model", "signed_bias", "percentage_bias", "overprediction_units", "underprediction_units"]], hide_index=True)
        st.dataframe(d["benchmark_analysis/spike_summary"], hide_index=True)
        days = d["benchmark_analysis/daily_errors"]
        examples = days[days.model.eq("hw_weekly")].nlargest(3, "actual").product_id.unique().tolist()
        spike_pid = st.selectbox("Spike example product", examples, key="spike_product")
        sample = days.query("product_id == @spike_pid")
        actual = sample[sample.model.eq("hw_weekly")]
        fig = go.Figure(go.Scatter(x=actual.date, y=actual.actual, name="Observed sales", line={"color": COLORS["actual"]}))
        for model, series in sample.groupby("model"):
            fig.add_trace(go.Scatter(x=series.date, y=series.prediction, name=LABELS[model], line={"color": COLORS[model]}))
        fig.update_layout(height=300, yaxis_title="Units", xaxis_title="Historical test date", legend={"orientation": "h"})
        st.plotly_chart(fig, width="stretch")
        st.caption("Spikes exceed the product's training-history 99th percentile; they remain in all primary errors, and their causes are unverified.")
    st.write("MAE: average absolute error in units. Pooled WAPE: 100 × total absolute error / total observed units. Mean product WAPE weights products equally. Bias: prediction minus actual; positive means overprediction. Zero denominators produce undefined percentages. WAPE is not accuracy.")
    st.caption("Sales proxy demand; the source cannot reveal lost sales or actual inventory. Later-2011 family selection and overlapping periods make robustness retrospective. Results are limited to high-volume cohorts and six historical windows.")
    with st.expander("Original validation evidence, frozen protocol and fit events"):
        st.dataframe(d["benchmark/validation_overall_metrics"], hide_index=True)
        st.json(json.loads((ROOT / "protocols/robustness_v1.json").read_text(encoding="utf-8")))
        st.json(d["robustness/model_events"])
