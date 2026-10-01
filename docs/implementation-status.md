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
| Dashboard and documentation | Verified | 39 tests pass; Edge/Playwright rendered checks and six visually inspected screenshots; same three tabs |
| Exact implementation final verification | Verified | 45d64ba; final-reproduction manifest: clean checkout, 39 tests, 40 CSVs plus Parquet reconciled, exact protected hashes |
| Push / CI / draft PR | Verified implementation; final evidence head checked at handoff | Implementation push CI passed; draft PR #1 verified open/draft into main. Final-head status is recorded in deliverables/final-github-verification.json after the evidence commit is pushed. |
| Review ZIP | Verified at handoff | Allowlisted package with source-hash guard, ZIP CRC/entry/exclusion checks and exact protected hashes; deliverables/package-verification.json records the final package |

Decisions: 182 calendar days, not 180; baselines computed once with 7/28/56-day histories; common preorigin expanding-history spike thresholds; all failures remain in primary support. No tuning after outcomes. Best smoothing 182-day WAPE 103.97687999441006%; expanding 104.51904083308533%; 365-day 107.65276528826755%; strongest baseline weekday_mean_4w 103.55868813422221%. The small pooled improvement wins only 2/6 periods and 9/20 products.

Old evidence and immutable artifacts are preserved. Evidence paths below outputs/verification/training-windows are new; source workspaces/environments/reference copies stay ignored under .verification-runs. No external blocker currently established.

CI repair: d56f8e8 Linux integration failed because immutable archive manifest keys contain Windows backslashes. Preserve the original manifest and resolve its keys portably using PureWindowsPath. A deterministic regression checks unchanged hashes and rejects altered bytes. This requires a new final implementation revision and fresh full verification.

Final clean run: 20261001T013753Z-96cc59ac, implementation 45d64ba3fcc24494308aef5812ac6cf216ce6dc9, 925.6 seconds. Commands all exit zero. Final execution metadata replaces the initial development manifest after source/input hash checks; numerical results are unchanged. Only evidence/report/provenance files change after the tested implementation. No blockers remain for local implementation; final external check outcomes are captured before handoff.

## Portfolio presentation phase

Starting revision: 8af778c01ba8a2bda40625db62bfe05629a8a8f6. Local/remote heads matched after fetch; PR #1 open/draft into unchanged main; private visibility verified. Baseline hashes and previous review package preserved. Earlier verification remains evidence of the earlier phase.

| Requirement | Existing implementation | Actual gap | Necessary change | Verification |
| --- | --- | --- | --- | --- |
| Report ownership | Main writer replaces README; secondary appends | Maintained prose is overwritten / direct repeats duplicate sections | Bounded sections and temporary-root regression | Four regression cases passed |
| Findings | Three correct SQL findings | Limited formula/denominator metadata | Extend authoritative artifact and shared interpreter | SQL/claim integration passed |
| README/interview/resume | Technical narrative and smoothing-focused bullet | Recruiter explanation and winning-method claim | Maintained README and generated evidence | Links/claims passed; 856 narrative words |
| Dashboard/walkthrough | Three tabs and saved controls | Start guidance and reproducible illustrative examples | Shared manifest and selector shortcuts | Five dashboard tests passed; nine development screenshots inspected |
| Quick demonstration | Saved-output application | Fresh-checkout proof before raw-data rebuild | Raw/database-free smoke evidence | Passed before raw data was copied; three tabs and shortcuts |
| Exact verification/package | Prior-phase guards and evidence | Bind to this phase | New run evidence and current provenance | Exact reproduction passed; package guard verified at final handoff |
| Push/PR/review | Existing pushed branch and draft PR | Updated final review | Real commits, latest-head checks, merge instructions | Implementation pushed; final-head CI/PR snapshot included in final package |

Development verification: 47 tests passed after screenshot capture; two further package-guard cases passed. The initial link check correctly failed before the three new screenshots existed, then passed after capture. Protected/result hash comparison found no changes. Development checks are distinct from the final exact-commit reproduction below.

Clean verification initially failed before analysis because the managed source .git owner differs from the verifier user. A command-scoped safe.directory entry for this exact source .git successfully cloned it; no global Git trust or ACL change was made. Failed-run evidence is preserved under outputs/verification/portfolio/failed-clone-run. A new exact-revision run follows this repair.

The next clean run passed installation, dependency checks, the raw/database-free quick demonstration and the full raw pipeline. Its test phase had 39 passes and 10 setup errors because the shared Windows pytest temporary root was inaccessible. Evidence is preserved under outputs/verification/portfolio/failed-temp-run. The verifier now uses a new test temporary directory inside its unique run root, outside published evidence; no user-wide temporary permissions or test assertions were changed. A fresh exact-commit run verifies the repair.

Final current-phase run: 20261001T062700Z-2e8ba9d2, tested implementation 121930eb8981b586762a9029290cb3d8daa60a7d, 27045.81 seconds. Fresh-checkout quick demonstration, complete raw rebuild, 49 tests (zero failures/errors/skips), separate dashboard smoke, 40 CSVs, customer-free Parquet, portfolio JSON, seven maintained documents and exact protected hashes passed. Nine rendered screenshots were visually inspected with no page errors. The complete delivery source map matches the tested revision. Final CI/PR/publication/package outcomes are independently checked at handoff and included in the ZIP. Older failures remain preserved and are not presented as successful verification.
