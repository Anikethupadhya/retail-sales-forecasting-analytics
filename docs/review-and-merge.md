# Review and merge

The project remains private. [Draft PR #1](https://github.com/Anikethupadhya/retail-sales-forecasting-analytics/pull/1) compares `feature/reproducible-training-windows` against `main`. No merge, deployment, visibility, licensing or repository-setting change is authorized in this phase.

Repository inspection on October 1, 2026 confirmed merge commits, squash merges and rebase merges are enabled. A merge commit is therefore available at the repository setting level; still confirm the PR's current checks and merge conditions before using it. The observed settings are saved in `outputs/verification/portfolio/repository-options.json`.

## What to inspect

Read the README's question, findings and forecasting interpretation. Follow the three [walkthrough examples](dashboard-walkthrough.md), comparing actual units with four-week and last-week forecasts. Check that product/period scores are distinct from the six-period pooled claim. Review [business finding denominators](business-findings.md), [resume evidence](resume-evidence.md), and the specific retrospective limitations.

Report ownership is described in [report-ownership.md](report-ownership.md). The quick dashboard path uses saved real aggregates and forecasts; full clean reproduction independently rebuilds from the checksum-verified workbook. Current-phase checks and exact revisions are recorded in `outputs/verification/portfolio/` and the final handoff. Older evidence proves the earlier implementation only. Final-head CI is checked after the evidence commit is pushed; its snapshot is also included in the review package.

## Manual steps after review

1. Open the draft PR, inspect Files changed, and confirm latest-head required checks succeeded. Check for conflicts and outstanding review requirements; a GitHub mergeability flag alone does not prove readiness.
2. Mark the draft **Ready for review** when you are satisfied.
3. If the repository offers **Create a merge commit**, choose that option to preserve the individual feature commits in main's history. Check the actual option before proceeding; no settings will be changed automatically. Other strategies require a deliberate choice.
4. Merge only after your explicit decision. Changing visibility is a separate action.
5. Update a clean local main after the GitHub merge:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git log -1 --oneline
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```

If local changes or divergent main prevent a fast-forward, preserve them and resolve the divergence; do not reset or force-push. Verify the merged version's GitHub checks and dashboard. A full exact-commit reproduction of the merge can be run with `python scripts/verify_reproduction.py --revision HEAD` if needed; do not describe premerge evidence as an execution of the merge commit.

## Publication readiness

Publication inspection uses `scripts/check_publication.py` on actual tracked files, reachable Git blobs, and nested ZIP entries, including CSV/Parquet schemas. It reports sanitized locations and inspection limits. Mere presence of an ignored local workbook is not evidence that raw data was committed. The targeted scan is not an exhaustive security guarantee.

The dataset's CC BY 4.0 attribution remains. The repository currently has no explicit code license; choosing one is a separate owner decision and does not inherit automatically from the dataset license. Resolve any scan findings before public sharing. Repository visibility and licensing remain unchanged.

## Current implementation verification

Tested implementation `121930eb8981b586762a9029290cb3d8daa60a7d` passed full clean reproduction: 49 tests, no failures/errors/skips, saved-output quick demo before raw acquisition, full rebuild, 40 CSVs plus Parquet/portfolio JSON reconciliation and exact historical hashes. Rendered Edge inspection covers nine screenshots with zero page errors. The final branch head adds evidence and documentation only; its complete implementation input set must match this revision. Latest-head push/PR checks, mergeability and head SHA are captured after the final push in the review ZIP under `review-evidence/portfolio-final-github.json` and `portfolio-final-pr.json`. The PR is intentionally draft; confirm those live checks and conflicts before marking it ready.
