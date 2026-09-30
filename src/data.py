"""Official source acquisition, row-level audit and leakage-safe product selection."""
import hashlib
import urllib.request
import zipfile

import numpy as np
import pandas as pd

from .common import ROOT, OUT, save_json


def acquire(cfg):
    path = ROOT / cfg["workbook"]
    if path.exists():
        return path
    # Accept the original workbook if the user placed it in another raw subfolder.
    matches = list((ROOT / "data/raw").rglob("online_retail_II.xlsx"))
    if matches:
        return matches[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    archive = path.parent / "online_retail_ii.zip"
    try:
        with urllib.request.urlopen(cfg["download_url"], timeout=120) as response:
            archive.write_bytes(response.read())
        with zipfile.ZipFile(archive) as zipped:
            member = next(n for n in zipped.namelist() if n.endswith("online_retail_II.xlsx"))
            path.write_bytes(zipped.read(member))
    except Exception as exc:
        raise RuntimeError(
            f"Official download failed: {exc}. Visit {cfg['source_url']}, click Download, "
            f"extract online_retail_II.xlsx from the ZIP into {path.parent}, then rerun. "
            "No substitute dataset is used."
        ) from exc
    return path


def cross_sheet_replicas(raw):
    """Exact cross-sheet match, preserving each sheet's repeated-line count."""
    raw_fields = [c for c in raw.columns if c not in {"source_sheet", "excel_row"}]
    occurrence = raw.groupby(raw_fields + ["source_sheet"], dropna=False, sort=False).cumcount()
    return raw.assign(_occurrence=occurrence).duplicated(
        subset=raw_fields + ["_occurrence"], keep="first")


def aggregate_sales(valid):
    """Compute line values before customer-free product/date aggregation."""
    lines = valid.assign(positive_sales_gbp=valid.units * valid.unit_price)
    return lines.groupby(["product_id", "date"], sort=True).agg(
        units=("units", "sum"), positive_sales_gbp=("positive_sales_gbp", "sum"),
        transaction_lines=("units", "size"), description=("description", "last")).reset_index()


def prepare_sales(cfg):
    path = acquire(cfg)
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    cache_dir = ROOT / "data/processed"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / f"workbook_{checksum}.parquet"
    info_path = cache_dir / f"workbook_{checksum}.json"
    if cache.exists() and info_path.exists():
        import json
        raw = pd.read_parquet(cache)
        sheet_info = json.loads(info_path.read_text())
    else:
        sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
        sheet_info = []
        frames = []
        expected = {"Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"}
        for name, frame in sheets.items():
            if set(frame.columns) != expected:
                raise ValueError(f"Unexpected columns in {name}: {list(frame.columns)}")
            sheet_info.append({"sheet": name, "raw_rows": len(frame), "columns": list(frame.columns),
                               "date_min": str(frame.InvoiceDate.min()), "date_max": str(frame.InvoiceDate.max())})
            frame["source_sheet"] = name
            frame["excel_row"] = np.arange(len(frame)) + 2
            frames.append(frame)
        raw = pd.concat(frames, ignore_index=True)
        for col in ["Invoice", "StockCode", "Description", "Country"]:
            raw[col] = raw[col].astype("string")
        raw.to_parquet(cache, index=False)
        save_json(info_path, sheet_info)
    dates = pd.to_datetime(raw.InvoiceDate, errors="coerce")
    quantity = pd.to_numeric(raw.Quantity, errors="coerce")
    price = pd.to_numeric(raw.Price, errors="coerce")
    code = raw.StockCode.astype("string").str.strip().str.upper()
    invoice = raw.Invoice.astype("string").str.strip()
    # Sheets overlap in time. Match full raw rows AND their within-sheet
    # occurrence number, keeping repeated invoice lines inside each sheet.
    cross_sheet_replica = cross_sheet_replicas(raw)
    flags = {
        "invalid_date": dates.isna(),
        "missing_product_or_invoice": code.isna() | code.eq("") | invoice.isna() | invoice.eq(""),
        "cross_sheet_replica": cross_sheet_replica,
        "cancellation_invoice": invoice.str.upper().str.startswith("C", na=False),
        "negative_quantity": quantity.lt(0),
        "zero_or_invalid_quantity": quantity.isna() | quantity.eq(0),
        "non_product_code": ~code.str.fullmatch(r"\d{5}[A-Z]{0,2}", na=False),
        "nonpositive_or_invalid_price": price.isna() | price.le(0),
        "final_incomplete_day": dates.dt.normalize().eq(dates.max().normalize()),
    }
    if not cfg["exclude_final_calendar_day"]:
        raise ValueError("This version prespecifies exclusion of the last calendar day")
    # Priority counts are mutually exclusive; flag counts deliberately overlap.
    reason = pd.Series("retained", index=raw.index)
    priority_counts = {}
    for name, flag in flags.items():
        removed = reason.eq("retained") & flag.fillna(False)
        priority_counts[name] = int(removed.sum())
        reason.loc[removed] = name
    valid = pd.DataFrame({"product_id": code, "date": dates.dt.normalize(), "units": quantity,
                          "unit_price": price,
                          "description": raw.Description})[reason.eq("retained")].copy()
    start = dates.min().normalize()
    end = dates.max().normalize() - pd.Timedelta(days=1)
    daily = aggregate_sales(valid)
    metadata = valid.sort_values("date").dropna(subset=["description"]).groupby("product_id").description.last().reset_index()
    metadata = pd.DataFrame({"product_id": sorted(valid.product_id.unique())}).merge(metadata, how="left")
    metadata["description"] = metadata.description.fillna("Description unavailable")
    calendar = pd.DataFrame({"date": pd.date_range(start, end)})
    calendar["month_start"] = calendar.date.dt.to_period("M").dt.to_timestamp()
    calendar["weekday_number"] = calendar.date.dt.dayofweek
    calendar["weekday"] = calendar.date.dt.day_name()
    calendar["complete_month"] = calendar.month_start.ge(start) & (calendar.month_start + pd.offsets.MonthEnd(0)).le(end)
    out = OUT / "sales"
    out.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(out / "product_daily_sales.parquet", index=False)
    metadata.to_csv(out / "product_metadata.csv", index=False)
    calendar.to_csv(out / "calendar.csv", index=False)
    raw_duplicates = int(raw.drop(columns=["source_sheet", "excel_row"]).duplicated().sum())
    audit = {
        "source": "Chen, D. (2012). Online Retail II. UCI Machine Learning Repository. DOI:10.24432/C5CG6D. CC BY 4.0.",
        "source_url": cfg["source_url"], "raw_file": str(path.relative_to(ROOT)), "sha256": checksum,
        "raw_rows": len(raw), "sheets": sheet_info, "raw_date_min": str(dates.min()), "raw_date_max": str(dates.max()),
        "overlapping_flag_counts": {k: int(v.sum()) for k, v in flags.items()},
        "exclusive_exclusion_counts_in_priority_order": priority_counts, "retained_rows": len(valid),
        "exact_duplicate_rows_beyond_first": raw_duplicates, "duplicate_rows_removed": int(cross_sheet_replica.sum()),
        "within_sheet_repeated_rows_retained": raw_duplicates - int(cross_sheet_replica.sum()),
        "duplicate_policy": "Workbook sheets overlap on 2010-12-01 through 2010-12-09. Remove only identical full-row cross-sheet replicas, matched by within-sheet occurrence number. Retain repeated invoice lines within a sheet; no unique line identifier justifies deleting them. Matching multiplicities preserve the maximum count found in any sheet.",
        "missing_customer_id_rows": int(raw["Customer ID"].isna().sum()),
        "retained_missing_customer_id_rows": int((reason.eq("retained") & raw["Customer ID"].isna()).sum()),
        "missing_description_rows": int(raw.Description.isna().sum()),
        "non_product_codes": raw.loc[flags["non_product_code"], "StockCode"].value_counts().to_dict(),
        "last_calendar_day_policy": "Exclude the entire latest day because the export may end mid-trading-day; no completeness claim for other dates.",
        "last_timestamp": str(dates.max()), "daily_grid_start": str(start.date()), "daily_grid_end": str(end.date()),
        "zero_sales_assumption": "Absent product-date rows become zero observed positive sales, including closures and dates before first sale. Missing transactions and stock-outs cannot be distinguished from genuine zeros.",
        "scope": "All countries pooled, positive-quantity merchandise with positive price. Returns are separate, not netted. Five digits optionally followed by up to two letters define merchandise codes; unconventional genuine codes may be excluded.",
        "positive_sales_gbp": float((valid.units * valid.unit_price).sum()),
        "positive_units": float(valid.units.sum()), "product_count": len(metadata),
        "sales_value_definition": "Transaction-level Quantity * Price summed before aggregation. GBP positive-sales value; not net revenue or profit.",
        "customer_free_aggregate_columns": list(daily.columns),
    }
    save_json(out / "data_audit.json", audit)
    return daily, metadata, calendar, audit
