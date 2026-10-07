"""Portfolio claims and illustrative walkthroughs derived only from saved outputs."""
import json
import math
import pandas as pd
from .common import ROOT, OUT, save_json
from .documents import update_section
from .findings import refresh

METHODS = {"hw_expanding": "Expanding-history smoothing", "hw_182d": "182-day smoothing",
           "hw_365d": "365-day smoothing", "seasonal_naive": "Last-week repetition",
           "weekday_mean_4w": "Four-week weekday average", "weekday_mean_8w": "Eight-week weekday average"}
CANDIDATE, COMPARATOR = "weekday_mean_4w", "seasonal_naive"


def read(outputs, name):
    return pd.read_csv(outputs/name, dtype={"product_id": str}, float_precision="round_trip")


def build_summary(outputs=OUT):
    metrics = read(outputs, "training_windows_v1/overall_metrics.csv").set_index("model")
    predictions = read(outputs, "training_windows_v1/predictions.csv")
    protocol = json.loads((outputs/"robustness/split_manifest.json").read_text(encoding="utf-8"))
    audit = json.loads((outputs/"sales/data_audit.json").read_text(encoding="utf-8"))
    keys = ["product_id", "forecast_start", "date"]
    reference = None
    for _, part in predictions.groupby("model", sort=True):
        if part.duplicated(keys).any():
            raise ValueError("Duplicate forecasting support")
        actual = part.sort_values(keys)[keys+["actual"]].reset_index(drop=True)
        if reference is None:
            reference = actual
        else:
            pd.testing.assert_frame_equal(actual, reference)
    candidate, comparator = metrics.loc[CANDIDATE], metrics.loc[COMPARATOR]
    denominator = float(comparator.absolute_error_sum)
    reduction = 100*(denominator-float(candidate.absolute_error_sum))/denominator if denominator else None
    wape_reduction = 100*(comparator.wape-candidate.wape)/comparator.wape if comparator.wape else None
    if reduction is not None and not math.isclose(reduction, wape_reduction, abs_tol=1e-10):
        raise ValueError("Absolute-error and WAPE reductions disagree")
    winner = metrics.sort_values(["wape"], kind="stable").index[0]
    return {"schema_version": 1, "experiment": "training_windows_v1", "best_method": winner,
            "candidate": CANDIDATE, "comparator": COMPARATOR,
            "candidate_wape": float(candidate.wape), "comparator_wape": float(comparator.wape),
            "candidate_absolute_error_units": float(candidate.absolute_error_sum),
            "comparator_absolute_error_units": denominator,
            "actual_units_per_method": float(candidate.actual_units),
            "relative_error_reduction_pct": reduction,
            "wape_difference_percentage_points": float(comparator.wape-candidate.wape),
            "methods": len(metrics), "products": len(protocol["selected_product_ids"]),
            "periods": len(protocol["splits"]), "horizon_days": int(predictions.groupby(["model","product_id","forecast_start"]).size().iloc[0]),
            "prediction_rows": len(predictions), "raw_rows": int(audit["raw_rows"]),
            "retained_lines": int(audit["retained_rows"]), "all_merchandise_products": int(audit["product_count"]),
            "formula": "100 × (comparator absolute_error_sum − candidate absolute_error_sum) / comparator absolute_error_sum",
            "sources": {"metrics": "outputs/training_windows_v1/overall_metrics.csv", "support": "outputs/training_windows_v1/predictions.csv",
                        "cohort": "outputs/robustness/split_manifest.json", "audit": "outputs/sales/data_audit.json"},
            "scope": "20 pre-January-2011 products; six retrospective 28-day periods; identical observations; observed positive units",
            "limitations": "Lowest pooled error among tested methods only. Later-2011 family selection and overlapping inspected evaluations; no independent holdout or significance claim. WAPE remains substantial."}


