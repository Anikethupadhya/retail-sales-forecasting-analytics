# Final handoff

[Draft PR #1](https://github.com/Anikethupadhya/retail-sales-forecasting-analytics/pull/1): verified open and draft, from feature/reproducible-training-windows into main. Feature branch: feature/reproducible-training-windows. Repository stays private; main stays at d18fc1fe20c3ed6b766b515694886ca01c696286. No merge, deployment, visibility change, force-push or history rewrite was performed.

## Completed implementation

Repeatable exact-commit reproduction uses a new clone, environment, reference copy and external evidence directory for every run. Raw-data checksums are verified and copied outputs/caches/databases are not reused. CI runs fixture/unit, saved-output integration and dashboard checks without the workbook or a pre-existing DuckDB. Temporary databases are explicitly rebuilt from committed customer-free aggregates. Protected Windows archive keys now work on Linux without changing archive/manifest bytes.

The experiment protocol was committed at c330d22855930481638a5339f8103e15b9cf5295, before real execution. Its SHA-256 is 58368645b26b573f1dfb22163d60d2722b877f2ec550c2a25ecf45a448613461. The same 20 pre-January-2011 products and six origins have 28 consecutive forecasts, giving 3,360 rows per method and 20,160 total. Baselines retain 7/28/56-day histories. Shared preorigin expanding spike labels, fit boundaries, warnings, failure/fallback statuses and clipping counts are saved. Expanding forecasts and baselines reconcile against the existing robustness implementation.

All three dashboard tabs remain; Forecast Evaluation adds inspectable saved training histories and named baselines. Model Performance includes pooled/period comparisons, wins/losses and expanded diagnostics. Reports, setup instructions, interview guidance and resume claim mappings are updated. Six rendered screenshots were visually inspected; Edge/Playwright reported no page errors.

## Measured results

| Experiment/method | Pooled WAPE (%) |
| --- | --- |
| Original corrected smoothing benchmark | 80.23984858319143 |
| Original corrected last-week baseline | 112.79803427524311 |
| Robustness / expanding smoothing | 104.51904083308533 |
| Training-window 182-day smoothing | 103.97687999441006 |
| Training-window 365-day smoothing | 107.65276528826755 |
| Shared last-week baseline | 110.41658145992102 |
| Shared 4-week weekday mean | 103.55868813422221 |
| Shared 8-week weekday mean | 104.90609080539689 |

Original corrected relative reduction is 28.864142802883528%, with the repair after initial test inspection disclosed and both historical executions preserved. The 182-day history reduces expanding WAPE relatively by 0.5187196843310986%, but improves only 2/6 periods and 9/20 combined-product comparisons. The 4-week weekday baseline remains best. All real fits succeeded; none required fallback. Common spikes number 31/3,360 product-days; they remain in primary scores.

These are retrospective comparisons: the model family was selected using later-2011 validation and some periods overlap inspected evaluations. No independent holdout, statistical significance, promotion/inventory cause or financial saving is claimed. The original cohort differs from the robustness/window cohort. Observed sales proxy demand; missing inventory/lost-sales information remains a limitation. Positive-sales value is transaction-level GBP Quantity×Price, not net revenue or profit.

## Verification and revisions

Tested implementation: 45d64ba3fcc24494308aef5812ac6cf216ce6dc9. Linux CI passed for this revision. Final full raw-data clean reproduction passed: fresh checkout/environment, empty cache, checksum-verified workbook, pipeline, 39 tests (zero failures/errors/skips), separate dashboard smoke, 40 CSVs and customer-free Parquet reconciled, protected checksums exact. Evidence is in outputs/verification/training-windows/final-reproduction/ and final-summary.json. Evidence-only commits may follow; implementation-input hashes must match the tested revision. Final branch-head CI must be inspected separately.

Historical starting d18fc1f and repaired-foundation c330d22 both passed fresh-clone reproduction, tests, smoke checks and numeric reconciliation. The initial development experiment correctly recorded dirty implementation inputs. Superseded runs remain local; they are not claimed as final verification.

Meaningful milestones: a99d700 reproduction/CI foundation; c330d22 frozen protocol; 4169350 fixture-tested windows/leakage/failures; 9ae9ec1 dashboard/browser/package integration; d56f8e8 measured outcomes/reporting; 45d64ba Linux archive-path repair. Commit times are real; no activity or timeline was manufactured.

## Commands

From the Git checkout after installing requirements.txt in Python 3.14.3:

```powershell
.\.venv\Scripts\python -m src.pipeline
.\.venv\Scripts\python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
.\.venv\Scripts\python scripts/verify_reproduction.py --revision HEAD
```

Full details: setup-and-reproduction.md. Saved outputs permit dashboard loading without raw workbook/database. The review ZIP excludes .git; clone the repository to validate protocol history and execute the full analysis.

## Resume bullets

- Evaluated six 28-day sales forecasting methods across six retrospective periods and 20 products using Python, pandas and statsmodels; the best smoothing history achieved 104.0% pooled WAPE versus 104.5% with expanding history.
- Audited 1,067,371 UCI transaction rows and built DuckDB SQL sales rankings, comparable-period growth and weekday analysis with a three-tab Streamlit/Plotly dashboard and evidence-backed error analysis.

Every number maps to saved fields in resume-evidence.md. These bullets do not claim smoothing beat the strongest baseline.

## Human review

Review the draft PR, experiment protocol and retrospective limitations; inspect the dashboard and reports; choose final resume wording. Then decide whether to mark the draft ready and merge. Publishing the repository or hosting the dashboard remains a separate choice. No human approval is needed to complete the authorized push/draft-PR workflow.

Verified review package: deliverables/retail-sales-forecasting-analytics-review.zip. Entry hashes, final ZIP hash/size, CRC integrity and exclusion results are stored in deliverables/review-manifest.json and package-verification.json. The previous review copy remains preserved in deliverables/pre-training-windows-review/.

The final evidence-only head is reported in the delivery message and draft PR body; git diff 45d64ba..HEAD over src, sql, tests, scripts, protocols, app.py, config.json, requirements.txt, pytest.ini, package.json and .github must be empty. Latest-head push/PR checks are inspected after that evidence commit; their final snapshot is saved in deliverables/final-github-verification.json.
