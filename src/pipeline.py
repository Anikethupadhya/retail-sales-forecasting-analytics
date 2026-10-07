"""python -m src.pipeline: all-merchandise sales, archived analysis and fixed robustness."""
import hashlib
import importlib.metadata
import json
import platform
import time

import pandas as pd

from .common import ROOT, OUT, load_config, save_json
from .analytics import build_sales_database
from .cohort import select_cohort, daily_grid, make_robustness_splits
from .data import prepare_sales
from .evidence import BENCHMARK, verify_archives, benchmark_analysis
from .forecast import evaluate
from .metrics import summaries, comparisons


def main():
    started = time.time()
    OUT.mkdir(exist_ok=True)
    (OUT / "run_manifest.json").unlink(missing_ok=True)
    cfg = load_config()
    archive_count = verify_archives()
    protocol_path = ROOT / cfg["robustness_protocol"]
    protocol_hash = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    if protocol_hash != protocol_path.with_suffix(".sha256").read_text(encoding="utf-8").strip():
        raise ValueError("Frozen protocol checksum mismatch")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if any(cfg[k] != v for k, v in protocol["eligibility"].items()) or cfg["models"] != protocol["models"]:
        raise ValueError("Config differs from frozen protocol")
    if cfg["horizon_days"] != protocol["horizon_days"] or cfg["clip_forecasts_at_zero"] != protocol["nonnegative_clipping"]:
        raise ValueError("Forecast rules differ from frozen protocol")
    print("Reading and auditing both official workbook sheets", flush=True)
    sales, metadata, calendar, audit = prepare_sales(cfg)
    build_sales_database(sales, metadata, calendar)
    print("Reconciled sales aggregates; analysing immutable corrected benchmark", flush=True)
    benchmark_analysis()
    robust = OUT / "robustness"
    robust.mkdir(exist_ok=True)
    selected, eligibility, cohort_metadata = select_cohort(sales, calendar.date.min(), protocol["selection_cutoff_exclusive"], protocol["eligibility"])
    eligibility.to_csv(robust / "product_eligibility.csv", index=False)
    cohort_metadata.to_csv(robust / "product_metadata.csv", index=False)
    daily = daily_grid(sales, selected, calendar.date.min(), calendar.date.max())
    daily.to_csv(robust / "daily_sales.csv", index=False)
    splits = make_robustness_splits(protocol, calendar.date.min(), calendar.date.max())
    old = json.loads((BENCHMARK / "split_manifest.json").read_text(encoding="utf-8"))["selected_product_ids"]
    manifest = {"experiment": protocol["experiment"], "protocol_sha256": protocol_hash,
                "selection_cutoff_exclusive": protocol["selection_cutoff_exclusive"], "selected_product_ids": selected,
                "criteria": protocol["eligibility"], "ranking": protocol["ranking"], "splits": splits,
                "cohort_comparison": {"shared": sorted(set(old)&set(selected)), "robustness_only": sorted(set(selected)-set(old)),
                                      "existing_benchmark_only": sorted(set(old)-set(selected))}, "limitations": protocol["limitations"]}
    save_json(robust / "split_manifest.json", manifest)
    # Manifest and frozen protocol exist before computing any robustness predictions.
    predictions, events = evaluate(daily, splits, protocol["models"], cfg)
    predictions.to_csv(robust / "predictions.csv", index=False)
    overall, products = summaries(predictions)
    compare, product_compare = comparisons(overall, products, tolerance=protocol["tie_absolute_error_tolerance"])
    for name, frame in [("overall_metrics", overall), ("product_metrics", products), ("baseline_comparisons", compare), ("product_comparisons", product_compare)]:
        frame.to_csv(robust / f"{name}.csv", index=False)
    period_metrics, period_products, period_compare, period_product_compare = [], [], [], []
    for split, part in predictions.groupby("split", sort=True):
        metric, per_product = summaries(part)
        comp, detail = comparisons(metric, per_product, tolerance=protocol["tie_absolute_error_tolerance"])
        for frame, collection in [(metric, period_metrics), (per_product, period_products), (comp, period_compare), (detail, period_product_compare)]:
            frame["forecast_start"] = split
            collection.append(frame)
    for name, frames in [("period_metrics", period_metrics), ("period_product_metrics", period_products), ("period_comparisons", period_compare), ("period_product_comparisons", period_product_compare)]:
        pd.concat(frames, ignore_index=True).to_csv(robust / f"{name}.csv", index=False)
    save_json(robust / "model_events.json", events)
    save_json(OUT / "run_manifest.json", {"project": cfg["name"], "completed": True, "python": platform.python_version(),
              "packages": {p: importlib.metadata.version(p) for p in ["pandas", "numpy", "duckdb", "statsmodels", "scipy", "plotly", "streamlit", "openpyxl", "pyarrow", "pytest"]},
              "raw_sha256": audit["sha256"], "config_sha256": hashlib.sha256((ROOT / "config.json").read_bytes()).hexdigest(),
              "protocol_sha256": protocol_hash, "historical_archive_files_verified": archive_count,
              "duration_seconds": round(time.time()-started, 2)})
    from .training_windows import run as run_training_windows
    run_training_windows()
    from .report import generate
    generate()
    print(overall.to_string(index=False), flush=True)
    print(compare.to_string(index=False), flush=True)
    print(f"Completed in {time.time()-started:.1f}s", flush=True)


if __name__ == "__main__":
    main()