def build_walkthrough(outputs=OUT):
    p = read(outputs, "training_windows_v1/predictions.csv")
    metadata = read(outputs, "robustness/product_metadata.csv").set_index("product_id")
    keys = ["product_id", "forecast_start", "date"]
    candidate = p[p.model.eq(CANDIDATE)][keys+["actual","prediction"]]
    comparator = p[p.model.eq(COMPARATOR)][keys+["actual","prediction"]]
    paired = candidate.merge(comparator, on=keys, suffixes=("_candidate","_comparator"), validate="one_to_one")
    if len(paired) != len(candidate) or len(candidate) != len(comparator) or not paired.actual_candidate.equals(paired.actual_comparator):
        raise ValueError("Walkthrough methods have different actual support")
    paired["candidate_error"] = (paired.prediction_candidate-paired.actual_candidate).abs()
    paired["comparator_error"] = (paired.prediction_comparator-paired.actual_comparator).abs()
    product = paired.groupby("product_id", as_index=False).agg(actual_units=("actual_candidate","sum"), candidate_error=("candidate_error","sum"), comparator_error=("comparator_error","sum"))
    product["error_reduction_units"] = product.comparator_error-product.candidate_error
    examples = []
    for kind, ascending, condition in [("improvement", False, product.error_reduction_units.gt(0)), ("deterioration", True, product.error_reduction_units.lt(0))]:
        eligible = product[condition & product.actual_units.gt(0)]
        if eligible.empty:
            continue
        row = eligible.sort_values(["error_reduction_units","product_id"], ascending=[ascending,True]).iloc[0]
        periods = paired[paired.product_id.eq(row.product_id)].groupby("forecast_start",as_index=False)[["candidate_error","comparator_error"]].sum()
        periods["change"] = periods.comparator_error-periods.candidate_error
        period = periods.sort_values(["change","forecast_start"], ascending=[ascending,True]).iloc[0]
        record = {"id": kind, "selection_rule": f"{'Greatest' if not ascending else 'Most negative'} six-period absolute-error reduction; product-ID ascending tie-break. Display period uses the same extremum, then earliest start.",
                  "product_id": str(row.product_id), "forecast_start": str(period.forecast_start),
                  "actual_units_six_periods": float(row.actual_units), "candidate_error_six_periods": float(row.candidate_error),
                  "comparator_error_six_periods": float(row.comparator_error), "error_reduction_units": float(row.error_reduction_units),
                  "candidate_wape_six_periods": float(100*row.candidate_error/row.actual_units), "comparator_wape_six_periods": float(100*row.comparator_error/row.actual_units),
                  "period_error_reduction_units": float(period.change),
                  "interpretation": "A product-specific example; the selected chart period is distinct from the six-period product score."}
        examples.append(record)
    spikes = p[p.model.eq("hw_expanding") & p.is_spike].copy()
    spikes["excess"] = spikes.actual-spikes.spike_threshold
    if not spikes.empty:
        spike = spikes.sort_values(["excess","product_id","date"],ascending=[False,True,True]).iloc[0]
        examples.append({"id":"spike", "selection_rule":"Largest actual-minus-existing shared threshold; product-ID then date ascending ties.",
                         "product_id":str(spike.product_id), "forecast_start":str(spike.forecast_start), "date":str(spike.date),
                         "actual_units":float(spike.actual), "spike_threshold":float(spike.spike_threshold), "excess_units":float(spike.excess),
                         "interpretation":"Large observed sales against a strictly preorigin 99th-percentile threshold; cause is unknown and the observation remains in primary scores."})
    for e in examples:
        e.update(experiment="training_windows_v1", candidate=CANDIDATE, comparator=COMPARATOR,
                 description=str(metadata.loc[e["product_id"],"description"]),
                 sources={"predictions":"outputs/training_windows_v1/predictions.csv", "fields":keys+["model","actual","prediction","spike_threshold","is_spike"], "description":"outputs/robustness/product_metadata.csv"},
                 selectors={"Evaluation experiment":"Training-window experiment", "Forecast start":e["forecast_start"], "Product":e["product_id"], "Smoothing histories":[], "Baseline comparisons":[CANDIDATE,COMPARATOR]})
    return {"schema_version":1, "selection_context":"Illustrations selected after inspecting saved results; not validation or evidence of representative performance.",
            "missing_example_types":sorted({"improvement","deterioration","spike"}-{e["id"] for e in examples}), "examples":examples}


