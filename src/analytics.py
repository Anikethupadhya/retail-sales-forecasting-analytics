"""All-merchandise SQL outputs, calendar-aware scope, and measured findings."""
import duckdb
import pandas as pd

from .common import ROOT, OUT, save_json


def build_sales_database(sales, metadata, calendar, *, database_path=None, output_dir=None):
    out = output_dir if output_dir is not None else OUT / "sales"
    out.mkdir(parents=True, exist_ok=True)
    totals = calendar[["date"]].merge(sales.groupby("date")[["units", "positive_sales_gbp", "transaction_lines"]].sum(), on="date", how="left").fillna(0)
    totals.to_csv(out / "daily_totals.csv", index=False)
    results = {}
    with duckdb.connect(str(database_path if database_path is not None else OUT / "sales_analytics.duckdb")) as con:
        for name, frame in [("sales", sales.drop(columns="description")), ("product_metadata", metadata), ("calendar", calendar), ("daily_totals", totals)]:
            con.register("input_frame", frame)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM input_frame")
            con.unregister("input_frame")
        # No historical scenario tables survive in the active database.
        for name in ["inventory_assumptions", "forecasts", "daily_sales"]:
            con.execute(f"DROP TABLE IF EXISTS {name}")
        for name in ["product_rankings", "monthly_trends", "weekday_seasonality", "comparable_growth"]:
            results[name] = con.execute((ROOT / f"sql/{name}.sql").read_text()).df()
            results[name].to_csv(out / f"{name}.csv", index=False)
    growth = results["comparable_growth"].iloc[-1]
    leader = results["product_rankings"].sort_values(["value_rank", "product_id"]).iloc[0]
    weekday = results["weekday_seasonality"].sort_values("average_daily_sales_gbp", ascending=False).iloc[0]
    findings = [
        {"id": "matched_growth", "text": f"January–November {int(growth.year)} positive-sales value changed by {growth.value_growth_pct:+.2f}% versus the same months in {int(growth.previous_year)}; units changed by {growth.units_growth_pct:+.2f}%.",
         "source": "outputs/sales/comparable_growth.csv", "row": f"year={int(growth.year)}", "value": float(growth.value_growth_pct)},
        {"id": "value_leader", "text": f"{leader.product_id} ({leader.description}) led positive-sales value at £{leader.positive_sales_gbp:,.2f}, accounting for {leader.value_share_pct:.2f}% of the all-merchandise total.",
         "source": "outputs/sales/product_rankings.csv", "row": f"product_id={leader.product_id}", "value": float(leader.positive_sales_gbp)},
        {"id": "weekday_pattern", "text": f"{weekday.weekday} had the highest average daily positive-sales value: £{weekday.average_daily_sales_gbp:,.2f} over {int(weekday.covered_calendar_days)} covered calendar days, including zero-sales dates.",
         "source": "outputs/sales/weekday_seasonality.csv", "row": f"weekday={weekday.weekday}", "value": float(weekday.average_daily_sales_gbp)}]
    save_json(out / "findings.json", {"scope": "All cleaned merchandise; 2009-12-01 through 2011-12-08; all countries", "findings": findings})
    return results
