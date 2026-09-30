# Original dataset

Source: Chen, D. (2012), *Online Retail II*, UCI Machine Learning Repository,
[DOI:10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D), CC BY 4.0.

The pipeline first looks for `data/raw/online_retail_II.xlsx`. If missing, it downloads
the official [ZIP](https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip).
No alternate or generated sales dataset is used.

If the download fails:

1. Open [the UCI dataset page](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
2. Click **Download (43.5 MB)**.
3. Open the downloaded ZIP and extract **online_retail_II.xlsx**.
4. Place the workbook in **data/raw/** in this repository, keeping that filename.
5. Run `python -m src.pipeline` again.

The first run inspects every sheet and its actual column names. Later runs reuse a
local Parquet read cache keyed by the raw workbook's SHA-256. Both the workbook and
cache are excluded from Git. `outputs/data_audit.json` records sheet coverage,
actual row counts, exclusions and checksum. `outputs/run_manifest.json` records the
environment and config checksum. The audit does not rely on the source's advertised
row count. A malformed schema fails rather than silently renaming unexpected fields.
