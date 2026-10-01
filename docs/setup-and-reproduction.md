# Setup, CI and full reproduction

Run full analysis from a Git clone with its commit history; the review ZIP is an inspection copy and deliberately excludes .git. The experiment validates its previously committed protocol before real-data execution.

While the draft is unmerged, a new GitHub clone starts on main. Switch to the reviewed feature branch to use this implementation:

```powershell
git clone https://github.com/Anikethupadhya/retail-sales-forecasting-analytics.git
cd retail-sales-forecasting-analytics
git switch feature/reproducible-training-windows
```

Use Python 3.14.3, the runtime recorded in the measured manifests. All Python dependencies remain pinned in requirements.txt; no broad upgrade was introduced.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip check
```

Full analysis, including audit, transaction-level GBP aggregation, DuckDB SQL, historical benchmark reconciliation, six-origin robustness, the committed training-window experiment and measured reports:

```powershell
.\.venv\Scripts\python -m src.pipeline
```

Launch the saved-output dashboard:

```powershell
.\.venv\Scripts\python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```

Open http://localhost:8501. No selector fits models. A cloned repository includes customer-free aggregates and saved forecasts, so it can display the dashboard without the raw workbook or DuckDB binary. Missing results display rebuild instructions.

Routine checks, requiring neither workbook nor existing database:

```powershell
.\.venv\Scripts\python -m pytest -q -m 'not integration and not dashboard'
.\.venv\Scripts\python -m pytest -q -m integration
.\.venv\Scripts\python -m pytest -q -m dashboard
```

Fixture checks use invented deterministic test inputs only. Integration checks reconcile real saved outputs and explicitly rebuild a temporary DuckDB from committed customer-free aggregates. Dashboard checks load saved results and forbid forecast fitting. All are mandatory in .github/workflows/checks.yml on push and pull_request, using Python 3.14.3 and a 15-minute timeout. Fast CI does not rerun the raw-data analysis. [GitHub Python workflow documentation](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) describes the action setup.

Full clean reproduction is a separate local command:

```powershell
.\.venv\Scripts\python scripts/verify_reproduction.py --revision HEAD
```

Each call creates .verification-runs/<UTC-and-UUID> containing an isolated clone of the exact commit, a new environment, independent reference outputs and an evidence directory. Existing runs are preserved. The runner removes only the new clone's copied generated outputs, retains immutable historical archives and protocols, starts with no processed cache, installs pinned requirements, checks dependencies, rebuilds from raw data, runs all tests and a separate dashboard smoke check. No previously built database is copied.

The existing official workbook is explicitly copied only after its recorded SHA-256 is verified. If absent, the pipeline obtains the official UCI workbook and verifies the checksum afterward. Use --raw-workbook PATH or --runs-dir PATH to choose alternatives. A failed run retains its command logs and failure manifest. Compare stable keys rather than CSV order: forecasts/metrics rtol=1e-10, atol=1e-8; GBP atol=1e-6; identifiers, dates, schemas, coverage and statuses exact. Protected hashes are exact. Runtime, source commit metadata and Plotly chart IDs are not numerical outcomes.

Evidence records the clean initial checkout, tested revision, commands, exit statuses, runtime/package versions, source/input/protocol checksums and reconciliation. Deliberate deletion/regeneration of tracked output copies is expected; implementation inputs must stay unchanged. Evidence belongs outside the tested checkout. A later evidence/report commit is not a claim that a different implementation was tested: compare src, sql, tests, scripts, app.py, config.json, requirements.txt, protocols, workflow and dependency files between tested implementation and final head. Any implementation change requires affected verification again.

Optional rendered browser checks require Node.js, the development-only Playwright 1.62.1 dependency declared in package.json, and a browser. With Node/npm installed:

```powershell
npm install
npx playwright install chromium
$env:DASHBOARD_URL='http://localhost:8501'
npm run dashboard:check
```

Alternatively use an installed Edge browser with $env:PLAYWRIGHT_CHANNEL='msedge'. [Playwright browser documentation](https://playwright.dev/docs/browsers) describes branded channels. SCREENSHOT_DIR and BROWSER_EVIDENCE can select run-specific evidence paths. The current Windows inspection used local Edge and Playwright 1.62.1 from the bundled Node runtime. Browser packages are optional development dependencies, not forecasting or routine CI dependencies.

After final verification, python scripts/package_review.py creates the allowlisted deliverables/retail-sales-forecasting-analytics-review.zip. Its manifest records per-entry SHA-256 and package integrity/exclusions. Raw data, customer-level extracts, environments, caches, .git and database binaries remain excluded.
