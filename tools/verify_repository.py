"""Read-only verification of the delivered public files against a trusted manifest."""
from pathlib import Path, PurePosixPath
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]

def main():
    manifest=json.loads((ROOT/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
    for rel,row in manifest['files'].items():
        name=PurePosixPath(rel)
        if name.is_absolute() or ':' in rel or '\\' in rel or any(p in ('','.','..') for p in rel.split('/')):
            raise ValueError('Invalid manifest path')
        file=ROOT/rel
        if not file.resolve().is_relative_to(ROOT) or file.is_symlink():raise ValueError('Unsafe file path')
        if file.stat().st_size!=row['bytes']:raise ValueError('Different size: '+rel)
        with file.open('rb') as stream:
            digest=hashlib.sha256()
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
        if digest.hexdigest()!=row['SHA256']:raise ValueError('Different digest: '+rel)
    expected=set(manifest['files'])|{'MANIFEST_SHA256.json'}
    actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file()
        and not any(part in ('.git','.venv','__pycache__','qualification_runs','benchmark_runs') for part in p.relative_to(ROOT).parts)}
    print(json.dumps(dict(integrity='PASS',verified_files=len(manifest['files']),
        extra_files_review_required=sorted(actual-expected),publication_authorized=False),indent=2))

if __name__=='__main__':main()
