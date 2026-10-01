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
