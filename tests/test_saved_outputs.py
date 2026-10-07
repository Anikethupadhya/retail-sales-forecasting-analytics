import hashlib
import json

import duckdb
import numpy as np
import pandas as pd
import pytest

from src.common import ROOT, OUT, load_config
from src.cohort import select_cohort, make_robustness_splits, daily_grid
from src.data import cross_sheet_replicas, aggregate_sales
from src.evidence import BENCHMARK, verify_archives
from src.forecast import evaluate, predict, seasonal_naive
from src.metrics import score, reduction, summaries, comparisons


from test_core import protocol
from src.training_windows import validate_support, reconcile_reference, load_protocol

@pytest.mark.integration
def test_saved_outputs_reconcile(saved_sales_database):
    assert verify_archives()>0
    audit = json.loads((OUT/"sales/data_audit.json").read_text())
    assert sum(audit["exclusive_exclusion_counts_in_priority_order"].values())+audit["retained_rows"]==audit["raw_rows"]
    old_audit = json.loads((BENCHMARK/"data_audit.json").read_text())
    assert audit["retained_rows"]==old_audit["retained_rows"]
    sales = pd.read_parquet(OUT/"sales/product_daily_sales.parquet")
    assert not {"Customer ID","Invoice","Country"}&set(sales.columns)
    assert sales.units.sum()==audit["positive_units"]
    assert sales.positive_sales_gbp.sum()==pytest.approx(audit["positive_sales_gbp"],abs=1e-6)
    assert sales.transaction_lines.sum()==audit["retained_rows"]
    manifest = json.loads((OUT/"robustness/split_manifest.json").read_text())
    rebuilt,_,_ = select_cohort(sales,sales.date.min(),"2011-01-01",protocol()["eligibility"])
    assert rebuilt==manifest["selected_product_ids"]
    predictions = pd.read_csv(OUT/"robustness/predictions.csv",dtype={"product_id":str})
    dates,origins = pd.to_datetime(predictions.date),pd.to_datetime(predictions.origin)
    assert ((dates-origins).dt.days==predictions.horizon_day).all()
    assert predictions.groupby(["split","product_id","model"]).size().eq(28).all()
    assert predictions.prediction.ge(0).all()
    assert predictions.train_last_date.eq(predictions.origin).all()
    o,p = summaries(predictions)
    saved = pd.read_csv(OUT/"robustness/overall_metrics.csv").set_index("model")
    for _,row in o.iterrows():
        assert saved.loc[row.model,"wape"]==pytest.approx(row.wape)
        assert row.absolute_error_sum==pytest.approx(p[p.model.eq(row.model)].absolute_error_sum.sum())
    ranking = pd.read_csv(OUT/"sales/product_rankings.csv")
    assert ranking.positive_units.sum()==audit["positive_units"]
    assert ranking.positive_sales_gbp.sum()==pytest.approx(audit["positive_sales_gbp"],abs=1e-6)
    with duckdb.connect(str(saved_sales_database),read_only=True) as con:
        assert {r[0] for r in con.execute("SHOW TABLES").fetchall()}=={"sales","product_metadata","calendar","daily_totals"}
    errors = pd.read_csv(OUT/"benchmark_analysis/product_error_analysis.csv")
    reconcile = json.loads((OUT/"benchmark_analysis/reconciliation.json").read_text())
    assert errors.error_reduction_units.sum()==pytest.approx(reconcile["net_absolute_error_reduction_units"])
    assert errors.share_of_model_absolute_error_pct.sum()==pytest.approx(100)
    assert errors.share_of_net_error_reduction_pct.sum()==pytest.approx(100)


@pytest.mark.integration
def test_training_window_saved_results_reconcile():
    folder = OUT/"training_windows_v1"
    p, checksum = load_protocol()
    manifest = json.loads((folder/"experiment_manifest.json").read_text())
    assert manifest["protocol_sha256"]==checksum
    predictions = pd.read_csv(folder/"predictions.csv",dtype={"product_id":str},parse_dates=["date","origin","train_last_date","train_start"])
    splits = make_robustness_splits(p, "2009-12-01", "2011-12-08")
    validate_support(predictions,p["selected_product_ids"],splits)
    assert len(predictions)==20160 and predictions.groupby("model").size().eq(3360).all()
    assert predictions.prediction.ge(0).all() and predictions.train_last_date.eq(predictions.origin).all()
    o, products = summaries(predictions)
    saved = pd.read_csv(folder/"overall_metrics.csv").set_index("model")
    for _, row in o.iterrows():
        for metric in ["mae","wape","signed_bias","percentage_bias","absolute_error_sum","actual_units","mean_product_wape"]:
            np.testing.assert_allclose(row[metric],saved.loc[row.model,metric],rtol=1e-10,atol=1e-8)
    periods = pd.read_csv(folder/"period_metrics.csv")
    for model, part in periods.groupby("model"):
        np.testing.assert_allclose(100*part.absolute_error_sum.sum()/part.actual_units.sum(),saved.loc[model,"wape"],rtol=1e-10,atol=1e-8)
    assert reconcile_reference(predictions,pd.read_csv(OUT/"robustness/predictions.csv",dtype={"product_id":str}))["status"]=="passed"
    fits = pd.read_csv(folder/"fit_records.csv",dtype={"product_id":str})
    assert len(fits)==720 and not fits.duplicated(["model","product_id","forecast_start"]).any()
    for method, count in {"hw_182d":182,"hw_365d":365,"seasonal_naive":7,"weekday_mean_4w":28,"weekday_mean_8w":56}.items():
        assert fits.loc[fits.model.eq(method),"training_observations"].eq(count).all()
    assert ((pd.to_datetime(fits.forecast_start)-pd.to_datetime(fits.train_end)).dt.days==1).all()
    events=json.loads((folder/"model_events.json").read_text())
    assert len(events)==len(fits)
    spikes=pd.read_csv(folder/"spike_summary.csv")
    assert spikes.spike_product_days.nunique()==1
    for _, row in spikes.iterrows():
        part=predictions[predictions.model.eq(row.model)]
        np.testing.assert_allclose(row.spike_absolute_error,(part.loc[part.is_spike,"prediction"]-part.loc[part.is_spike,"actual"]).abs().sum(),rtol=1e-10,atol=1e-8)
