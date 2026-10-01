"""Bounded inspection of tracked files/reachable blobs and nested archives; no secret contents printed."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.common import save_json

SECRETS = [rb"gh[pousr]_[A-Za-z0-9]{30,}", rb"github_pat_[A-Za-z0-9_]{60,}",
           rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}", rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
           rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"]


def inspect(data, name, findings, counts, *, depth=0):
    counts["inspected_items"] += 1
    for pattern in SECRETS:
        if re.search(pattern,data):
            findings.append({"location":name,"kind":"credential-pattern; contents withheld"})
            break
    lower = name.lower().replace("\\","/")
    if any(k in lower for k in [".env", "secrets.toml", "excluded_rows.csv", "returns_cancellations.csv"]) or ("data/raw/" in lower and not lower.endswith(".gitkeep")):
        findings.append({"location":name,"kind":"sensitive/raw filename requires review"})
    if lower.endswith(".csv"):
        first = data.decode("utf-8-sig",errors="replace").splitlines()[:2]
        if len(first)>1:
            fields = {f.strip().lower().replace("_"," ") for f in next(csv.reader(first))}
            if fields & {"customer id","customerid","invoice","invoice id","invoiceno","invoice number"}:
                findings.append({"location":name,"kind":"customer/invoice-level CSV columns"})
    if lower.endswith(".parquet"):
        import pyarrow.parquet as pq
        fields = {f.lower().replace("_"," ") for f in pq.read_schema(io.BytesIO(data)).names}
        if fields & {"customer id","customerid","invoice","invoice id","invoiceno"}:
            findings.append({"location":name,"kind":"customer/invoice-level Parquet columns"})
    if lower.endswith((".xlsx",".xls")):
        findings.append({"location":name,"kind":"workbook requires raw/customer-level review"})
    if lower.endswith(".zip"):
        if depth>=4:
            findings.append({"location":name,"kind":"archive depth limit; inspection incomplete"})
            return
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            counts["nested_archives"] += 1
            if archive.testzip() is not None:
                findings.append({"location":name,"kind":"archive integrity failure"})
            for item in archive.infolist():
                if not item.is_dir():
                    if item.file_size>128*1024*1024:
                        findings.append({"location":name+"!"+item.filename,"kind":"size limit; inspection incomplete"})
                    else:
                        inspect(archive.read(item),name+"!"+item.filename,findings,counts,depth=depth+1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence",type=Path,default=ROOT/"outputs/verification/portfolio/publication.json")
    args=parser.parse_args()
    findings=[]; counts={"tracked_files":0,"reachable_blobs":0,"nested_archives":0,"inspected_items":0}
    paths=subprocess.check_output(["git","ls-files","-z"],cwd=ROOT).decode().split("\0")
    for name in filter(None,paths):
        path=ROOT/name
        if path.is_file():
            counts["tracked_files"]+=1
            inspect(path.read_bytes(),name,findings,counts)
    objects=subprocess.check_output(["git","rev-list","--objects","--all"],cwd=ROOT,text=True).splitlines()
    batch=subprocess.Popen(["git","cat-file","--batch"],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for line in objects:
            oid,_,name=line.partition(" ")
            batch.stdin.write((oid+"\n").encode()); batch.stdin.flush()
            header=batch.stdout.readline().decode().split()
            size=int(header[2]); data=batch.stdout.read(size); batch.stdout.read(1)
            if header[1]=="blob":
                counts["reachable_blobs"]+=1
                inspect(data,f"git:{oid}:{name}",findings,counts)
    finally:
        batch.stdin.close(); batch.stdout.close(); batch.wait()
    result={"status":"review_required" if findings else "no_matches_in_inspected_scope", "revision":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            "counts":counts,"findings":findings,"patterns":"GitHub/OpenAI/AWS key formats and private-key headers; raw/sensitive names; customer/invoice CSV/Parquet fields; nested ZIP entries",
            "limits":"Targeted patterns and known extract schemas do not prove exhaustive absence of secrets or personal data. Other credential formats, encoded/encrypted payloads and unidentified schemas require separate review.",
            "code_license_present":any((ROOT/n).exists() for n in ["LICENSE","LICENSE.md","LICENSE.txt"]),"repository_visibility_changed":False}
    save_json(args.evidence,result)
    print(json.dumps({"status":result["status"],"counts":counts,"findings_count":len(findings),"code_license_present":result["code_license_present"]}))


if __name__=="__main__":
    main()
