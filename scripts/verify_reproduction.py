"""Verify an exact committed revision in fresh, run-specific directories."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common import save_json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_frame(left, right, label):
    assert list(left.columns) == list(right.columns) and left.shape == right.shape, f'Schema/coverage: {label}'
    candidates = [
        ['experiment','model','product_id','forecast_start','date'],
        ['model','product_id','forecast_start','date'], ['model','product_id','date'],
        ['model','baseline','product_id','forecast_start'], ['model','baseline','product_id'],
        ['model','baseline','forecast_start'], ['model','product_id','forecast_start'],
        ['model','product_id'], ['model','forecast_start'],
        ['baseline','product_id','forecast_start'], ['baseline','product_id'],
        ['model','baseline'], ['model'], ['product_id','forecast_start'],
        ['product_id','date'], ['product_id'], ['date'], ['month_start'], ['weekday_number'], ['year']]
    keys = next((k for k in candidates if set(k) <= set(left) and not left.duplicated(k).any() and not right.duplicated(k).any()), None)
    assert keys, f'No unique semantic reconciliation key: {label}'
    left, right = [f.sort_values(keys).reset_index(drop=True) for f in [left,right]]
    exact = {'horizon_day','observations','training_days','training_observations','wins','losses','ties','undefined','negative_predictions_clipped','covered_calendar_days'}
    for col in left:
        if col in keys or col in exact or not pd.api.types.is_numeric_dtype(left[col]) or pd.api.types.is_bool_dtype(left[col]):
            pd.testing.assert_series_equal(left[col],right[col],check_names=False,check_dtype=False,check_exact=True,obj=f'{label}:{col}')
        else:
            np.testing.assert_allclose(left[col],right[col],rtol=1e-10,atol=1e-6 if 'gbp' in col or 'value' in col else 1e-8,equal_nan=True,err_msg=f'{label}:{col}')
    return keys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',default='HEAD')
    parser.add_argument('--runs-dir',type=Path,default=ROOT/'.verification-runs')
    parser.add_argument('--raw-workbook',type=Path,default=ROOT/'data/raw/online_retail_II.xlsx')
    args = parser.parse_args()
    revision = subprocess.check_output(['git','rev-parse',args.revision],cwd=ROOT,text=True).strip()
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    run = args.runs_dir.resolve()/run_id
    workspace, environment, evidence, reference = [run/p for p in ['workspace','environment','evidence','reference']]
    evidence.mkdir(parents=True,exist_ok=False)
    result = {'run_id':run_id,'tested_implementation_commit':revision,'status':'running','driver_python':platform.python_version(),
        'workspace':str(workspace),'environment':str(environment),'evidence_directory':str(evidence),'commands':[],
        'initial_processed_cache_files':0,'tolerances':{'relative':1e-10,'forecast_metric_absolute':1e-8,'sales_gbp_absolute':1e-6},
        'excluded_nondeterministic_metadata':['run_manifest.duration_seconds','experiment_manifest.duration_seconds','experiment_manifest.implementation_revision','experiment_manifest.source_checksums','Plotly HTML div IDs']}
    def record():
        save_json(evidence/'reproduction.json',result)
    def command(label,argv,cwd=workspace):
        start = time.time()
        with (evidence/f'{label}.log').open('w',encoding='utf-8') as log:
            code = subprocess.run([str(a) for a in argv],cwd=cwd,stdout=log,stderr=subprocess.STDOUT).returncode
        result['commands'].append({'label':label,'argv':[str(a) for a in argv],'cwd':str(cwd),'exit_status':code,'seconds':round(time.time()-start,3)})
        record()
        if code:
            raise RuntimeError(f'{label} failed ({code}); inspect {evidence}')
        print(f'{run_id}: {label} passed',flush=True)
    started = time.time()
    record()
    try:
        command('clone',['git','clone','--local','--no-hardlinks',ROOT,workspace],ROOT)
        command('checkout',['git','checkout','--detach',revision])
        result['checkout_initial_status'] = subprocess.check_output(['git','status','--porcelain'],cwd=workspace,text=True).strip()
        assert not result['checkout_initial_status'], 'Initial checkout must be clean'
        result['source_checksums'] = {p.relative_to(workspace).as_posix():sha(p) for folder in ['src','sql','tests','scripts','protocols','.github'] for p in (workspace/folder).rglob('*') if p.is_file()}
        result['source_checksums'].update({n:sha(workspace/n) for n in ['app.py','config.json','requirements.txt','.gitattributes']})
        shutil.copytree(workspace/'outputs',reference)
        # Delete only this newly created resolved checkout's generated output directory.
        shutil.rmtree(workspace/'outputs')
        assert not (workspace/'data/processed').exists()
        result['copied_generated_outputs_removed'] = True
        result['protected_checksums'] = {p.relative_to(workspace).as_posix():sha(p) for folder in ['archives','protocols'] for p in (workspace/folder).rglob('*') if p.is_file()}
        raw = workspace/'data/raw/online_retail_II.xlsx'
        raw.parent.mkdir(parents=True,exist_ok=True)
        expected = json.loads((reference/'run_manifest.json').read_text())['raw_sha256']
        if args.raw_workbook.exists():
            assert sha(args.raw_workbook)==expected, 'Official workbook checksum mismatch'
            shutil.copy2(args.raw_workbook,raw)
            result['raw_acquisition'] = 'Explicit copy of existing checksum-verified official UCI workbook'
        else:
            result['raw_acquisition'] = 'Official UCI acquisition by pipeline; checked after execution'
        command('create-environment',[sys.executable,'-m','venv',environment])
        python = environment/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
        command('install',[python,'-m','pip','install','-r',workspace/'requirements.txt'])
        command('pip-check',[python,'-m','pip','check'])
        command('pipeline',[python,'-m','src.pipeline'])
        assert sha(raw)==expected
        result['raw_sha256'] = sha(raw)
        command('tests',[python,'-m','pytest','-q',f'--junitxml={evidence / "tests.xml"}'])
        command('dashboard-smoke',[python,'-c',"from streamlit.testing.v1 import AppTest; a=AppTest.from_file('app.py').run(timeout=60); assert not a.exception; assert [t.label for t in a.tabs]==['Sales Overview','Forecast Evaluation','Model Performance']"])
        reconciled = []
        for folder in ['sales','robustness','benchmark_analysis','training_windows_v1']:
            for path in sorted((reference/folder).glob('*.csv')):
                relative = path.relative_to(reference)
                keys = compare_frame(pd.read_csv(path,dtype={'product_id':str}),pd.read_csv(workspace/'outputs'/relative,dtype={'product_id':str}),str(relative))
                reconciled.append({'path':str(relative),'keys':keys})
        compare_frame(pd.read_parquet(reference/'sales/product_daily_sales.parquet'),pd.read_parquet(workspace/'outputs/sales/product_daily_sales.parquet'),'customer-free parquet')
        for folder in ['sales','robustness','benchmark_analysis','training_windows_v1']:
            for path in sorted((reference/folder).glob('*.json')):
                if path.name=='experiment_manifest.json':
                    continue
                relative = path.relative_to(reference)
                left,right = json.loads(path.read_text()),json.loads((workspace/'outputs'/relative).read_text())
                if path.name=='findings.json':
                    assert left['scope']==right['scope']
                    for a,b in zip(left['findings'],right['findings'],strict=True):
                        np.testing.assert_allclose(a['value'],b['value'],rtol=1e-10,atol=1e-6)
                        assert {k:v for k,v in a.items() if k!='value'}=={k:v for k,v in b.items() if k!='value'}
                else:
                    assert left==right, relative
        for path,checksum in result['protected_checksums'].items():
            assert sha(workspace/path)==checksum, path
        result['environment_record'] = json.loads((workspace/'outputs/run_manifest.json').read_text())
        assert result['environment_record']['python']==json.loads((reference/'run_manifest.json').read_text())['python'], 'Runtime changed'
        manifest = workspace/'outputs/training_windows_v1/experiment_manifest.json'
        if manifest.exists():
            experiment = json.loads(manifest.read_text())
            assert experiment['implementation_revision']==revision
            result['experiment_provenance'] = experiment
            assert experiment['protocol_sha256']==sha(workspace/'protocols/training_windows_v1.json')
        result.update(status='passed',reconciled_csv_files=reconciled,customer_free_parquet_reconciled=True,protected_artifacts_unchanged=True,duration_seconds=round(time.time()-started,2))
    except Exception as exc:
        result.update(status='failed',error=str(exc),duration_seconds=round(time.time()-started,2))
        raise
    finally:
        record()
    print(f'Evidence: {evidence}',flush=True)


if __name__=='__main__':
    main()
