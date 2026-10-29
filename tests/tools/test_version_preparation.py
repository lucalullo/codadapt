"""Versioning boundary tests: no training, package imports, builds or publication."""
from pathlib import Path
import hashlib
import importlib.util
import json
import pytest

HERE=Path(__file__).resolve().parent
TOOL=HERE/'prepare_version.py' if (HERE/'prepare_version.py').is_file() else HERE.parents[1]/'tools/prepare_version.py'
spec=importlib.util.spec_from_file_location('prepare_version_under_test', TOOL)
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)


def fixture(tmp_path):
    root=tmp_path/'source'
    (root/'src/codadapt/serving').mkdir(parents=True)
    (root/'pyproject.toml').write_bytes(b'[project]\nname = "codadapt"\nversion = "2.0.0.dev0+lab.g6r1"\n\n[other]\nvalue = 1\n')
    (root/'src/codadapt/_version.py').write_bytes(b'__version__ = "2.0.0.dev0+lab.g6r1"\n')
    (root/'src/codadapt/__init__.py').write_bytes(b'from ._version import __version__\n')
    (root/'src/codadapt/serving/_contract.py').write_bytes(b'# frozen contract loader\n')
    native,serving,combined=tool.sources(root)
    contract=dict(format=tool.FORMAT,native_version='2.0.0.dev0+lab.g6r1',native_sources=native,
        serving_sources=serving,native_source_sha256=combined,public_release=False,inherited_baseline_sources={'old.py':'0'*64})
    (root/'src/codadapt/serving/source_contract.json').write_bytes((json.dumps(contract,indent=2)+'\n').encode())
    (root/'README.md').write_text('Historical 2.0.0; proposed 2.1.0.\n')
    return root


def file_hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}


def test_prepare_copy_and_contract_deterministic(tmp_path):
    source=fixture(tmp_path);before=file_hashes(source)
    first=tmp_path/'first';second=tmp_path/'second'
    a=tool.prepare(source,first,'2.1.0');b=tool.prepare(source,second,'2.1.0')
    assert a==b
    assert file_hashes(first)==file_hashes(second)
    assert file_hashes(source)==before
    assert set(a['changed_files'])=={'pyproject.toml','src/codadapt/_version.py','src/codadapt/serving/source_contract.json'}
    assert tool.package_version(first)==tool.project_version(first)=='2.1.0'
    assert a['status']=='UNQUALIFIED_VERSION_COPY' and a['RELEASE']=='HOLD'
    assert a['after']['contract_SHA256']!=a['before']['contract_SHA256']
    new=json.loads((first/'src/codadapt/serving/source_contract.json').read_text())
    assert new['native_sources']['codadapt/_version.py']==tool.sha(first/'src/codadapt/_version.py')
    assert new['native_source_sha256']==hashlib.sha256(json.dumps(new['native_sources'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert new['inherited_baseline_sources']=={'old.py':'0'*64}
    assert not a['old_serving_images_readable_by_new_contract']
    assert new['public_release'] is False
    assert (first/'README.md').read_text()==(source/'README.md').read_text()
    assert a['remaining_reference_inventory']


@pytest.mark.parametrize('bad_version',['2.0.0','02.1.0','2.1','2.1.0+local','2.1.0\n','../2.1.0'])
def test_reject_invalid_or_published_version_before_write(tmp_path,bad_version):
    source=fixture(tmp_path);destination=tmp_path/'output'
    with pytest.raises(ValueError):tool.prepare(source,destination,bad_version)
    assert not destination.exists()


@pytest.mark.parametrize('case',['package_version','source_digest','combined_digest','serving_digest','unknown_format','missing_file','extra_source'])
def test_reject_inconsistent_source_before_copy(tmp_path,case):
    source=fixture(tmp_path);destination=tmp_path/'output'
    contract=source/'src/codadapt/serving/source_contract.json'
    if case=='package_version':(source/'src/codadapt/_version.py').write_text('__version__ = "9.9.9"\n')
    elif case=='source_digest':(source/'src/codadapt/__init__.py').write_text('# changed\n')
    elif case=='missing_file':(source/'src/codadapt/serving/_contract.py').unlink()
    elif case=='extra_source':(source/'src/codadapt/new.py').write_text('# unbound new source\n')
    else:
        data=json.loads(contract.read_text())
        if case=='combined_digest':data['native_source_sha256']='0'*64
        if case=='serving_digest':data['serving_sources']['_contract.py']='0'*64
        if case=='unknown_format':data['format']='unsupported'
        contract.write_text(json.dumps(data))
    with pytest.raises((ValueError,FileNotFoundError)):tool.prepare(source,destination,'2.1.0')
    assert not destination.exists()


@pytest.mark.parametrize('case',['inside_source','same_source','source_parent','existing'])
def test_non_overlapping_new_destination_required(tmp_path,case):
    source=fixture(tmp_path)
    destination={'inside_source':source/'new','same_source':source,'source_parent':tmp_path,'existing':tmp_path/'existing'}[case]
    if case=='existing':destination.mkdir();(destination/'KEEP').write_text('keep')
    before=file_hashes(source)
    with pytest.raises(ValueError):tool.prepare(source,destination,'2.1.0')
    assert file_hashes(source)==before
    if case=='existing':assert (destination/'KEEP').read_text()=='keep'


def test_old_artifacts_not_requalified_by_copy(tmp_path):
    source=fixture(tmp_path)
    for rel in ('dist/old.whl','qualification/old_pass.json','qualification_runs/pass/RESULT.json','build/cache','MANIFEST_SHA256.json','FILE_COMPARISON.json'):
        file=source/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('old identity')
    target=tmp_path/'new_version';tool.prepare(source,target,'2.1.0rc1')
    assert not (target/'dist').exists()
    assert not (target/'qualification').exists()
    assert not (target/'qualification_runs').exists()
    assert not (target/'MANIFEST_SHA256.json').exists()
    assert not (target/'FILE_COMPARISON.json').exists()
    assert tool.validate(target)['version']=='2.1.0rc1'
