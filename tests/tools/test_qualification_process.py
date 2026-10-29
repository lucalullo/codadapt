"""Finite process budgets and exact ownership; no model fitting."""
from pathlib import Path
import importlib.util
import os
import sys
import psutil
import pytest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('qualification_process_test',ROOT/'tools/qualification_process.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

def run(tmp_path,code,**kwargs):
    with (tmp_path/'out').open('wb') as out,(tmp_path/'err').open('wb') as err:
        return helper.run_owned([sys.executable,'-I','-B','-c',code],cwd=tmp_path,env=os.environ.copy(),stdout=out,stderr=err,**kwargs)

def assert_gone(result):
    assert result['active_recorded_owned_processes']==0
    for pid,birth in result['owned_process_births'].items():
        try:
            process=psutil.Process(int(pid))
            assert abs(process.create_time()-birth)>=.01 or not process.is_running() or process.status()==psutil.STATUS_ZOMBIE
        except psutil.NoSuchProcess:pass

def test_process_success(tmp_path):
    result=run(tmp_path,'print("ok")')
    assert result['returncode']==0 and not result['resource_stop']
    assert (tmp_path/'out').read_text().strip()=='ok';assert_gone(result)

def test_process_error_is_preserved(tmp_path):
    result=run(tmp_path,'raise SystemExit(7)')
    assert result['returncode']==7;assert_gone(result)

def test_time_budget_reaps_owned_descendant(tmp_path):
    code='import subprocess,sys,time; child=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); print(child.pid,flush=True); time.sleep(30)'
    result=run(tmp_path,code,timeout=.6)
    assert result['returncode']==124 and result['resource_stop']=='COMMAND_TIMEOUT'
    child=(tmp_path/'out').read_text().strip()
    assert child and child in result['owned_process_births'];assert_gone(result)

def test_memory_budget_reaps_owned_process(tmp_path):
    result=run(tmp_path,'import time; time.sleep(30)',max_rss=1)
    assert result['returncode']==137 and result['resource_stop']=='OWNED_TREE_RSS_LIMIT';assert_gone(result)

def test_invalid_budget_does_not_spawn(tmp_path,monkeypatch):
    monkeypatch.setattr(helper.subprocess,'Popen',lambda *args,**kwargs:pytest.fail('Must not spawn'))
    with pytest.raises(ValueError):run(tmp_path,'',timeout=0)

def test_profile_311_avoids_numpy312_requirement():
    spec=importlib.util.spec_from_file_location('qualify_test',ROOT/'tools/qualify_platform.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    file,status=runner.profile((3,11,18))
    assert file=='windows310.txt' and 'NOT_TESTED' in status
