"""Interpret authoritative SQL outputs; shared by analysis and report-only paths."""
import json
import pandas as pd
from .common import OUT, save_json


def build_findings(results, audit):
    growth = results["comparable_growth"].dropna(subset=["value_growth_pct"]).sort_values("year").iloc[-1]
    leader = results["product_rankings"].sort_values(["value_rank", "product_id"]).iloc[0]
    weekday = results["weekday_seasonality"].sort_values(["average_daily_sales_gbp", "weekday_number"], ascending=[False, True]).iloc[0]
    scope = "All cleaned merchandise; 2009-12-01 through 2011-12-08; all countries"
    common = {"population": "All cleaned positive merchandise sales; all countries",
              "date_range": {"start": "2009-12-01", "end": "2011-12-08"},
              "display": {"GBP_decimals": 2, "percentage_decimals": 2, "count_decimals": 0},
              "value_basis": "Transaction-level Quantity × Price, summed before aggregation; returns excluded"}
    definitions = [
        dict(id="matched_growth", text=f"January–November {int(growth.year)} positive-sales value changed by {growth.value_growth_pct:+.2f}% versus the same months in {int(growth.previous_year)}; units changed by {growth.units_growth_pct:+.2f}%.",
             source="outputs/sales/comparable_growth.csv", row=f"year={int(growth.year)}", value=float(growth.value_growth_pct),
             values={k: float(growth[k]) for k in ["positive_sales_gbp", "previous_value", "positive_units", "previous_units", "value_growth_pct", "units_growth_pct"]},
             formula="100 × (current / previous − 1), calculated separately for value and units",
             units={"positive_sales_gbp": "GBP", "positive_units": "units", "growth": "%"},
             numerator={"value": "positive_sales_gbp − previous_value", "units": "positive_units − previous_units"},
             denominator={"value": "previous_value", "units": "previous_units"},
             comparison_periods={"current": f"{int(growth.year)}-01-01 through {int(growth.year)}-11-30", "previous": f"{int(growth.previous_year)}-01-01 through {int(growth.previous_year)}-11-30"},
             sql="sql/comparable_growth.sql", limitations="Matched complete January–November periods; value and unit changes do not establish price, mix, or causal explanations."),
        dict(id="value_leader", text=f"{leader.product_id} ({leader.description}) led positive-sales value at £{leader.positive_sales_gbp:,.2f}, accounting for {leader.value_share_pct:.2f}% of the all-merchandise total.",
             source="outputs/sales/product_rankings.csv", row=f"product_id={leader.product_id}", value=float(leader.positive_sales_gbp),
             values={"positive_sales_gbp": float(leader.positive_sales_gbp), "all_merchandise_positive_sales_gbp": float(audit["positive_sales_gbp"]), "value_share_pct": float(leader.value_share_pct)},
             product_id=str(leader.product_id), description=str(leader.description), formula="sum(transaction Quantity × Price); share = 100 × product value / all-merchandise value",
             units={"positive_sales_gbp": "GBP", "value_share_pct": "%"}, numerator="Product positive_sales_gbp", denominator="All-merchandise positive_sales_gbp",
             sql="sql/product_rankings.sql", limitations="Ranking is by observed positive-sales value across the extract, not profit, net revenue, or customer preference."),
        dict(id="weekday_pattern", text=f"{weekday.weekday} had the highest average daily positive-sales value: £{weekday.average_daily_sales_gbp:,.2f} over {int(weekday.covered_calendar_days)} covered calendar days, including zero-sales dates.",
             source="outputs/sales/weekday_seasonality.csv", row=f"weekday={weekday.weekday}", value=float(weekday.average_daily_sales_gbp),
             values={"positive_sales_gbp": float(weekday.positive_sales_gbp), "covered_calendar_days": int(weekday.covered_calendar_days), "average_daily_sales_gbp": float(weekday.average_daily_sales_gbp)},
             weekday=str(weekday.weekday), formula="weekday positive_sales_gbp / covered_calendar_days, including zero-sale dates",
             units={"positive_sales_gbp": "GBP", "covered_calendar_days": "days", "average_daily_sales_gbp": "GBP/calendar day"}, numerator="weekday positive_sales_gbp", denominator="covered_calendar_days",
             sql="sql/weekday_seasonality.sql", limitations="Covered calendar days include zeros; zero observations cannot distinguish closure, missing records, or stock-outs.")]
    for finding in definitions:
        finding.update(common)
        finding["source_fields"] = list(finding["values"])
        if finding["id"] == "value_leader":
            finding["source_fields"].remove("all_merchandise_positive_sales_gbp")
            finding["denominator_source"] = "outputs/sales/data_audit.json:positive_sales_gbp"
    return {"schema_version": 2, "scope": scope, "findings": definitions}


def refresh(outputs=OUT):
    results = {name: pd.read_csv(outputs/"sales"/f"{name}.csv", dtype={"product_id": str})
               for name in ["comparable_growth", "product_rankings", "weekday_seasonality"]}
    audit = json.loads((outputs/"sales/data_audit.json").read_text(encoding="utf-8"))
    document = build_findings(results, audit)
    save_json(outputs/"sales/findings.json", document)
    return document