def generate(*, root=ROOT, outputs=OUT):
    findings = refresh(outputs)
    summary, walkthrough = build_summary(outputs), build_walkthrough(outputs)
    save_json(outputs/"portfolio/summary.json", summary)
    save_json(outputs/"portfolio/walkthrough_examples.json", walkthrough)
    reduction = summary["relative_error_reduction_pct"]
    result = (f"The **four-week weekday-average baseline** had the lowest pooled error among the tested methods: **{summary['candidate_wape']:.2f}% WAPE**, "
              f"versus **{summary['comparator_wape']:.2f}%** for last-week repetition. This is **{reduction:.1f}% relative reduction in pooled absolute error** "
              f"({summary['wape_difference_percentage_points']:.2f} percentage points), across **{summary['products']} products and {summary['periods']} retrospective {summary['horizon_days']}-day periods**. The remaining error is substantial.")
    update_section(root/"README.md", "headline", result)
    update_section(root/"README.md", "sales-findings", "\n".join(f"- {f['text']}" for f in findings["findings"])+"\n\n[Calculations, denominators, and SQL](docs/business-findings.md).")
    metrics = read(outputs,"training_windows_v1/overall_metrics.csv").sort_values(["wape","model"])
    table = "| Method | Pooled WAPE (%) |\n| --- | ---: |\n"+"\n".join(f"| {METHODS[r.model]} | {r.wape:.2f} |" for r in metrics.itertuples())
    update_section(root/"README.md", "forecast-results", table+f"\n\n{result}\n\n[Detailed experiment and mixed smoothing outcomes](docs/training-window-experiment.md).")
    business = []
    for f in findings["findings"]:
        values = "\n".join(f"| {key} | {value!r} |" for key,value in f["values"].items())
        business.append(f"## {f['id'].replace('_',' ').title()}\n\n{f['text']}\n\nPopulation: {f['population']}; {f['date_range']['start']} through {f['date_range']['end']}.\n\nCalculation: {f['formula']}. Numerator: {f['numerator']}; denominator: {f['denominator']}.\n\nFull-precision inputs/results:\n\n| Field | Value |\n| --- | ---: |\n{values}\n\nUnits: {f['units']}. Display: {f['display']}. Comparison periods: {f.get('comparison_periods','entire analysed extract')}.\n\n[SQL](../{f['sql']}); [output](../{f['source']}), row `{f['row']}`, fields `{', '.join(f['source_fields'])}`.\n\nLimitation: {f['limitations']}")
    update_section(root/"docs/business-findings.md", "business-findings", "\n\n".join(business), title="Business findings")
    examples_text = []
    for e in walkthrough["examples"]:
        calculation = (f"Six-period absolute errors: {e['candidate_error_six_periods']:,.2f} units for the four-week mean versus {e['comparator_error_six_periods']:,.2f} for last-week repetition; reduction {e['error_reduction_units']:+,.2f} units. The displayed period reduction is {e['period_error_reduction_units']:+,.2f} units."
                       if e["id"]!="spike" else f"On {e['date']}, actual sales were {e['actual_units']:,.0f} units against a {e['spike_threshold']:,.2f}-unit historical threshold (excess {e['excess_units']:,.2f}).")
        examples_text.append(f"## {e['id'].title()}: {e['product_id']} — {e['description']}\n\nSelection: {e['selection_rule']}\n\nIn Forecast Evaluation choose **Walkthrough example → {e['id'].title()}**. This applies experiment Training-window experiment, start {e['forecast_start']}, product {e['product_id']}, no smoothing curves, and four-week/last-week baselines. Manual controls remain available.\n\n{calculation}\n\n{e['interpretation']}\n\nSource: [saved predictions](../outputs/training_windows_v1/predictions.csv), matching product/start/model/date keys; fields actual, prediction, spike_threshold and is_spike. Screenshot: [selected view](screenshots/walkthrough-{e['id']}.png).")
    update_section(root/"docs/dashboard-walkthrough.md", "walkthrough", walkthrough["selection_context"]+"\n\n"+"\n\n".join(examples_text)+"\n\n[Machine-readable selection evidence](../outputs/portfolio/walkthrough_examples.json).", title="Dashboard walkthrough")
    evidence = f"""## Data and evaluation scope

The audit contains {summary['raw_rows']:,} source transaction rows and {summary['all_merchandise_products']:,} cleaned merchandise products. The forecasting comparison is a separate cohort: {summary['methods']} methods, {summary['products']} products, and {summary['periods']} retrospective {summary['horizon_days']}-day periods.

## Result sources

| Measurement | Artifact and field/calculation |
| --- | --- |
| Source rows and merchandise products | [Data audit](../outputs/sales/data_audit.json): raw_rows, product_count |
| Methods, products, periods and horizon | [Evaluation summary](../outputs/portfolio/summary.json): methods, products, periods, horizon_days |
| {reduction:.1f}% relative error reduction | [Overall metrics](../outputs/training_windows_v1/overall_metrics.csv): weekday_mean_4w and seasonal_naive absolute_error_sum; 100 × (comparator − candidate) / comparator |
| {summary['candidate_wape']:.2f}% versus {summary['comparator_wape']:.2f}% WAPE | Same metric rows: wape; identical pooled observations |
| {summary['wape_difference_percentage_points']:.6f} percentage points | Comparator WAPE − candidate WAPE; distinct from relative reduction |
| Three sales findings | [Finding definitions](../outputs/sales/findings.json): values, source, row, source_fields, sql, numerator, denominator |

Full-precision relative reduction: {reduction!r}%. The four-week weekday-average baseline is compared with last-week repetition. WAPE is total absolute error divided by actual units; it is not accuracy.

## Interpretation

The original corrected 28.86% result belongs to a different single-period cohort and followed duplicate repair after initial test inspection. Later-2011 model-family selection and overlapping inspected evaluations make the six-period comparison retrospective, rather than an untouched holdout. Positive-sales value excludes returns and is not net revenue or profit. These results do not establish operational savings or statistical significance.
"""
    update_section(root/"docs/result-evidence.md", "result-evidence", evidence, title="Result evidence")
    return summary, walkthrough
