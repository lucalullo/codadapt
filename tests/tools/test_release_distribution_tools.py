"""Real local tooling controls; they never qualify a Linux wheel or a model."""
from pathlib import Path
import importlib.util,json,struct,subprocess,sys,zipfile
from tempfile import TemporaryDirectory
import pytest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('elf_inspection',ROOT/'tools/inspect_elf_versions.py')
elf=importlib.util.module_from_spec(spec);spec.loader.exec_module(elf)

def test_parse_required_symbol_versions_without_loading_library():
    strings=b'\0libc.so.6\0GLIBC_2.34\0';version_offset=256+len(strings)
    data=bytearray(version_offset+32);data[:6]=b'\x7fELF\x02\x01'
    struct.pack_into('<H',data,18,62);struct.pack_into('<Q',data,40,64);struct.pack_into('<HH',data,58,64,3)
    struct.pack_into('<IIQQQQIIQQ',data,128,0,3,0,0,256,len(strings),0,0,1,0)
    struct.pack_into('<IIQQQQIIQQ',data,192,0,0x6ffffffe,0,0,version_offset,32,1,0,4,0)
    data[256:version_offset]=strings
    struct.pack_into('<HHIII',data,version_offset,1,1,1,16,0)
    struct.pack_into('<IHHII',data,version_offset+16,0,0,0,strings.index(b'GLIBC'),0)
    result=elf.inspect(data)
    assert result['machine']==62 and result['requirements']==[dict(library='libc.so.6',versions=['GLIBC_2.34'])]

@pytest.mark.parametrize('data',[b'',b'not ELF',b'\x7fELF\x01\x01'+b'\0'*60,b'\x7fELF\x02\x01'+b'\0'*58])
def test_invalid_elf_is_rejected(data):
    with pytest.raises(ValueError):elf.inspect(data)

def test_missing_actual_target_still_returns_failure_archive():
    # The tool deliberately rejects output paths inside ROOT. Pytest --basetemp
    # can be inside ROOT in CI, so this negative test needs an external temp dir.
    with TemporaryDirectory(prefix='codadapt-manylinux-negative-') as temporary:
        out=Path(temporary)/'run'
        result=subprocess.run([sys.executable,'-I','-B',str(ROOT/'tools/manylinux_release.py'),
            '--output',str(out),'--expected-python','0.0.0','--image-digest','sha256:'+'0'*64],
            capture_output=True,text=True,timeout=15)
        assert result.returncode==1
        with zipfile.ZipFile(out/'CODADAPT_210_EXTERNAL_RESULTS.zip') as z:
            state=json.loads(z.read('FINAL_STATUS.json'))
            assert state['status']=='HOLD_EXECUTION_FAILED_OR_UNAVAILABLE'
            assert state['steps']==[] and state['manylinux_qualified'] is False
