"""Fixed-origin forecasts with validation-only global model selection."""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


def seasonal_naive(y, horizon):
    if len(y) < 7:
        raise ValueError("Seasonal naive requires seven days")
    return np.resize(np.asarray(y, dtype=float)[-7:], horizon)


def predict(y, model, horizon):
    if model == "seasonal_naive":
        return seasonal_naive(y, horizon), [], False
    if model in {"weekday_mean_4w", "weekday_mean_8w"}:
        weeks = 4 if model == "weekday_mean_4w" else 8
        if len(y) < weeks * 7:
            raise ValueError("Insufficient baseline history")
        weekday_means = np.asarray(y, dtype=float)[-weeks * 7:].reshape(weeks, 7).mean(axis=0)
        return np.resize(weekday_means, horizon), [], False
    if model != "hw_weekly":
        raise ValueError(f"Unknown model: {model}")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fit = ExponentialSmoothing(np.asarray(y), trend=None, damped_trend=False, seasonal="add",
                                   seasonal_periods=7, initialization_method="estimated").fit(optimized=True, use_brute=False)
        values = np.asarray(fit.forecast(horizon), dtype=float)
        messages = [f"{w.category.__name__}: {w.message}" for w in caught]
        converged = getattr(fit, "mle_retvals", None)
        failed_convergence = converged is not None and not converged.get("success", True)
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite forecast")
    return values, messages, bool(failed_convergence)


def evaluate(daily, splits, models, cfg):
    rows, events = [], []
    for split in splits:
        print(f"Forecasting {split['split']} through {split['forecast_end']}", flush=True)
        for pid, series in daily.groupby("product_id", sort=True):
            series = series.sort_values("date").set_index("date").units
            origin = pd.Timestamp(split["train_end"])
            history = series.loc[:origin].to_numpy(dtype=float)
            future_dates = pd.date_range(split["forecast_start"], periods=cfg["horizon_days"])
            actual = series.reindex(future_dates).to_numpy()
            if np.isnan(actual).any():
                raise ValueError("Missing evaluation observations")
            for model in models:
                status = "ok"
                try:
                    values, messages, nonconverged = predict(history, model, cfg["horizon_days"])
                    if nonconverged:
                        status = "nonconverged_baseline_fallback"
                        values = seasonal_naive(history, cfg["horizon_days"])
                    negative_count = int((values < 0).sum())
                    if cfg["clip_forecasts_at_zero"]:
                        values = np.maximum(values, 0)
                    if messages or nonconverged or negative_count:
                        events.append({"split": split["split"], "product_id": pid, "model": model,
                                       "status": status, "warnings": messages, "negative_predictions_clipped": negative_count})
                except Exception as exc:
                    if model != "hw_weekly":
                        raise
                    status = "failure_baseline_fallback"
                    values = seasonal_naive(history, cfg["horizon_days"])
                    events.append({"split": split["split"], "product_id": pid, "model": model,
                                   "status": status, "error": str(exc)})
                for step, (date, observed, forecast) in enumerate(zip(future_dates, actual, values), 1):
                    rows.append({"stage": split["stage"], "split": split["split"], "product_id": pid,
                                 "model": model, "origin": origin, "train_last_date": origin, "date": date,
                                 "forecast_start": split["forecast_start"], "forecast_end": split["forecast_end"],
                                 "horizon_day": step, "actual": float(observed), "prediction": float(forecast), "status": status})
    return pd.DataFrame(rows), events
