import pytest
from streamlit.testing.v1 import AppTest

from src.common import ROOT, OUT


@pytest.mark.dashboard
def test_tabs_experiments_products_periods_and_scopes():
    app = AppTest.from_file(str(ROOT/"app.py")).run(timeout=60)
    assert len(app.exception)==0
    assert [t.label for t in app.tabs]==["Sales Overview","Forecast Evaluation","Model Performance"]
    assert len(app.slider)==0
    app.selectbox(key="ranking").select("Positive units sold")
    app.selectbox(key="experiment").select("Retrospective robustness")
    app.run(timeout=60)
    assert len(app.exception)==0
    app.selectbox(key="product_robustness").select_index(1)
    app.selectbox(key="period").select_index(5)
    app.selectbox(key="comparison").select("weekday_mean_8w")
    app.run(timeout=60)
    assert len(app.exception)==0
    assert any("Training cutoff: 2011-10-31" in m.value for m in app.markdown)
    assert any("Selected product only" in m.value for m in app.markdown)
    assert any("All cleaned merchandise" in s.value for s in app.subheader)


@pytest.mark.dashboard
def test_window_controls_load_saved_series_without_fitting(monkeypatch):
    import src.forecast
    def forbidden(*args, **kwargs):
        raise AssertionError("Dashboard must never fit forecasts")
    monkeypatch.setattr(src.forecast,"predict",forbidden)
    app=AppTest.from_file(str(ROOT/"app.py")).run(timeout=60)
    app.selectbox(key="experiment").select("Training-window experiment").run(timeout=60)
    assert not app.exception
    assert app.multiselect(key="window_methods").value==["hw_expanding"]
    app.multiselect(key="window_methods").set_value(["hw_expanding","hw_182d","hw_365d"])
    app.multiselect(key="window_baselines").set_value(["seasonal_naive","weekday_mean_4w","weekday_mean_8w"])
    app.selectbox(key="period").select_index(5)
    app.selectbox(key="product_robustness").select_index(3)
    app.selectbox(key="window_candidate").select("hw_182d")
    app.run(timeout=60)
    assert not app.exception
    assert any("Training cutoff: 2011-10-31" in m.value for m in app.markdown)
    assert any("normalized absolute error" in c.value for c in app.caption)
    # Confirm rendered forecast chart scope and all six requested forecast traces.
    import json
    chart=app.get("plotly_chart")[3]
    spec=json.loads(chart.proto.spec)
    names={trace["name"] for trace in spec["data"]}
    assert {"Smoothing · expanding history","Smoothing · 182 days","Smoothing · 365 days","Last-week baseline","4-week weekday average","8-week weekday average"}<=names
    assert spec["layout"]["yaxis"]["title"]["text"]=="Positive units sold"


@pytest.mark.dashboard
def test_walkthrough_shortcuts_match_evidence_without_fitting(monkeypatch):
    import json
    import src.forecast
    import src.training_windows
    def forbidden(*args, **kwargs):
        raise AssertionError("Walkthrough must use saved forecasts")
    monkeypatch.setattr(src.forecast,"predict",forbidden)
    monkeypatch.setattr(src.training_windows,"evaluate_windows",forbidden)
    evidence = json.loads((OUT/"portfolio/walkthrough_examples.json").read_text(encoding="utf-8"))
    app = AppTest.from_file(str(ROOT/"app.py")).run(timeout=60)
    assert any("Start here" in m.value for m in app.markdown)
    for example in evidence["examples"]:
        app.selectbox(key="walkthrough_example").select(example["id"].title()).run(timeout=60)
        assert not app.exception
        assert app.selectbox(key="experiment").value == "Training-window experiment"
        assert app.selectbox(key="period").value["forecast_start"] == example["forecast_start"]
        assert app.selectbox(key="product_robustness").value == example["product_id"]
        assert app.multiselect(key="window_methods").value == []
        assert app.multiselect(key="window_baselines").value == example["selectors"]["Baseline comparisons"]
    app.selectbox(key="product_robustness").select_index(0).run(timeout=60)
    assert not app.exception
    assert any("Manual selections differ" in c.value for c in app.caption)


@pytest.mark.dashboard
@pytest.mark.parametrize("partial",[False,True])
def test_missing_results_show_rebuild_instructions(monkeypatch,tmp_path,partial):
    import src.common
    monkeypatch.setattr(src.common,"OUT",tmp_path)
    if partial:
        (tmp_path/"run_manifest.json").write_text('{}')
    app=AppTest.from_file(str(ROOT/"app.py")).run(timeout=60)
    assert not app.exception
    assert any("python -m src.pipeline" in message.value for message in app.info)
