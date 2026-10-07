# Verification

The project has three distinct verification paths. Each proves a different property.

## Routine checks

Fixture tests exercise data preparation, training boundaries, failure handling, metric calculations and report regeneration. Saved-output integration checks reconcile the committed real results and construct a temporary DuckDB database from customer-free aggregates. Dashboard checks load the saved results and reject attempts to fit models during selection.

The GitHub Actions workflow runs all three groups on pushes and pull requests using Python 3.14.3 and the pinned requirements. These checks require neither the raw workbook nor an existing local database.

```powershell
.\.venv\Scripts\python -m pytest -q
```

Report regression checks run in temporary project/output directories. They preserve maintained prose, verify repeated generation is deterministic, and change a relevant saved input to check that its generated section updates. Malformed section boundaries fail without erasing the document.

## Saved-output demonstration

`scripts/verify_quick_demo.py` checks a checkout without the raw workbook, processed cache or DuckDB database. It opens all three dashboard tabs and applies the improvement, deterioration and spike examples while forbidding data preparation, fitting and database creation. It demonstrates that committed real outputs are sufficient to use the app; it does not prove raw-data reproduction.

## Full raw-data reproduction

```powershell
.\.venv\Scripts\python scripts/verify_reproduction.py --revision HEAD
```

This creates an isolated checkout of the selected commit, a fresh environment, independent reference outputs and a new temporary directory. It verifies the saved-output demonstration first, removes only the fresh checkout's generated output copies, and rebuilds from the checksum-verified official workbook. It then runs the tests and dashboard smoke check, compares numerical artifacts, checks maintained prose and verifies protected hashes.

Forecast and metric comparisons use relative tolerance `1e-10` and absolute tolerance `1e-8`; GBP aggregates use absolute tolerance `1e-6`. Identifiers, dates, schemas, counts and statuses are exact. Historical archive and protocol hashes must match byte-for-byte. Runtime durations and chart identifiers are recorded separately from numerical results.

## Recorded execution

The complete raw-data execution of implementation `121930eb8981b586762a9029290cb3d8daa60a7d` passed 49 tests, a separate dashboard smoke check, 40 CSV comparisons, customer-free Parquet and derived JSON reconciliation. Its [manifest and command outcomes](../outputs/verification/portfolio/final-reproduction/reproduction.json) identify that exact implementation. [Rendered browser evidence](../outputs/verification/portfolio/browser.json) records nine screenshots and zero page errors.

Those manifests remain historical evidence of their named revision. The public documentation cleanup changes reporting destinations and navigation; its current tests and saved-output checkout checks are separate evidence under `outputs/verification/publication/`. The raw-data preparation, SQL, forecasting configuration, protocols and saved numerical results are unchanged.

Publication inspection covers tracked files, reachable Git blobs and nested ZIP entries for targeted credential patterns and customer/invoice schemas. Its stated limits apply; a clean scan is not an exhaustive security guarantee. [Setup and reproduction](setup-and-reproduction.md) explains dependencies and commands.
