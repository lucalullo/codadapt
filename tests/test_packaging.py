"""Distribution safety contracts for the current pure-Python build backend."""
from pathlib import Path
import importlib.util

import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('codadapt_build_contract',ROOT/'tools/release_backend.py')
backend=importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


@pytest.mark.parametrize('name',['../outside.py','/absolute.py','C:/absolute.py','a\\b.py','a/../b.py','./a.py'])
def test_source_members_refuse_unsafe_paths(name,tmp_path,monkeypatch):
    (tmp_path/'release').mkdir()
    (tmp_path/'release/SOURCE_MANIFEST.txt').write_text(name+'\n',encoding='utf-8')
    monkeypatch.setattr(backend,'ROOT',tmp_path)
    with pytest.raises(ValueError,match='Invalid source member'):
        backend.source_names()


def test_source_allowlist_refuses_missing_and_duplicate_files(tmp_path,monkeypatch):
    (tmp_path/'release').mkdir()
    manifest=tmp_path/'release/SOURCE_MANIFEST.txt'
    monkeypatch.setattr(backend,'ROOT',tmp_path)
    manifest.write_text('missing.py\n',encoding='utf-8')
    with pytest.raises(ValueError,match='Missing or unsafe'):
        backend.source_names()
    manifest.write_text('a.py\na.py\n',encoding='utf-8')
    with pytest.raises(ValueError,match='duplicate'):
        backend.source_names()


def test_public_metadata_has_author_license_and_exact_readme():
    from email.parser import BytesParser
    raw=backend.metadata_bytes()
    metadata=BytesParser().parsebytes(raw)
    assert metadata['Name']=='codadapt'
    assert metadata['Version']=='2.2.0'
    assert metadata['Author']=='Luca Lullo'
    assert metadata['License-Expression']=='MIT'
    assert metadata['Metadata-Version']=='2.4'
    assert raw.split(b'\n\n',1)[1]==(ROOT/'README.md').read_bytes()
    payload=backend.wheel_payload()
    for name in metadata.get_all('License-File'):
        assert payload[f'{backend.DIST}/licenses/{name}']==(ROOT/name).read_bytes()
    assert all(not x.endswith(('.pyd','.so','.dll','.pkl','.npz')) for x in payload)
