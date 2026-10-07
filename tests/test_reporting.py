import hashlib
import json
from pathlib import Path
import re
import shutil

import numpy as np
import pandas as pd
import pytest

from src.common import ROOT, OUT
from src.documents import update_section
from src.report import generate
from src.training_report import generate as generate_training
from src.portfolio import build_summary, build_walkthrough


def test_reports_preserve_prose_repeat_and_update_changed_input(tmp_path, monkeypatch):
    import src.data
    import src.forecast
    import src.analytics
    def forbidden(*args, **kwargs):
        raise AssertionError("Report-only path must not prepare raw data, fit forecasts or create databases")
    monkeypatch.setattr(src.data, "prepare_sales", forbidden)
    monkeypatch.setattr(src.forecast, "predict", forbidden)
    monkeypatch.setattr(src.analytics, "build_sales_database", forbidden)
    outputs = tmp_path/"outputs"
    shutil.copytree(OUT, outputs, ignore=shutil.ignore_patterns("verification", "*.duckdb*"))
    root = tmp_path/"project"
    root.mkdir()
    sentinel = "My maintained introduction and setup instructions must survive."
    (root/"README.md").write_text(f"# Maintained README\n\n{sentinel}\n",encoding="utf-8")
    (root/"docs").mkdir()
    (root/"docs/error-analysis.md").write_text(sentinel+"\n",encoding="utf-8")
    generate(root=root, outputs=outputs)
    snapshot = {p.relative_to(root):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}
    generate(root=root, outputs=outputs)
    generate_training(root=root, outputs=outputs)
    generate_training(root=root, outputs=outputs)
    assert snapshot == {p.relative_to(root):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}
    for name in ["README.md","docs/error-analysis.md"]:
        assert sentinel in (root/name).read_text(encoding="utf-8")
    readme = (root/"README.md").read_text(encoding="utf-8")
    for key in ["headline","sales-findings","forecast-results"]:
        assert readme.count(f"generated:{key}:start") == readme.count(f"generated:{key}:end") == 1
    assert (root/"docs/result-evidence.md").exists()
    assert not (root/"docs/resume-evidence.md").exists()
    assert not (root/"docs/interview-guide.md").exists()
    rankings = pd.read_csv(outputs/"sales/product_rankings.csv",dtype={"product_id":str})
    leader = rankings.sort_values(["value_rank","product_id"]).index[0]
    rankings.loc[leader,"positive_sales_gbp"] += 1234
    rankings.loc[leader,"value_share_pct"] = 100*rankings.loc[leader,"positive_sales_gbp"]/json.loads((outputs/"sales/data_audit.json").read_text())["positive_sales_gbp"]
    rankings.to_csv(outputs/"sales/product_rankings.csv",index=False)
    generate(root=root, outputs=outputs)
    changed = (root/"README.md").read_text(encoding="utf-8")
    assert changed != readme and sentinel in changed
    assert f"£{rankings.loc[leader,'positive_sales_gbp']:,.2f}" in changed
    assert changed.count("generated:sales-findings:start") == 1


@pytest.mark.parametrize("body", ["<!-- generated:x:start -->", "<!-- generated:x:end -->\n<!-- generated:x:start -->", "<!-- generated:x:start --><!-- generated:x:end -->"*2])
def test_malformed_owned_sections_fail_without_erasing_prose(tmp_path, body):
    path = tmp_path/"readme.md"
    initial = "Maintained prose\n"+body
    path.write_text(initial,encoding="utf-8")
    with pytest.raises(ValueError):
        update_section(path,"x","replacement")
    assert path.read_text(encoding="utf-8") == initial


@pytest.mark.integration
def test_findings_and_headline_match_authoritative_fields():
    findings = json.loads((OUT/"sales/findings.json").read_text(encoding="utf-8"))
    assert findings["schema_version"] == 2 and len(findings["findings"]) == 3
    for f in findings["findings"]:
        assert (ROOT/f["sql"]).exists()
        assert f["numerator"] and f["denominator"] and f["limitations"] and f["display"]
    by = {f["id"]:f for f in findings["findings"]}
    growth = by["matched_growth"]["values"]
    assert growth["value_growth_pct"] == pytest.approx(100*(growth["positive_sales_gbp"]/growth["previous_value"]-1))
    assert growth["units_growth_pct"] == pytest.approx(100*(growth["positive_units"]/growth["previous_units"]-1))
    leader = by["value_leader"]["values"]
    assert leader["value_share_pct"] == pytest.approx(100*leader["positive_sales_gbp"]/leader["all_merchandise_positive_sales_gbp"])
    weekday = by["weekday_pattern"]["values"]
    assert weekday["average_daily_sales_gbp"] == pytest.approx(weekday["positive_sales_gbp"]/weekday["covered_calendar_days"])
    s = build_summary()
    assert s["best_method"] == "weekday_mean_4w"
    assert s["relative_error_reduction_pct"] == pytest.approx(6.21092705010806)
    assert s["wape_difference_percentage_points"] == pytest.approx(6.85789332569881)
    assert s["prediction_rows"] == 20160
    np.testing.assert_allclose(s["relative_error_reduction_pct"],100*(s["comparator_absolute_error_units"]-s["candidate_absolute_error_units"])/s["comparator_absolute_error_units"],atol=1e-10)


