"""Cohort and date rules from the immutable retrospective protocol."""
import pandas as pd


def select_cohort(sales, start, cutoff, rules):
    start, cutoff = pd.Timestamp(start), pd.Timestamp(cutoff)
    initial_days = (cutoff - start).days
    if initial_days < rules["min_initial_days"]:
        raise ValueError("Insufficient initial history")
    pre = sales[sales.date.lt(cutoff)]
    eligibility = pre.groupby("product_id").agg(first_sale=("date", "min"), last_sale=("date", "max"),
                                                initial_units=("units", "sum"), active_days=("date", "nunique"))
    recent = pre[pre.date.ge(cutoff - pd.Timedelta(days=rules["recent_days"]))].groupby("product_id").date.nunique()
    eligibility["recent_active_days"] = recent.reindex(eligibility.index, fill_value=0)
    eligibility["active_day_fraction"] = eligibility.active_days / initial_days
    eligibility["recent_active_day_fraction"] = eligibility.recent_active_days / rules["recent_days"]
    eligibility["eligible"] = (
        eligibility.first_sale.le(start + pd.Timedelta(days=rules["max_first_sale_offset_days"])) &
        eligibility.active_day_fraction.ge(rules["min_active_day_fraction"]) &
        eligibility.recent_active_day_fraction.ge(rules["min_recent_active_day_fraction"]))
    ranked = eligibility[eligibility.eligible].reset_index().sort_values(["initial_units", "product_id"], ascending=[False, True])
    selected = ranked.head(rules["product_count"]).product_id.tolist()
    if not selected:
        raise ValueError("No eligible products; thresholds remain fixed")
    eligibility["selected"] = eligibility.index.isin(selected)
    metadata = ranked.head(rules["product_count"]).copy()
    descriptions = pre.sort_values("date").dropna(subset=["description"]).groupby("product_id").description.last()
    metadata["description"] = metadata.product_id.map(descriptions).fillna("Description unavailable")
    return selected, eligibility.reset_index(), metadata


def daily_grid(sales, products, start, end):
    grid = pd.MultiIndex.from_product([products, pd.date_range(start, end)], names=["product_id", "date"])
    return sales[sales.product_id.isin(products)].groupby(["product_id", "date"]).units.sum().reindex(grid, fill_value=0).reset_index()


def make_robustness_splits(protocol, start, end):
    splits = []
    for date in protocol["forecast_start_dates"]:
        forecast_start = pd.Timestamp(date)
        forecast_end = forecast_start + pd.Timedelta(days=protocol["horizon_days"] - 1)
        if forecast_end > pd.Timestamp(end):
            raise ValueError("Forecast horizon exceeds observed coverage")
        splits.append({"split": date, "stage": "robustness", "train_start": str(pd.Timestamp(start).date()),
                       "train_end": str((forecast_start - pd.Timedelta(days=1)).date()),
                       "forecast_start": date, "forecast_end": str(forecast_end.date()),
                       "training_days": (forecast_start - pd.Timestamp(start)).days,
                       "horizon_days": protocol["horizon_days"]})
    return splits
