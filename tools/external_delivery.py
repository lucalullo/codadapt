"""Safe package extraction and complete result collection, including failed runs."""
from pathlib import Path,PurePosixPath
import hashlib,json,stat,zipfile

def safe_extract(archive,destination,expected_sha256):
    archive=Path(archive);destination=Path(destination).resolve()
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected_sha256:raise ValueError('Untrusted package SHA256')
    if destination.exists():raise ValueError('Extraction destination must be new')
    with zipfile.ZipFile(archive) as z:
        seen=set();members=[];total=0
        for item in z.infolist():
            name=item.filename;parts=name.rstrip('/').split('/')
            if '\x00' in item.orig_filename or item.orig_filename!=name:raise ValueError('Noncanonical ZIP filename')
            if not name or ':' in name or '\\' in name or PurePosixPath(name).is_absolute() or any(p in ('','.','..') for p in parts):raise ValueError('Unsafe ZIP name')
            if stat.S_ISLNK(item.external_attr>>16) or name.casefold() in seen:raise ValueError('ZIP alias or link')
            seen.add(name.casefold());total+=item.file_size
            if total>150*1024**2:raise ValueError('ZIP expansion budget exceeded')
            target=destination.joinpath(*parts).resolve()
            if not target.is_relative_to(destination):raise ValueError('ZIP escape')
            members.append((item,target))
        destination.mkdir(parents=True)
        for item,target in members:
            if item.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(item))
    return destination

def collect_results(output,status):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    (output/'FINAL_STATUS.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    excluded={'build_env','consumer','source','restored','tmp','pip-cache','pytest-cache','pytest-tmp','__pycache__'}
    files=[p for p in output.rglob('*') if p.is_file() and not p.is_symlink() and not any(part in excluded for part in p.relative_to(output).parts) and p.name not in ('RETURN_MANIFEST.json','CODADAPT_210_EXTERNAL_RESULTS.zip')]
    manifest={p.relative_to(output).as_posix():dict(bytes=p.stat().st_size,SHA256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
    (output/'RETURN_MANIFEST.json').write_text(json.dumps(dict(files=manifest,scope='Private execution evidence; integrity not host authentication'),indent=2))
    files.append(output/'RETURN_MANIFEST.json');archive=output/'CODADAPT_210_EXTERNAL_RESULTS.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(output).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for p in files:assert z.read(p.relative_to(output).as_posix())==p.read_bytes()
    return archive