@pytest.mark.integration
def test_walkthrough_scores_and_rules_match_saved_predictions():
    manifest = build_walkthrough()
    assert manifest == json.loads((OUT/"portfolio/walkthrough_examples.json").read_text(encoding="utf-8"))
    p = pd.read_csv(OUT/"training_windows_v1/predictions.csv",dtype={"product_id":str},float_precision="round_trip")
    p["error"] = (p.prediction-p.actual).abs()
    sums = p.groupby(["product_id","model"]).error.sum().unstack()
    reductions = sums.seasonal_naive-sums.weekday_mean_4w
    examples = {e["id"]:e for e in manifest["examples"]}
    assert examples["improvement"]["error_reduction_units"] == pytest.approx(reductions.max())
    assert examples["deterioration"]["error_reduction_units"] == pytest.approx(reductions.min())
    spike = examples["spike"]
    rows = p[p.model.eq("hw_expanding") & p.is_spike]
    assert spike["excess_units"] == pytest.approx((rows.actual-rows.spike_threshold).max())
    assert spike["actual_units"] > spike["spike_threshold"]
    for e in examples.values():
        assert e["selectors"]["Product"] == e["product_id"]
        assert e["selectors"]["Baseline comparisons"] == ["weekday_mean_4w","seasonal_naive"]


@pytest.mark.integration
def test_portfolio_local_links_and_generated_claims():
    paths = [ROOT/"README.md"]+[ROOT/"docs"/n for n in ["report-ownership.md","business-findings.md","dashboard-walkthrough.md","result-evidence.md","verification.md","setup-and-reproduction.md"]]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"[A-Z]:[\\/]Users[\\/]",text)
        for destination in re.findall(r"\]\(([^)]+)\)",text):
            if re.match(r"https?://",destination) or destination.startswith("#"):
                continue
            assert (path.parent/destination.split("#")[0]).exists(), (path.name,destination)
    s = build_summary()
    for path in [ROOT/"README.md",ROOT/"docs/result-evidence.md"]:
        text = path.read_text(encoding="utf-8")
        assert f"{s['relative_error_reduction_pct']:.1f}%" in text
        assert "later-2011" in text.lower() and "last-week" in text.lower()
    readme = (ROOT/"README.md").read_text(encoding="utf-8").lower()
    assert not re.search(r"resume|résumé|recruiter|interview|draft pr|currently private",readme)


@pytest.mark.parametrize("change",["modified","added"])
def test_package_rejects_changed_implementation_file_set(tmp_path, monkeypatch, change):
    import scripts.package_review as package
    import sys
    root=tmp_path/"project"; root.mkdir()
    for folder in ["src","sql","tests","scripts","protocols",".github"]:
        (root/folder).mkdir()
    checks={}
    for name in ["app.py","config.json","requirements.txt",".gitattributes","pytest.ini","package.json"]:
        (root/name).write_text("verified bytes",encoding="utf-8")
        checks[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    evidence=root/"evidence"; (evidence/"final-reproduction").mkdir(parents=True)
    (evidence/"final-reproduction/reproduction.json").write_text(json.dumps({"status":"passed","tested_implementation_commit":"tested","source_checksums":checks}))
    (evidence/"browser.json").write_text(json.dumps({"status":"passed","page_errors":[],"implementation_revision":"tested","source_checksums":{}}))
    if change=="modified":
        (root/"app.py").write_text("untested behavior",encoding="utf-8")
    else:
        (root/"src/new.py").write_text("untested addition",encoding="utf-8")
    monkeypatch.setattr(package,"ROOT",root)
    monkeypatch.setattr(package,"verify_archives",lambda:0)
    monkeypatch.setattr(sys,"argv",["package_review.py","--evidence-dir",str(evidence)])
    with pytest.raises(RuntimeError,match="changed since clean verification"):
        package.main()
    assert not (root/"deliverables").exists()
