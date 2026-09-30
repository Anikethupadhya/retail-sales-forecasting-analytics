import numpy as np
import pandas as pd


def score(actual, prediction):
    actual, prediction = np.asarray(actual, dtype=float), np.asarray(prediction, dtype=float)
    if actual.shape != prediction.shape or not np.isfinite(actual).all() or not np.isfinite(prediction).all():
        raise ValueError("Metrics require aligned finite values")
    error = np.abs(actual - prediction)
    denominator = np.abs(actual).sum()
    signed = prediction - actual
    return {"mae": float(error.mean()), "wape": float(100 * error.sum() / denominator) if denominator else None,
            "signed_bias": float(signed.mean()), "percentage_bias": float(100 * signed.sum() / denominator) if denominator else None,
            "overprediction_units": float(np.maximum(signed, 0).sum()), "underprediction_units": float(np.maximum(-signed, 0).sum()),
            "absolute_error_sum": float(error.sum()), "actual_units": float(denominator), "observations": len(actual)}


def reduction(baseline, candidate):
    return 100 * (baseline - candidate) / baseline if pd.notna(baseline) and baseline > 0 and pd.notna(candidate) else None


def summaries(predictions):
    overall, products = [], []
    for model, group in predictions.groupby("model", sort=True):
        overall.append({"model": model, **score(group.actual, group.prediction)})
        for pid, part in group.groupby("product_id"):
            products.append({"model": model, "product_id": pid, **score(part.actual, part.prediction)})
    products = pd.DataFrame(products)
    overall = pd.DataFrame(overall)
    for i, row in overall.iterrows():
        part = products[products.model.eq(row.model)]
        overall.loc[i, "mean_product_wape"] = part.wape.mean()
    return overall, products


def comparisons(overall, products, candidate="hw_weekly", baselines=None, tolerance=1e-9):
    """Explicit pairwise baseline rows; never hard-code one comparator."""
    if baselines is None:
        baselines = [m for m in overall.model if m != candidate]
    model = products[products.model.eq(candidate)].set_index("product_id")
    selected = overall.set_index("model").loc[candidate]
    results, detail = [], []
    for baseline in baselines:
        base = products[products.model.eq(baseline)].set_index("product_id")
        joined = model.join(base, lsuffix="_model", rsuffix="_baseline", validate="one_to_one")
        if len(joined) != len(base) or joined.actual_units_baseline.isna().any():
            raise ValueError("Comparisons require identical product populations")
        counts = {k: 0 for k in ["win", "loss", "tie", "undefined"]}
        for pid, row in joined.iterrows():
            difference = row.absolute_error_sum_baseline - row.absolute_error_sum_model
            outcome = "undefined" if row.actual_units_model == 0 else ("tie" if abs(difference) <= tolerance else ("win" if difference > 0 else "loss"))
            counts[outcome] += 1
            detail.append({"baseline": baseline, "product_id": pid, "outcome": outcome,
                           "model_wape": row.wape_model, "baseline_wape": row.wape_baseline,
                           "error_reduction_units": difference,
                           "relative_wape_reduction_pct": reduction(row.wape_baseline, row.wape_model)})
        base_overall = overall.set_index("model").loc[baseline]
        comparable = counts["win"] + counts["loss"] + counts["tie"]
        results.append({"model": candidate, "baseline": baseline, "model_wape": selected.wape,
                        "baseline_wape": base_overall.wape, "relative_wape_reduction_pct": reduction(base_overall.wape, selected.wape),
                        "error_reduction_units": base_overall.absolute_error_sum - selected.absolute_error_sum,
                        "wins": counts["win"], "losses": counts["loss"], "ties": counts["tie"], "undefined": counts["undefined"],
                        "comparable_products": comparable, "win_pct": 100 * counts["win"] / comparable if comparable else None})
    return pd.DataFrame(results), pd.DataFrame(detail)
