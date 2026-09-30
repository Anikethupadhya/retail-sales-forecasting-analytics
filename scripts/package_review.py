"""Allowlisted customer-free review bundle; no raw data, environments or databases."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.common import save_json
from src.evidence import verify_archives


def main():
    verify_archives()
    reproduction = json.loads((ROOT/"outputs/verification/reproduction.json").read_text())
    browser = json.loads((ROOT/"outputs/verification/browser.json").read_text())
    if reproduction["status"] != "passed" or browser["page_errors"]:
        raise RuntimeError("Verification must pass before packaging")
    files = [ROOT/name for name in [".gitignore","README.md","app.py","config.json","requirements.txt"]]
    folders = ["src","sql","tests","scripts","protocols","docs","archives",
               "outputs/sales","outputs/robustness","outputs/benchmark_analysis","outputs/verification"]
    extensions = {".py",".sql",".cjs",".json",".sha256",".md",".txt",".csv",".parquet",".png",".html",".xml",".log",".zip"}
    for folder in folders:
        files.extend(f for f in (ROOT/folder).rglob("*") if f.is_file() and f.suffix in extensions and "__pycache__" not in f.parts)
    files = sorted(set(files))
    forbidden = ["data/raw/","data/processed/",".venv/",".repro-venv/",".repro-workspace/",".git/","returns_cancellations","excluded_rows",".duckdb"]
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        if any(token in name for token in forbidden):
            raise ValueError(f"Forbidden review entry: {name}")
    target = ROOT/"deliverables"
    target.mkdir(exist_ok=True)
    filename = target/"retail-sales-forecasting-analytics-review.zip"
    manifest = {"project":"Retail Sales Forecasting & Analytics","policy":"Allowlisted source, documentation, historical evidence and customer-free aggregates only; raw files, customer extracts, environments, caches and database binaries excluded.",
                "entries":{p.relative_to(ROOT).as_posix():{"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"bytes":p.stat().st_size} for p in files}}
    save_json(target/"review-manifest.json",manifest)
    with zipfile.ZipFile(filename,"w",zipfile.ZIP_DEFLATED) as zipped:
        for path in files:
            zipped.write(path,path.relative_to(ROOT).as_posix())
        zipped.writestr("review-manifest.json",json.dumps(manifest,indent=2))
    with zipfile.ZipFile(filename) as zipped:
        assert zipped.testzip() is None
        assert all(not any(token in name for token in forbidden) for name in zipped.namelist())
    save_json(target/"package-verification.json",{"zip":filename.name,"sha256":hashlib.sha256(filename.read_bytes()).hexdigest(),"entries":len(files)+1,"bytes":filename.stat().st_size,"integrity_checked":True,"exclusion_check_passed":True})
    print(filename)
    print(f"{len(files)+1} entries; {filename.stat().st_size/1024/1024:.2f} MB; integrity and exclusions passed")


if __name__=="__main__":
    main()
