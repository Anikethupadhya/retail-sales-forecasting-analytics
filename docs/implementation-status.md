# Implementation status

Starting revision: d18fc1fe20c3ed6b766b515694886ca01c696286. Verified default branch: main; unchanged. Feature branch: feature/reproducible-training-windows. Initial tree clean; two prior commits. Private repository verified via GitHub API. Local checkpoint deliverables/pre-training-windows.bundle passed bundle verification.

| Milestone | Status | Evidence / decision |
| --- | --- | --- |
| Starting artifacts/runtime | Verified | 45 archive files; exact corrected WAPE 80.23984858319143%, reduction 28.864142802883528%; Python 3.14.3 |
| Starting clean reproduction | Verified | d18fc1f; starting-reproduction evidence; fresh clone/environment, no caches, 16 tests, dashboard smoke, 26 CSVs and aggregate Parquet reconciled |
| Committed reproduction/CI repair | Verified locally | c330d22; foundation-reproduction evidence; temporary DuckDB, mandatory integration/dashboard checks |
| Protocol before execution | Verified | c330d22855930481638a5339f8103e15b9cf5295; protocol SHA 58368645b26b573f1dfb22163d60d2722b877f2ec550c2a25ecf45a448613461 |
| Experiment implementation | Verified | 18 fixture tests; initial measured run recorded development dirty inputs honestly |
| Experiment and reconciliation | Verified | 20,160 predictions; 3,360 per method; expanding/baselines/statuses reconciled; no fallback |
| Dashboard and documentation | Verified | 38 tests pass; Edge/Playwright rendered checks and six visually inspected screenshots; same three tabs |
| Exact implementation final verification | Pending | Integration-ready commit must precede final unique clone run |
| Push/latest-head CI/draft PR | Pending | API auth works; main stays unchanged; no publication or merge |
| Review ZIP | Pending | Requires final clean evidence and unchanged implementation hashes |

Decisions: 182 calendar days, not 180; baselines computed once with 7/28/56-day histories; common preorigin expanding-history spike thresholds; all failures remain in primary support. No tuning after outcomes. Best smoothing 182-day WAPE 103.97687999441006%; expanding 104.51904083308533%; 365-day 107.65276528826755%; strongest baseline weekday_mean_4w 103.55868813422221%. The small pooled improvement wins only 2/6 periods and 9/20 products.

Old evidence and immutable artifacts are preserved. Evidence paths below outputs/verification/training-windows are new; source workspaces/environments/reference copies stay ignored under .verification-runs. No external blocker currently established.
