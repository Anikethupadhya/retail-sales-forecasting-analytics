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


def protocol():
    return json.loads((ROOT / "protocols/robustness_v1.json").read_text())


def test_protocol_is_frozen_and_dates_are_unambiguous():
    path = ROOT / "protocols/robustness_v1.json"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == path.with_suffix(".sha256").read_text().strip()
    splits = make_robustness_splits(protocol(), "2009-12-01", "2011-12-08")
    assert len(splits) == 6
    assert splits[0]["train_end"] == "2010-12-31"
    assert splits[0]["forecast_end"] == "2011-01-28"
    assert splits[0]["training_days"] == 396
    for split in splits:
        assert pd.Timestamp(split["train_end"]) + pd.Timedelta(days=1) == pd.Timestamp(split["forecast_start"])
        assert (pd.Timestamp(split["forecast_end"])-pd.Timestamp(split["forecast_start"])).days == 27
    with pytest.raises(ValueError):
        make_robustness_splits(protocol(), "2009-12-01", "2011-11-15")


def test_cross_sheet_matching_retains_within_sheet_multiplicity():
    raw = pd.DataFrame({"Invoice": [1]*7, "Quantity": [5,5,5,5,5,6,5], "Customer ID": [np.nan]*7,
                        "source_sheet": ["a","a","b","b","b","b","a"], "excel_row": range(2,9)})
    assert cross_sheet_replicas(raw).tolist() == [False,False,True,True,False,False,True]


@pytest.mark.parametrize("model,weeks", [("weekday_mean_4w",4),("weekday_mean_8w",8)])
def test_weekday_baseline_arithmetic(model, weeks):
    # Every seven-day row is a calendar week aligned to the future start weekday.
    history = np.arange(1, weeks*7+1, dtype=float)
    expected_week = np.array([np.mean(history[i::7]) for i in range(7)])
    forecast, _, _ = predict(history, model, 28)
    np.testing.assert_allclose(forecast, np.tile(expected_week,4))
    with pytest.raises(ValueError):
        predict([1]*10, model,28)


def test_seasonal_naive_repeats_last_week():
    np.testing.assert_array_equal(seasonal_naive([999]*30+[1,2,3,4,5,6,7],28), np.tile([1,2,3,4,5,6,7],4))


@pytest.mark.parametrize("model", ["seasonal_naive","weekday_mean_4w","weekday_mean_8w","hw_weekly"])
def test_future_actuals_do_not_change_forecasts(model):
    dates = pd.date_range("2020-01-01", periods=428)
    sales = pd.DataFrame({"product_id":"12345", "date":dates, "units":np.tile(np.arange(1,8),62)[:428]})
    split = {"split":"probe", "stage":"test", "train_end":str(dates[399].date()), "forecast_start":str(dates[400].date()), "forecast_end":str(dates[-1].date())}
    before,_ = evaluate(sales,[split],[model],load_config())
    sales.loc[400:,"units"] = 100000
    after,_ = evaluate(sales,[split],[model],load_config())
    np.testing.assert_array_equal(before.prediction,after.prediction)
    assert not np.array_equal(before.actual,after.actual)


def test_cohort_does_not_use_future_selection_information():
    dates = pd.date_range("2009-12-01", "2011-12-08")
    sales = pd.concat([pd.DataFrame({"product_id":p,"date":dates,"units":v,"description":p}) for p,v in [("a",1),("b",2)]])
    rules = protocol()["eligibility"].copy()
    rules["product_count"] = 1
    first, _, _ = select_cohort(sales,dates.min(),"2011-01-01",rules)
    assert first == ["b"]
    sales.loc[sales.date.ge("2011-01-01") & sales.product_id.eq("a"),"units"] = 100000
    second, _, _ = select_cohort(sales,dates.min(),"2011-01-01",rules)
    assert second == first
    fewer, _, _ = select_cohort(sales,dates.min(),"2011-01-01",protocol()["eligibility"])
    assert len(fewer) == 2  # Accept fewer, never relax criteria.


