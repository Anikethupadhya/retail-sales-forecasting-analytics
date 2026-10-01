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
            results[name] = con.execute((ROOT / f"sql/{name}.sql").read_text(encoding="utf-8")).df()
            results[name].to_csv(out / f"{name}.csv", index=False)
    from .findings import build_findings
    audit = {"positive_sales_gbp": float(totals.positive_sales_gbp.sum())}
    save_json(out / "findings.json", build_findings(results, audit))
    return results
