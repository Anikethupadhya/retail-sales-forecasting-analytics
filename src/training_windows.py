"""Prespecified training histories; saved evidence from common forecast support."""
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time

import numpy as np
import pandas as pd

from .common import ROOT, OUT, load_config, save_json
from .cohort import make_robustness_splits
from .forecast import predict, seasonal_naive
from .metrics import summaries, comparisons, score

BASELINES = {"seasonal_naive": 7, "weekday_mean_4w": 28, "weekday_mean_8w": 56}
WINDOWS = {"hw_expanding": None, "hw_182d": 182, "hw_365d": 365}


def load_protocol():
    path = ROOT / "protocols/training_windows_v1.json"
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != path.with_suffix(".sha256").read_text(encoding="utf-8").strip():
        raise ValueError("Training-window protocol checksum mismatch")
    p = json.loads(path.read_text(encoding="utf-8"))
    old = json.loads((ROOT/"protocols/robustness_v1.json").read_text(encoding="utf-8"))
    for key in ["forecast_start_dates", "horizon_days", "eligibility", "selection_cutoff_exclusive", "hw_weekly", "failure_policy", "nonnegative_clipping", "tie_absolute_error_tolerance"]:
        if p[key] != old[key]:
            raise ValueError(f"Training-window protocol changed established rule: {key}")
    if p["smoothing_methods"] != WINDOWS or p["baseline_history_days"] != BASELINES:
        raise ValueError("Unexpected methods or history lengths")
    return p, checksum


def preflight(daily, splits, products, protocol):
    if daily.duplicated(["product_id", "date"]).any() or set(daily.product_id) != set(products):
        raise ValueError("Duplicate or changed product population")
    if not np.isfinite(daily.units).all() or daily.units.lt(0).any():
        raise ValueError("History/actuals must be finite nonnegative sales")
    for split in splits:
        start = pd.Timestamp(split["forecast_start"])
        if pd.Timestamp(split["train_end"]) != start-pd.Timedelta(days=1):
            raise ValueError("Training cutoff must precede origin")
        if pd.Timestamp(split["forecast_end"]) != start+pd.Timedelta(days=27):
            raise ValueError("Exactly 28 consecutive forecast dates required")
        grid = pd.date_range(protocol["expanding_start"], split["forecast_end"])
        if (start-pd.Timestamp(protocol["expanding_start"])).days < 365:
            raise ValueError("Insufficient calendar history for the declared windows")
        for pid in products:
            dates = pd.DatetimeIndex(daily.loc[daily.product_id.eq(pid), "date"]).sort_values()
            if not dates[(dates >= grid.min()) & (dates <= grid.max())].equals(grid):
                raise ValueError(f"Incomplete calendar grid for {pid} at {start.date()}")


def evaluate_windows(daily, splits, products, protocol, cfg):
    preflight(daily, splits, products, protocol)
    rows, fits, thresholds = [], [], []
    for split in splits:
        start = pd.Timestamp(split["forecast_start"])
        origin = start-pd.Timedelta(days=1)
        future = pd.date_range(start, periods=28)
        for pid in products:
            series = daily.loc[daily.product_id.eq(pid)].sort_values("date").set_index("date").units
            expanding = series.loc[pd.Timestamp(protocol["expanding_start"]):origin]
            actual = series.reindex(future).to_numpy(dtype=float)
            threshold = float(expanding.quantile(.99, interpolation="linear"))
            thresholds.append({"product_id": pid, "forecast_start": split["forecast_start"], "train_start": str(expanding.index.min().date()), "train_end": str(origin.date()), "training_observations": len(expanding), "threshold_99": threshold})
            for method, window in {**WINDOWS, **BASELINES}.items():
                train_start = expanding.index.min() if window is None else start-pd.Timedelta(days=window)
                history = series.loc[train_start:origin].to_numpy(dtype=float)
                if len(history) != (len(expanding) if window is None else window):
                    raise ValueError("History length does not match frozen boundary")
                status, messages, error, clipped = "ok", [], None, 0
                try:
                    values, messages, failed = predict(history, "hw_weekly" if method in WINDOWS else method, 28)
                    if failed:
                        status = "nonconverged_baseline_fallback"
                        values = seasonal_naive(history, 28)
                    if len(values) != 28 or not np.isfinite(values).all():
                        raise ValueError("Invalid model forecast")
                    clipped = int((values < 0).sum())
                    values = np.maximum(values, 0) if cfg["clip_forecasts_at_zero"] else values
                except Exception as exc:
                    if method not in WINDOWS:
                        raise
                    status, error = "failure_baseline_fallback", str(exc)
                    values = seasonal_naive(history, 28)
                fit = {"model": method, "product_id": pid, "forecast_start": split["forecast_start"],
                       "train_start": str(train_start.date()), "train_end": str(origin.date()), "training_observations": len(history),
                       "status": status, "warnings": messages, "error": error, "negative_predictions_clipped": clipped}
                fits.append(fit)
                for step, (date, observed, value) in enumerate(zip(future, actual, values, strict=True), 1):
                    rows.append({"experiment": protocol["experiment"], "model": method, "product_id": pid,
                        "forecast_start": split["forecast_start"], "forecast_end": split["forecast_end"], "date": date,
                        "origin": origin, "train_last_date": origin, "train_start": train_start, "training_observations": len(history),
                        "horizon_day": step, "actual": observed, "prediction": float(value), "status": status,
                        "spike_threshold": threshold, "is_spike": bool(observed > threshold)})
    predictions = pd.DataFrame(rows)
    validate_support(predictions, products, splits)
    return predictions, fits, pd.DataFrame(thresholds)