def test_metrics_bias_zero_denominators_and_pooled_ratio():
    s = score([10,0,20],[8,4,24])
    assert s["mae"] == pytest.approx(10/3)
    assert s["wape"] == pytest.approx(100/3)
    assert s["signed_bias"] == pytest.approx(2)
    assert s["percentage_bias"] == pytest.approx(20)
    assert s["overprediction_units"] == 8
    assert s["underprediction_units"] == 2
    assert score([0,0],[1,1])["wape"] is None
    assert score([0,0],[1,1])["percentage_bias"] is None
    assert reduction(50,60) == -20
    assert reduction(0,0) is None
    with pytest.raises(ValueError):
        score([1],[np.nan])
    rows = [{"model":m,"product_id":p,"actual":a,"prediction":f} for m in ["hw_weekly","seasonal_naive"] for p,a,f in [("a",100,90),("b",1,0)]]
    overall,_ = summaries(pd.DataFrame(rows))
    assert overall.iloc[0].wape == pytest.approx(1100/101)
    assert overall.iloc[0].mean_product_wape == 55


def test_pairwise_wins_losses_ties_and_undefined():
    rows = []
    for model in ["hw_weekly","seasonal_naive","weekday_mean_4w","weekday_mean_8w"]:
        forecasts = [10,12,10,1] if model=="hw_weekly" else [12,10,10,0]
        for pid,actual,forecast in zip(["win","loss","tie","zero"],[10,10,10,0],forecasts):
            rows.append({"model":model,"product_id":pid,"actual":actual,"prediction":forecast})
    o,p = summaries(pd.DataFrame(rows))
    comparison,detail = comparisons(o,p)
    assert len(comparison)==3
    assert comparison.wins.eq(1).all() and comparison.losses.eq(1).all()
    assert comparison.ties.eq(1).all() and comparison.undefined.eq(1).all()
    assert len(detail)==12


def test_sql_calendar_denominators_and_complete_growth():
    calendar = pd.DataFrame({"date":pd.date_range("2010-01-01","2011-12-08")})
    calendar["month_start"] = calendar.date.dt.to_period("M").dt.to_timestamp()
    calendar["weekday_number"] = calendar.date.dt.dayofweek
    calendar["weekday"] = calendar.date.dt.day_name()
    calendar["complete_month"] = (calendar.month_start+pd.offsets.MonthEnd(0)).le(calendar.date.max())
    daily = calendar[["date"]].copy()
    daily["units"] = np.where(daily.date.dt.dayofweek==5,0,1)
    daily["positive_sales_gbp"] = np.where(daily.date.dt.year==2010,10.,20.)
    with duckdb.connect() as con:
        con.register("calendar",calendar)
        con.register("daily_totals",daily)
        weekday = con.execute((ROOT/"sql/weekday_seasonality.sql").read_text()).df()
        assert weekday.loc[weekday.weekday.eq("Saturday"),"average_daily_units"].iloc[0]==0
        assert weekday.covered_calendar_days.sum()==len(calendar)
        monthly = con.execute((ROOT/"sql/monthly_trends.sql").read_text()).df()
        assert pd.isna(monthly.iloc[-1].comparable_monthly_growth_pct)
        assert not monthly.iloc[-1].complete_month
        annual = con.execute((ROOT/"sql/comparable_growth.sql").read_text()).df()
        assert annual.iloc[-1].value_growth_pct==pytest.approx(100)


def test_transaction_value_is_aggregated_before_daily_totals():
    # Changing prices inside a day cannot be represented by units * a final price.
    lines = pd.DataFrame({"product_id":["a","a"],"date":[pd.Timestamp("2020-01-01")]*2,"units":[2,3],"unit_price":[10,20],"description":["Example"]*2})
    daily = aggregate_sales(lines)
    assert daily.positive_sales_gbp.iloc[0]==80
    assert daily.units.iloc[0]==5
    assert daily.transaction_lines.iloc[0]==2


@pytest.mark.skipif(not (OUT/"run_manifest.json").exists(),reason="Run pipeline first")
def test_saved_outputs_reconcile():
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
    with duckdb.connect(str(OUT/"sales_analytics.duckdb"),read_only=True) as con:
        assert {r[0] for r in con.execute("SHOW TABLES").fetchall()}=={"sales","product_metadata","calendar","daily_totals"}
    errors = pd.read_csv(OUT/"benchmark_analysis/product_error_analysis.csv")
    reconcile = json.loads((OUT/"benchmark_analysis/reconciliation.json").read_text())
    assert errors.error_reduction_units.sum()==pytest.approx(reconcile["net_absolute_error_reduction_units"])
    assert errors.share_of_model_absolute_error_pct.sum()==pytest.approx(100)
    assert errors.share_of_net_error_reduction_pct.sum()==pytest.approx(100)
