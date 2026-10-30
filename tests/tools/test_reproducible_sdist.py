"""Archive identity/content controls; no model or foreign-platform execution."""
from pathlib import Path
import hashlib,importlib.util,io,tarfile
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('normalized_sdist',ROOT/'tools/reproducible_sdist.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

def source(path,names,timestamp):
    with tarfile.open(path,'w:gz') as z:
        for name in names:
            m=tarfile.TarInfo(name);m.mtime=timestamp;m.uid=123;m.uname='irrelevant-builder';m.size=7
            z.addfile(m,io.BytesIO(b'content'))

def test_reproducibility_ignores_archive_order_builder_and_time(tmp_path):
    names=['codadapt-2.1.0/docs/usage.md','codadapt-2.1.0/pyproject.toml']
    first=tmp_path/'first.tar.gz';second=tmp_path/'second.tar.gz'
    source(first,names,1);source(second,names[::-1],100000)
    a=tmp_path/'a.tar.gz';b=tmp_path/'b.tar.gz'
    tool.normalize(first,a,1793232000);tool.normalize(second,b,1793232000)
    assert a.read_bytes()==b.read_bytes()
    with tarfile.open(a) as z:
        assert sorted(m.name for m in z)==sorted(names)
        for m in z.getmembers():assert z.extractfile(m).read()==b'content' and m.mtime==1793232000

@pytest.mark.parametrize('name',['../bad','/absolute','codadapt-2.1.0/../bad','codadapt-2.1.0/PRIVATE_CODEX/a','other-2.1.0/PKG-INFO'])
def test_unsafe_members_rejected_before_output(tmp_path,name):
    src=tmp_path/'src.tar.gz';out=tmp_path/'out.tar.gz';source(src,[name],1)
    with pytest.raises(ValueError):tool.normalize(src,out,1)
    assert not out.exists()

def test_existing_destination_preserved(tmp_path):
    src=tmp_path/'src.tar.gz';out=tmp_path/'out.tar.gz';source(src,['codadapt-2.1.0/PKG-INFO'],1);out.write_bytes(b'keep')
    with pytest.raises(ValueError):tool.normalize(src,out,1)
    assert out.read_bytes()==b'keep'