def validate_support(predictions, products, splits):
    key = ["experiment", "model", "product_id", "forecast_start", "date"]
    if predictions.duplicated(key).any():
        raise ValueError("Duplicate prediction key")
    expected = len(products)*len(splits)*28
    if set(predictions.model) != set(WINDOWS)|set(BASELINES) or not predictions.groupby("model").size().eq(expected).all():
        raise ValueError("Incomplete method coverage")
    support_key = ["product_id", "forecast_start", "date"]
    reference = None
    for _, part in predictions.groupby("model"):
        part = part.sort_values(support_key).reset_index(drop=True)
        support = part[support_key+["actual", "is_spike", "spike_threshold"]]
        if reference is None:
            reference = support
        else:
            pd.testing.assert_frame_equal(reference, support, check_exact=True)
        if not part.groupby(["product_id", "forecast_start"]).size().eq(28).all():
            raise ValueError("Product-origin horizon coverage mismatch")
        if not ((part.date-pd.to_datetime(part.forecast_start)).dt.days+1).eq(part.horizon_day).all():
            raise ValueError("Forecast dates are not consecutive")


def all_comparisons(overall, products, tolerance):
    pairs, details = [], []
    for model in WINDOWS:
        p,d = comparisons(overall, products, candidate=model, tolerance=tolerance)
        d["model"] = model
        pairs.append(p)
        details.append(d)
    return pd.concat(pairs, ignore_index=True), pd.concat(details, ignore_index=True)


def reconcile_reference(predictions, reference):
    key = ["model", "product_id", "forecast_start", "date"]
    current = predictions[predictions.model.isin(["hw_expanding", *BASELINES])].copy()
    current["model"] = current.model.replace({"hw_expanding": "hw_weekly"})
    current["date"] = pd.to_datetime(current.date)
    reference = reference.copy()
    reference["date"] = pd.to_datetime(reference.date)
    current, reference = [f.sort_values(key).reset_index(drop=True) for f in [current, reference]]
    pd.testing.assert_frame_equal(current[key], reference[key], check_exact=True)
    for column in ["prediction", "actual"]:
        np.testing.assert_allclose(current[column], reference[column], rtol=1e-10, atol=1e-8)
    assert current.status.equals(reference.status), "Fit statuses changed"
    return {"status": "passed", "rows": len(current), "methods": ["hw_expanding", *BASELINES], "relative_tolerance": 1e-10, "absolute_tolerance": 1e-8, "statuses_equal": True}


