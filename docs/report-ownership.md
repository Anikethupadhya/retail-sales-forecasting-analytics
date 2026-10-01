# Report ownership and regeneration

Prose outside `<!-- generated:NAME:start -->` / `<!-- generated:NAME:end -->` is maintained content. Reporting replaces only the matching bounded section. Each key must occur once; duplicate, incomplete or reversed boundaries are errors rather than permission to erase a document.

The maintained README owns its introduction, method explanation, setup commands, limitations and navigation. `src.portfolio` owns its headline, sales-findings and forecast-results sections. It also owns bounded sections in business findings, walkthrough, resume evidence and interview guidance. `src.report` owns corrected benchmark error analysis and deterministic HTML figures. `src.training_report` owns the training-window report and its error-analysis summary; it never rewrites the README or appends duplicate sections.

The canonical command is:

```powershell
.\.venv\Scripts\python -m src.report
```

It reads existing customer-free SQL outputs, audit metadata and saved predictions. It does not read the workbook, create DuckDB, or fit forecasts. `src.findings` is the shared interpreter of authoritative SQL results for both pipeline and reporting. Numbers are retained at full precision in JSON, then rounded for display. `outputs/portfolio/summary.json` records the relative reduction and claim sources; `walkthrough_examples.json` records post-inspection illustrative selections.

The full `python -m src.pipeline` calls the same reporting path after the existing analyses. The secondary `python -m src.training_report` replaces only its own sections and is safe to repeat. Generated Markdown/JSON and HTML div IDs have no run timestamps; runtime provenance lives in verification/experiment manifests separately.

Regression checks use temporary roots and saved-input copies. They seed maintained prose, render twice, compare deterministic outputs, change a relevant saved input, and check that the owned section changes while maintained content remains. They forbid calls into fitting and raw-data preparation.
