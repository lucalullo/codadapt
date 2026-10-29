"""Inspect generated distributions without injecting host dependencies or fitting."""
from pathlib import Path
from email import message_from_bytes
import json
import os
import tarfile
import zipfile
import pytest
from codadapt import __version__

ROOT=Path(__file__).resolve().parents[2]

@pytest.fixture(scope='module')
def distributions():
    folder=Path(os.environ.get('CODADAPT_TEST_DIST',ROOT/'dist'))
    wheels=sorted(folder.glob(f'codadapt-{__version__}-*.whl'))
    source=folder/f'codadapt-{__version__}.tar.gz'
    assert wheels and source.is_file(),'Build wheel and sdist first; see docs/QUALIFICATION.md or set CODADAPT_TEST_DIST to qualified development artifacts'
    return wheels,source

def test_wheel_code_and_contract_match_source(distributions):
    for wheel in distributions[0]:
        with zipfile.ZipFile(wheel) as archive:
            for p in (ROOT/'src/codadapt').rglob('*'):
                if p.is_file() and p.suffix in ('.py','.json'):
                    assert archive.read(p.relative_to(ROOT/'src').as_posix())==p.read_bytes()
            meta=message_from_bytes(archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))))
            assert meta['Name']=='codadapt' and meta['Version']==__version__
            assert meta.get_all('Requires-Dist')

def test_optional_dependencies_remain_optional(distributions):
    with zipfile.ZipFile(distributions[0][0]) as archive:
        meta=message_from_bytes(archive.read(next(n for n in archive.namelist() if n.endswith('.dist-info/METADATA'))))
    requirements=meta.get_all('Requires-Dist')
    assert len([r for r in requirements if r.startswith('interpret-core') and 'extra == "ebm"' in r])==1
    assert not any(r.lower().startswith(('lightgbm','xgboost','catboost')) for r in requirements)

def test_sdist_rebuild_and_test_inputs_complete(distributions):
    with tarfile.open(distributions[1]) as archive:
        names={m.name.split('/',1)[1] for m in archive if '/' in m.name}
        for name in ('pyproject.toml','setup.py','native/memory_read.cpp','src/codadapt/serving/source_contract.json',
            'docs/API.md','docs/EBM_COMPILER.md','docs/SAFE_BLEND_EXPERIMENTAL.md',
            'tools/qualify_platform.py','tests/tools/test_distribution_contents.py','tests/data/binary/DATA.npz',
            'requirements/build.txt','examples/basic_usage.py'):
            assert name in names,name

def test_no_development_memory_or_unsafe_archive_members(distributions):
    with tarfile.open(distributions[1]) as archive:
        for member in archive:
            assert member.isfile() or member.isdir()
            assert not member.name.startswith('/') and '..' not in member.name.split('/')
            parts=member.name.split('/')
            assert not any(p in ('.git','.venv','research_private','PRIVATE_CODEX','dist','__pycache__') for p in parts)