def run():
    started = time.time()
    protocol, checksum = load_protocol()
    cfg = load_config()
    if cfg["horizon_days"] != 28 or cfg["clip_forecasts_at_zero"] is not True:
        raise ValueError("Configuration differs from frozen experiment")
    cohort = json.loads((OUT/"robustness/split_manifest.json").read_text(encoding="utf-8"))
    if cohort["selected_product_ids"] != protocol["selected_product_ids"]:
        raise ValueError("Robustness cohort differs from the committed protocol")
    protocol_commit = subprocess.check_output(["git", "log", "--diff-filter=A", "--format=%H", "--", "protocols/training_windows_v1.json"], cwd=ROOT, text=True).strip().splitlines()[0]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    committed = subprocess.check_output(["git", "show", f"{revision}:protocols/training_windows_v1.json"], cwd=ROOT)
    if hashlib.sha256(committed).hexdigest() != checksum:
        raise ValueError("Protocol must be committed before execution")
    daily = pd.read_csv(OUT/"robustness/daily_sales.csv", dtype={"product_id": str}, parse_dates=["date"])
    splits = make_robustness_splits(protocol, daily.date.min(), daily.date.max())
    # Record source changes, excluding expected removal/regeneration of saved output copies.
    implementation_paths = ["src", "sql", "tests", "scripts", "protocols", ".github", "app.py", "config.json", "requirements.txt", "pytest.ini", "package.json", "package-lock.json"]
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain", "--", *implementation_paths], cwd=ROOT, text=True).strip())
    predictions, fits, thresholds = evaluate_windows(daily, splits, protocol["selected_product_ids"], protocol, cfg)
    reconciliation = reconcile_reference(predictions, pd.read_csv(OUT/"robustness/predictions.csv", dtype={"product_id": str}))
    out = OUT/"training_windows_v1"
    out.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(out/"predictions.csv", index=False)
    thresholds.to_csv(out/"spike_thresholds.csv", index=False)
    fit_frame = pd.DataFrame(fits).drop(columns=["warnings", "error"])
    fit_frame.to_csv(out/"fit_records.csv", index=False)
    save_json(out/"model_events.json", fits)
    save_json(out/"reference_reconciliation.json", reconciliation)
    overall, products = summaries(predictions)
    pairs, detail = all_comparisons(overall, products, protocol["tie_absolute_error_tolerance"])
    for name, frame in [("overall_metrics", overall), ("product_metrics", products), ("pairwise_comparisons", pairs), ("product_comparisons", detail)]:
        frame.to_csv(out/f"{name}.csv", index=False)
    collections = {k: [] for k in ["period_metrics", "period_product_metrics", "period_comparisons", "period_product_comparisons"]}
    for origin, part in predictions.groupby("forecast_start"):
        o,p = summaries(part)
        c,d = all_comparisons(o,p,protocol["tie_absolute_error_tolerance"])
        for name, frame in zip(collections, [o,p,c,d], strict=True):
            collections[name].append(frame.assign(forecast_start=origin))
    for name, frames in collections.items():
        pd.concat(frames, ignore_index=True).to_csv(out/f"{name}.csv", index=False)
    spike_rows = []
    for model, part in predictions.groupby("model"):
        error = (part.prediction-part.actual).abs()
        spike_error = float(error[part.is_spike].sum())
        spike_rows.append({"model": model, "spike_product_days": int(part.is_spike.sum()), "product_days": len(part), "spike_absolute_error": spike_error,
                           "total_absolute_error": float(error.sum()), "spike_error_share_pct": 100*spike_error/error.sum() if error.sum() else None})
    pd.DataFrame(spike_rows).to_csv(out/"spike_summary.csv", index=False)
    metadata = pd.read_csv(OUT/"robustness/product_metadata.csv", dtype={"product_id": str})[["product_id", "description"]]
    contribution = detail.merge(metadata, on="product_id", validate="many_to_one").merge(products[["model", "product_id", "actual_units", "absolute_error_sum", "signed_bias"]], on=["model", "product_id"], validate="many_to_one")
    contribution["share_of_actual_units_pct"] = 100*contribution.actual_units/overall.actual_units.iloc[0]
    contribution["share_of_model_error_pct"] = contribution.groupby(["model", "baseline"]).absolute_error_sum.transform(lambda x:100*x/x.sum())
    contribution.to_csv(out/"product_contributions.csv", index=False)
    predictions[predictions.model.eq("hw_expanding") & predictions.is_spike].merge(metadata, on="product_id").sort_values("actual", ascending=False).head(10).to_csv(out/"spike_examples.csv", index=False)
    save_json(out/"experiment_manifest.json", {"experiment": protocol["experiment"], "protocol_commit": protocol_commit, "protocol_sha256": checksum,
        "implementation_revision": revision, "implementation_inputs_dirty_before_execution": dirty, "selected_product_ids": protocol["selected_product_ids"],
        "forecast_start_dates": protocol["forecast_start_dates"], "rows_per_method": len(protocol["selected_product_ids"])*6*28, "prediction_rows": len(predictions),
        "source_checksums": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for folder in ["src", "sql", "protocols"] for p in (ROOT/folder).glob("*") if p.is_file()},
        "input_checksums": {f: hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in ["robustness/daily_sales.csv", "robustness/split_manifest.json", "robustness/predictions.csv"]},
        "raw_sha256": json.loads((OUT/"sales/data_audit.json").read_text(encoding="utf-8"))["sha256"], "python": platform.python_version(),
        "packages": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "statsmodels", "scipy"]}, "duration_seconds": round(time.time()-started, 3), "limitations": protocol["limitations"]})
    print(overall[["model", "mae", "wape", "signed_bias"]].to_string(index=False), flush=True)
    return overall


if __name__ == "__main__":
    run()
