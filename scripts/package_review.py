"""Package the current verified implementation and customer-free review evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.common import save_json
from src.evidence import verify_archives


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir",type=Path,default=ROOT/"outputs/verification/portfolio")
    args=parser.parse_args()
    verify_archives()
    reproduction_path=args.evidence_dir/"final-reproduction/reproduction.json"
    browser_path=args.evidence_dir/"browser.json"
    reproduction=json.loads(reproduction_path.read_text(encoding="utf-8"))
    browser=json.loads(browser_path.read_text(encoding="utf-8"))
    if reproduction["status"]!="passed" or browser.get("status")!="passed" or browser["page_errors"]:
        raise RuntimeError("Current reproduction and rendered verification must pass")
    if browser["implementation_revision"]!=reproduction["tested_implementation_commit"]:
        raise RuntimeError("Browser evidence must identify the tested implementation")
    current_sources={p.relative_to(ROOT).as_posix():sha(p) for folder in ["src","sql","tests","scripts","protocols",".github"] for p in (ROOT/folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    current_sources.update({n:sha(ROOT/n) for n in ["app.py","config.json","requirements.txt",".gitattributes","pytest.ini","package.json"]})
    if current_sources!=reproduction["source_checksums"]:
        raise RuntimeError("Implementation file set or bytes changed since clean verification")
    for name,checksum in browser["source_checksums"].items():
        if sha(ROOT/name)!=checksum:
            raise RuntimeError(f"Changed since rendered verification: {name}")
    files=[ROOT/n for n in [".gitignore",".gitattributes","README.md","app.py","config.json","requirements.txt","pytest.ini","package.json","outputs/run_manifest.json"]]
    folders=["src","sql","tests","scripts","protocols","docs","archives",".github","outputs/sales","outputs/robustness","outputs/benchmark_analysis","outputs/training_windows_v1","outputs/portfolio","outputs/verification"]
    extensions={".py",".sql",".cjs",".json",".sha256",".md",".txt",".csv",".parquet",".png",".html",".xml",".log",".zip",".yml",".yaml",".ini"}
    for folder in folders:
        files.extend(p for p in (ROOT/folder).rglob("*") if p.is_file() and p.suffix in extensions and "__pycache__" not in p.parts)
    forbidden=["data/raw/","data/processed/",".venv/",".repro-venv/",".repro-workspace/",".verification-runs/","node_modules/",".git/","returns_cancellations","excluded_rows",".duckdb","secrets.toml",".env"]
    entries={p.relative_to(ROOT).as_posix():p for p in sorted(set(files))}
    for name in entries:
        if any(token in name for token in forbidden):
            raise ValueError(f"Forbidden review entry: {name}")
    for name in ["portfolio-final-github.json","portfolio-final-pr.json","portfolio-final-repository.json"]:
        path=ROOT/"deliverables"/name
        if path.exists():
            entries["review-evidence/"+name]=path
    target=ROOT/"deliverables"; target.mkdir(exist_ok=True)
    filename=target/"retail-sales-forecasting-analytics-review.zip"
    revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    manifest={"project":"Retail Sales Forecasting & Analytics","package_purpose":"Inspection; clone with Git history for full execution",
              "tested_implementation_revision":reproduction["tested_implementation_commit"],"packaging_revision":revision,
              "packaging_worktree_status":subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True).strip(),
              "verification_manifests":{"reproduction":reproduction_path.relative_to(ROOT).as_posix(),"browser":browser_path.relative_to(ROOT).as_posix()},
              "source_checksums":current_sources,"protected_checksums":reproduction["protected_checksums"],
              "policy":"Allowlisted implementation, maintained/generated documentation, customer-free outputs and required historical evidence; no raw data, secrets, environments, databases or Git internals",
              "entries":{name:{"sha256":sha(path),"bytes":path.stat().st_size} for name,path in entries.items()}}
    save_json(target/"review-manifest.json",manifest)
    with zipfile.ZipFile(filename,"w",zipfile.ZIP_DEFLATED) as zipped:
        for name,path in entries.items():
            zipped.write(path,name)
        zipped.writestr("review-manifest.json",json.dumps(manifest,indent=2))
    with zipfile.ZipFile(filename) as zipped:
        assert zipped.testzip() is None
        for name,record in manifest["entries"].items():
            assert hashlib.sha256(zipped.read(name)).hexdigest()==record["sha256"],name
        for name,checksum in reproduction["protected_checksums"].items():
            assert hashlib.sha256(zipped.read(name)).hexdigest()==checksum,name
        assert all(not any(token in name for token in forbidden) for name in zipped.namelist())
    save_json(target/"package-verification.json",{"zip":filename.name,"sha256":sha(filename),"entries":len(entries)+1,"bytes":filename.stat().st_size,
              "tested_implementation_revision":reproduction["tested_implementation_commit"],"packaging_revision":revision,
              "integrity_checked":True,"entry_hashes_checked":True,"protected_hashes_checked":True,"exclusion_check_passed":True})
    print(json.dumps({"zip":str(filename),"entries":len(entries)+1,"bytes":filename.stat().st_size,"tested_revision":reproduction["tested_implementation_commit"],"packaging_revision":revision}))


if __name__=="__main__":
    main()
