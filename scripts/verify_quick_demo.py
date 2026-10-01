"""Prove a clean checkout can show real saved outputs without raw data or a database."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.common import save_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,required=True)
    args = parser.parse_args()
    assert not list((ROOT/"data/raw").glob("*.xlsx")), "Quick demo proof requires a checkout without the workbook"
    assert not list((ROOT/"outputs").glob("*.duckdb*")), "Quick demo proof requires no database"
    assert not (ROOT/"data/processed").exists(), "Quick demo proof requires no processed cache"
    from streamlit.testing.v1 import AppTest
    def forbidden(*a,**k):
        raise AssertionError("Quick demonstration must not prepare raw data, fit models or build a database")
    with patch("src.data.prepare_sales",forbidden), patch("src.forecast.predict",forbidden), patch("src.analytics.build_sales_database",forbidden):
        app = AppTest.from_file(str(ROOT/"app.py")).run(timeout=60)
        assert not app.exception
        assert [t.label for t in app.tabs] == ["Sales Overview","Forecast Evaluation","Model Performance"]
        for example in ["Improvement","Deterioration","Spike"]:
            app.selectbox(key="walkthrough_example").select(example).run(timeout=60)
            assert not app.exception
            assert app.selectbox(key="experiment").value == "Training-window experiment"
    save_json(args.evidence,{"status":"passed","tested_revision":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                            "raw_workbook_present":False,"database_present":False,"processed_cache_present":False,
                            "saved_outputs_used":True,"tabs_checked":3,"walkthrough_examples_checked":3,
                            "app_sha256":hashlib.sha256((ROOT/"app.py").read_bytes()).hexdigest()})


if __name__=="__main__":
    main()
