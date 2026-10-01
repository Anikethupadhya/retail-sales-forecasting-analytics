# Final handoff: portfolio presentation

The current implementation finishes presentation and report maintainability on the existing feature branch. [Draft PR #1](https://github.com/Anikethupadhya/retail-sales-forecasting-analytics/pull/1) remains the review route into main. The repository stays private and main stays at d18fc1fe20c3ed6b766b515694886ca01c696286. The earlier phase's handoff is preserved in Git at 8af778c and in the previous review ZIP; historical verification remains under outputs/verification/training-windows.

## What changed and what was reused

The existing Python/pandas pipeline, DuckDB SQL, benchmark, robustness and training-window results remain the calculation sources. No new forecasting experiment was added. Protected archives, protocols and established numerical results retain their starting hashes.

The main and secondary report writers now replace explicitly bounded sections, preserving maintained prose. Temporary-root regression tests prove stable repeated generation, no duplicate sections, malformed-boundary rejection and relevant-input updates. The README has 856 narrative words, a screenshot, three findings, scoped forecasting interpretation and distinct quick-demo/report/full-reproduction commands.

The authoritative findings artifact now records IDs, full precision, formulas, denominators, units, SQL/output fields, dates and limitations. Shared portfolio artifacts derive the headline and deterministic improvement, deterioration and spike examples. The dashboard preserves its three tabs, adds Start here and manifest-driven shortcuts, and distinguishes selected-product/period scores from pooled cohort results. Selectors load saved data without fitting. Interview, resume and walkthrough materials use the same evidence.

Verification and packaging now bind to current-phase evidence. The clean runner first proves a raw/database-free saved-output demonstration, then removes only the new checkout's generated copies, rebuilds from the checksum-verified official workbook, and reconciles results. The publication inspector scans tracked files, reachable Git blobs and nested ZIP entries. The package guard rejects changed implementation bytes or added implementation files.

## Three business findings

- Matched January-November 2011 positive-sales value increased 2.896081910134423% versus the same months in 2010; positive units changed by -5.998392093469389%.
- Product 22423, REGENCY CAKESTAND 3 TIER, led observed positive-sales value at GBP 330,757.09, or 1.6960448923506632% of the all-merchandise total.
- Thursday had the highest calendar-day average positive-sales value: GBP 37923.15811320754 across 106 covered days for that weekday, including zero-sales dates.

These findings concern cleaned positive merchandise sales across all countries, December 1, 2009 through December 8, 2011. The growth comparison uses complete matched months. Value is transaction-level Quantity multiplied by Price in GBP, with returns excluded; it is not net revenue, profit or a causal explanation. [Business finding evidence](business-findings.md) maps every calculation.

## Forecasting claim

Across six methods, 20 products and six retrospective 28-day periods, the four-week weekday-average method had pooled WAPE 103.55868813422221%, versus 110.41658145992102% for last-week repetition. Absolute errors were 227,884 and 242,975 units over the same 220,053 actual units. Relative reduction is 6.210927050108036%; WAPE is 6.857893325698811 percentage points lower. Concise wording: the four-week weekday-average baseline reduced pooled absolute error by approximately 6.2% versus last-week repetition.

WAPE is total absolute error divided by actual sales and can exceed 100%; it is not accuracy. Daily errors remain substantial. Later-2011 model-family selection and overlapping inspected evaluations make these retrospective comparisons. The original corrected 28.86% result belongs to a different single-period cohort, with duplicate repair after initial test inspection; it remains separate and its historical executions are preserved. Observed sales do not establish unconstrained demand, inventory availability, promotions or savings.

## Verification and exact revisions

Tested implementation: **121930eb8981b586762a9029290cb3d8daa60a7d**. Run: 20261001T062700Z-2e8ba9d2, 27045.81 seconds. Fresh clone and environment, pinned dependencies and pip check passed. Quick demo had no workbook, processed cache or database and checked three tabs plus all three walkthrough shortcuts. Full pipeline, 49 tests with zero failures/errors/skips, and separate dashboard smoke passed. Forty CSVs and customer-free Parquet reconciled; portfolio JSON claims and walkthrough reconciled; seven maintained documents survived regeneration; all 50 protected hashes remained exact. All 89 starting protected/numerical artifact hashes are unchanged in the delivery checkout.

Nine Edge/Playwright screenshots were rendered and visually inspected with zero page errors. [Current verification summary](../outputs/verification/portfolio/final-summary.json), [clean reproduction](../outputs/verification/portfolio/final-reproduction/reproduction.json), [browser evidence](../outputs/verification/portfolio/browser.json) and [implementation equivalence](../outputs/verification/portfolio/implementation-equivalence.json) describe distinct scopes. The earlier run failures are preserved: managed Git ownership and inaccessible shared pytest temporary folders. Repairs use command-scoped Git trust and a fresh run-local test directory; no global trust, ACL or assertion change was made.

Later evidence commits change only documentation, screenshots, evidence and verified execution metadata. They are not a new implementation. Final-head CI is independently inspected after pushing; its SHA and external snapshots are included as review-evidence/portfolio-final-github.json and portfolio-final-pr.json inside the ZIP and in the delivery message. Compare the complete implementation path set against the tested revision; packaging repeats that checksum guard.

## Meaningful commits

- d0ac555: maintained report ownership and authoritative portfolio claims.
- 56f75aa: manifest-driven dashboard, regression checks, browser and current packaging/verification guards.
- 69a52db: command-scoped managed-repository clone repair.
- 121930e: unique test temporary directory and preserved failure evidence.
- A final evidence/handoff commit follows the successful exact-commit run; its actual SHA is recorded in final external GitHub/package evidence.

All development times are real. Prior training-window commits remain in history; there is no rewrite, force-push or manufactured activity.

## Commands

From a clone on feature/reproducible-training-windows, use Python 3.14.3:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```

The quick demo uses committed real outputs. Report-only refresh, full analysis and independent clean reproduction are separate:

```powershell
.\.venv\Scripts\python -m src.report
.\.venv\Scripts\python -m src.pipeline
.\.venv\Scripts\python scripts/verify_reproduction.py --revision HEAD
```

[Setup and reproduction](setup-and-reproduction.md) explains cloning, branch selection, installation and checks. The ZIP deliberately excludes Git internals; use a clone to execute the protocol-history checks.

## Resume bullets

- Audited 1,067,371 UCI transaction rows and built a Python/pandas and DuckDB pipeline covering 4,706 products, with SQL sales analysis and a three-tab Streamlit/Plotly dashboard.
- Compared 6 sales forecasting methods across 20 products and 6 retrospective 28-day periods; the four-week weekday-average baseline reduced pooled absolute error by 6.2% versus last-week repetition.

[Resume evidence](resume-evidence.md) provides the engineering alternative and artifact/field mappings. [Interview guide](interview-guide.md) includes short and two-minute explanations, technical answers and the reproducible demonstration.

## Review package and human decisions

The allowlisted ZIP is deliverables/retail-sales-forecasting-analytics-review.zip, with tested implementation, packaging revision, entry/source/protocol checksums and current evidence. deliverables/package-verification.json records final size, SHA-256, entry count, CRC, exclusions and protected-hash checks. The previous ZIP/manifest remain in deliverables/pre-portfolio-review. Current publication scan evidence is outputs/verification/portfolio/publication.json; targeted inspection is not an exhaustive guarantee.

Inspect the README, all three dashboard examples, numerical scopes, retrospective limitations, resume wording and PR diff. [Review and merge instructions](review-and-merge.md) explain checking final CI/conflicts, marking the draft ready, using an available merge commit to preserve development commits, and updating/verifying local main after your decision. The PR remains draft until you mark it ready. No merge, deployment, visibility, licensing or repository-setting change was performed. Choosing a code license and public visibility are separate owner decisions; the dataset attribution is retained.
