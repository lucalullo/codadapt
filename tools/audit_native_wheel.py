"""Actual-host wheel tags, payload and static dependency inspection; no ML import."""
from pathlib import Path
import argparse,hashlib,json,platform,shutil,subprocess,sys,sysconfig,tempfile,zipfile
from packaging.tags import sys_tags
from packaging.utils import parse_wheel_filename
def main():
    p=argparse.ArgumentParser();p.add_argument('--wheel',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--backend',choices=['native','pure'],required=True);a=p.parse_args()
    name,version,build,tags=parse_wheel_filename(a.wheel.name)
    if name!='codadapt' or str(version)!='2.1.0' or not tags.intersection(set(sys_tags())):raise ValueError('Wheel ABI/platform/version not compatible with actual interpreter')
    with zipfile.ZipFile(a.wheel) as z:
        if z.testzip() is not None:raise ValueError('Corrupt wheel')
        native=[n for n in z.namelist() if n.startswith('codadapt/_native_kernel') and n.endswith(('.so','.pyd'))]
        if len(native)!=(1 if a.backend=='native' else 0):raise ValueError('Native/pure payload mismatch')
        if native and not native[0].endswith('.pyd' if sys.platform=='win32' else '.so'):raise ValueError('Wrong native binary format for actual OS')
        binary_hash=hashlib.sha256(z.read(native[0])).hexdigest() if native else None
        dependency=dict(status='NOT_APPLICABLE_PURE')
        if native:
            command={'Linux':['readelf','-h','-d'],'Darwin':['otool','-L'],'Windows':['dumpbin','/DEPENDENTS']}.get(platform.system())
            dependency=dict(status='TOOL_UNAVAILABLE',command=command)
            if command and shutil.which(command[0]):
                with tempfile.TemporaryDirectory(dir=a.output.parent) as directory:
                    binary=Path(directory)/Path(native[0]).name;binary.write_bytes(z.read(native[0]))
                    result=subprocess.run([*command,str(binary)],capture_output=True,text=True,timeout=20)
                    dependency.update(status='PASS_STATIC_INSPECTION' if result.returncode==0 else 'INSPECTION_FAILED',returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
    record=dict(status='PASS_ACTUAL_HOST_WHEEL_TAGS_AND_PAYLOAD',system=platform.system(),machine=platform.machine(),python=sys.version,SOABI=sysconfig.get_config_var('SOABI'),libc=platform.libc_ver(),tags=sorted(str(t) for t in tags),native_members=native,native_binary_SHA256=binary_hash,dependency_inspection=dependency,manylinux_qualified=False,wheel_SHA256=hashlib.sha256(a.wheel.read_bytes()).hexdigest(),scope='Static target checks only; import/nativecalls require separate smoke. Dependency output is not a manylinux certificate.')
    a.output.write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()
