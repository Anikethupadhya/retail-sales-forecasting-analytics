"""Immutable historical evidence and benchmark error decomposition."""
import hashlib
import json

import numpy as np
import pandas as pd

from .common import ROOT, OUT, save_json
from .metrics import summaries

ARCHIVE = ROOT / "archives"
BENCHMARK = ARCHIVE / "benchmark_corrected"


def verify_archives():
    manifest = json.loads((ARCHIVE / "manifest.json").read_text())
    for path, expected in manifest["archive_files"].items():
        if hashlib.sha256((ARCHIVE / path).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Historical archive changed: {path}")
    return len(manifest["archive_files"])


def benchmark_analysis():
    out = OUT / "benchmark_analysis"
    out.mkdir(parents=True, exist_ok=True)
    predictions = pd.read_csv(BENCHMARK / "test_predictions.csv", dtype={"product_id": str})
    history = pd.read_csv(BENCHMARK / "daily_sales.csv", dtype={"product_id": str}, parse_dates=["date"])
    metadata = pd.read_csv(BENCHMARK / "product_metadata.csv", dtype={"product_id": str}).set_index("product_id")
    overall, products = summaries(predictions)
    archived = pd.read_csv(BENCHMARK / "test_overall_metrics.csv").set_index("model")
    for _, row in overall.iterrows():
        for metric in ["wape", "mae", "absolute_error_sum", "actual_units"]:
            np.testing.assert_allclose(row[metric], archived.loc[row.model, metric], rtol=1e-10, atol=1e-8)
    selected = products[products.model.eq("hw_weekly")].set_index("product_id")
    baseline = products[products.model.eq("seasonal_naive")].set_index("product_id")
    net_reduction = baseline.absolute_error_sum.sum() - selected.absolute_error_sum.sum()
    selected["description"] = metadata.description
    selected["baseline_wape"] = baseline.wape
    selected["baseline_absolute_error"] = baseline.absolute_error_sum
    selected["error_reduction_units"] = baseline.absolute_error_sum - selected.absolute_error_sum
    selected["relative_wape_reduction_pct"] = 100 * (baseline.wape - selected.wape) / baseline.wape.replace(0, np.nan)
    selected["share_of_model_absolute_error_pct"] = 100 * selected.absolute_error_sum / selected.absolute_error_sum.sum()
    selected["share_of_net_error_reduction_pct"] = 100 * selected.error_reduction_units / net_reduction if net_reduction else np.nan
    selected = selected.reset_index()
    selected.to_csv(out / "product_error_analysis.csv", index=False)
    selected[selected.error_reduction_units.gt(0)].nlargest(5, "error_reduction_units").to_csv(out / "largest_improvements.csv", index=False)
    selected[selected.error_reduction_units.lt(0)].nsmallest(5, "error_reduction_units").to_csv(out / "largest_deteriorations.csv", index=False)
    threshold_rows, spike_rows = [], []
    for pid, group in predictions.groupby("product_id"):
        origin = pd.Timestamp(group.origin.iloc[0])
        training = history[history.product_id.eq(pid) & history.date.le(origin)].units
        threshold = float(training.quantile(0.99, interpolation="linear"))
        threshold_rows.append({"product_id": pid, "training_end": str(origin.date()), "training_days": len(training), "spike_threshold_units": threshold})
        for _, row in group.iterrows():
            spike_rows.append({"product_id": pid, "description": metadata.loc[pid, "description"], "date": row.date,
                               "model": row.model, "actual": row.actual, "prediction": row.prediction,
                               "absolute_error": abs(row.prediction-row.actual), "signed_error": row.prediction-row.actual,
                               "spike_threshold_units": threshold, "is_spike": row.actual > threshold})
    days = pd.DataFrame(spike_rows)
    days.to_csv(out / "daily_errors.csv", index=False)
    pd.DataFrame(threshold_rows).to_csv(out / "spike_thresholds.csv", index=False)
    spike_summary = []
    for model, part in days.groupby("model"):
        spikes = part[part.is_spike]
        spike_summary.append({"model": model, "spike_product_days": len(spikes), "product_days": len(part),
                              "spike_absolute_error": float(spikes.absolute_error.sum()),
                              "total_absolute_error": float(part.absolute_error.sum()),
                              "spike_error_share_pct": float(100*spikes.absolute_error.sum()/part.absolute_error.sum())})
    pd.DataFrame(spike_summary).to_csv(out / "spike_summary.csv", index=False)
    overall.to_csv(out / "overall_metrics.csv", index=False)
    save_json(out / "reconciliation.json", {"archived_metrics_reconciled": True, "absolute_tolerance": 1e-8, "relative_tolerance": 1e-10,
              "net_absolute_error_reduction_units": float(net_reduction), "source": "archives/benchmark_corrected/test_predictions.csv",
              "spike_rule": "Actual units strictly exceed product training-history 99th percentile, linear interpolation, through 2011-11-10. Zero days included. Spikes retained in every primary metric.",
              "causality": "Patterns are observed; order/customer motives and promotion effects are not established by these aggregate outputs."})
    return selected, days
