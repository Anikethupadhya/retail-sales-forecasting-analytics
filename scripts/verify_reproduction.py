"""Fresh-environment verification using a separate workspace and no read caches."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common import save_json


def main():
    target = ROOT / ".repro-workspace"
    if target.exists():
        raise RuntimeError("Reproduction workspace already exists; preserve prior evidence and use a new workspace for another audit")
    target.mkdir()
    out = ROOT / "outputs/verification"
    for name in ["src", "sql", "tests", "protocols", "archives", "docs"]:
        shutil.copytree(ROOT/name, target/name, ignore=shutil.ignore_patterns("__pycache__"))
    for name in ["config.json", "requirements.txt", "app.py", "README.md", ".gitignore"]:
        shutil.copy2(ROOT/name, target/name)
    raw = target / "data/raw"
    raw.mkdir(parents=True)
    shutil.copy2(ROOT/"data/raw/online_retail_II.xlsx", raw/"online_retail_II.xlsx")
    python = ROOT / ".repro-venv/Scripts/python.exe"
    if not python.exists():
        raise RuntimeError("Install requirements in .repro-venv first")
    started = time.time()
    result = {"new_environment": str(python.relative_to(ROOT)), "separate_workspace": str(target.relative_to(ROOT)),
              "initial_processed_cache_files": 0, "initial_outputs_present": False,
              "installation_log": "outputs/verification/clean-install.log", "installation_verified_by_pip_check": False,
              "tolerances": {"forecast_metric_absolute": 1e-8, "relative": 1e-10, "sales_gbp_absolute": 1e-6}}
    save_json(out/"reproduction.json", {**result, "status": "running"})
    for label, command in [
        ("pip-check", [str(python),"-m","pip","check"]),
        ("pipeline", [str(python),"-m","src.pipeline"]),
        ("tests", [str(python),"-m","pytest","-q","--junitxml=outputs/verification/clean-tests.xml"]),
    ]:
        if label=="tests":
            (target/"outputs/verification").mkdir(parents=True,exist_ok=True)
        with (out/f"clean-{label}.log").open("w",encoding="utf-8") as log:
            proc = subprocess.run(command,cwd=target,stdout=log,stderr=subprocess.STDOUT)
        result[f"{label}_exit_code"] = proc.returncode
        if proc.returncode:
            save_json(out/"reproduction.json",{**result,"status":"failed","failed_step":label})
            raise RuntimeError(f"Clean {label} failed; inspect its log")
        print(f"Clean {label} passed",flush=True)
    result["installation_verified_by_pip_check"] = True
    files = sorted((ROOT/"outputs/sales").glob("*.csv")) + sorted((ROOT/"outputs/robustness").glob("*.csv")) + sorted((ROOT/"outputs/benchmark_analysis").glob("*.csv"))
    reconciled = []
    for path in files:
        relative = path.relative_to(ROOT)
        left = pd.read_csv(path,dtype={"product_id":str})
        right = pd.read_csv(target/relative,dtype={"product_id":str})
        assert list(left.columns)==list(right.columns) and left.shape==right.shape,relative
        for column in left:
            if pd.api.types.is_numeric_dtype(left[column]) and not pd.api.types.is_bool_dtype(left[column]):
                atol = 1e-6 if "gbp" in column or "value" in column else 1e-8
                np.testing.assert_allclose(left[column],right[column],rtol=1e-10,atol=atol,equal_nan=True,err_msg=f"{relative}:{column}")
            else:
                assert left[column].fillna("<null>").astype(str).equals(right[column].fillna("<null>").astype(str)),f"{relative}:{column}"
        reconciled.append(str(relative))
    left = pd.read_parquet(ROOT/"outputs/sales/product_daily_sales.parquet")
    right = pd.read_parquet(target/"outputs/sales/product_daily_sales.parquet")
    pd.testing.assert_frame_equal(left,right,check_exact=False,rtol=1e-10,atol=1e-6)
    for relative in ["outputs/sales/data_audit.json","outputs/robustness/split_manifest.json","outputs/robustness/model_events.json","outputs/sales/findings.json"]:
        first, second = json.loads((ROOT/relative).read_text()),json.loads((target/relative).read_text())
        if relative.endswith("findings.json"):
            # SQL summation may vary in last floating bits; display text must match.
            assert [f["text"] for f in first["findings"]]==[f["text"] for f in second["findings"]]
        else:
            assert first==second,relative
    shutil.copy2(target/"outputs/verification/clean-tests.xml",out/"clean-tests.xml")
    result.update({"status":"passed","reconciled_csv_files":reconciled,"customer_free_parquet_reconciled":True,
                   "raw_sha256":hashlib.sha256((raw/"online_retail_II.xlsx").read_bytes()).hexdigest(),
                   "clean_environment":json.loads((target/"outputs/run_manifest.json").read_text()),"duration_seconds":round(time.time()-started,2)})
    save_json(out/"reproduction.json",result)
    print(f"Reconciled {len(reconciled)} CSV files and full aggregate Parquet",flush=True)


if __name__=="__main__":
    main()
