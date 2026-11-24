"""No-fit integrity and local packaging verification; standard library only."""
from pathlib import Path
from email.parser import BytesParser
import ast
import base64
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import release_backend as backend


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def csv_rows(name):
    with (ROOT / "benchmarks/data" / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def markdown_anchors(path):
    result=set()
    duplicates={}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',path.read_text(encoding='utf-8-sig'),re.M):
        heading=re.sub(r'<[^>]+>|[`*_~]','',heading).lower()
        slug=re.sub(r'[^\w\- ]','',heading).replace(' ','-')
        suffix=duplicates.get(slug,0)
        result.add(slug if suffix==0 else f'{slug}-{suffix}')
        duplicates[slug]=suffix+1
    return result


def verify():
    names = backend.source_names()
    require(not any(p.name=='__pycache__' or p.suffix=='.pyc' for p in ROOT.rglob('*') if '.git' not in p.parts and 'dist' not in p.parts), 'Generated cache in source checkout')
    manifest_path = ROOT / "release/MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))["files"]
    exclude = {"release/MANIFEST.json", "release/SHA256SUMS.txt"}
    require(set(names) - exclude == set(manifest), "Manifest membership mismatch")
    for name, receipt in manifest.items():
        data = (ROOT / name).read_bytes()
        require(len(data) == receipt["bytes"] and sha(data) == receipt["SHA256"], f"Integrity mismatch: {name}")
    require((ROOT / "release/SHA256SUMS.txt").read_text().split()[0] == sha(manifest_path.read_bytes()), "Manifest digest mismatch")
    sbom = json.loads((ROOT / "release/SBOM.json").read_text())
    sbom_files = {r['path']:r for r in sbom['source_files']}
    require(set(sbom_files) == set(manifest)-{'release/SBOM.json'}, 'SBOM membership mismatch')
    for name, rec in sbom_files.items():
        require(rec['SHA256']==manifest[name]['SHA256'] and rec['bytes']==manifest[name]['bytes'], f'SBOM hash mismatch: {name}')
    for name in names:
        if name.endswith(".py"):
            ast.parse((ROOT / name).read_text(encoding="utf-8-sig"), filename=name)
    require(not (ROOT/'PKG-INFO').exists() or (ROOT/'PKG-INFO').read_bytes()==backend.metadata_bytes(), 'Stale generated PKG-INFO')
    runtime = {name:manifest[name]['SHA256'] for name in names if name.startswith('src/codadapt/')}
    receipt = json.loads((ROOT/'qualification/REVIEW.json').read_text())
    require(runtime == receipt['revised_runtime_SHA256'], 'Revised runtime mismatch')
    # Verify all Markdown local file references without contacting external sites.
    links = 0
    for name in names:
        if not name.endswith('.md'):
            continue
        path = ROOT / name
        for dest in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8-sig')):
            target,_,anchor=dest.partition('#')
            url=urlsplit(target)
            if url.scheme:
                if url.netloc=='github.com' and url.path.startswith(('/lucalullo/codadapt/blob/main/','/lucalullo/codadapt/tree/main/')):
                    resolved=(ROOT/unquote(url.path.split('/main/',1)[1])).resolve()
                else:
                    continue
            else:
                resolved = (path.parent/unquote(target)).resolve() if target else path
            require(resolved.is_relative_to(ROOT) and resolved.exists(), f'Broken or outside link: {name}: {dest}')
            if anchor and resolved.suffix=='.md':
                require(unquote(anchor) in markdown_anchors(resolved), f'Broken Markdown anchor: {name}: {dest}')
            links += 1
    notices = json.loads((ROOT/'licenses/DEPENDENCY_NOTICE_INDEX.json').read_text())['items']
    for notice in notices:
        data = (ROOT/notice['notice_file']).read_bytes()
        require(sha(data)==notice['SHA256'] and len(data)==notice['bytes'], 'License notice mismatch')
    for task in ('binary','multiclass','regression'):
        data = (ROOT/f'tests/fixtures/{task}.pkl').read_bytes()
        require(sha(data)==(ROOT/f'tests/fixtures/{task}.sha256').read_text().strip(), 'Fixture mismatch')
    measurements = csv_rows('measurements.csv')
    pairs = csv_rows('paired_comparisons.csv')
    joint = csv_rows('joint_tradeoffs.csv')
    from collections import Counter
    require(len(measurements)==97 and len({r['dataset'] for r in measurements})==14, 'Benchmark measurement coverage mismatch')
    require(Counter(r['status'] for r in pairs)=={'exploratory_favorable':14,'inconclusive':40,'exploratory_unfavorable':29,'missing':1}, 'Paired outcomes mismatch')
    require(len(joint)==15 and len({r['dataset'] for r in joint})==6, 'Joint point coverage mismatch')
    require(len(json.loads((ROOT/'benchmarks/data/full_precision.json').read_text(encoding='utf-8'))['records'])==97, 'Aggregate precision coverage mismatch')
    require({r['comparison_id'] for r in joint}=={r['comparison_id'] for r in pairs if r.get('joint_favorable_point')=='yes'}, 'Joint point identity mismatch')
    require(len(list((ROOT/'benchmarks/figures').glob('*.svg')))==14, 'Chart coverage mismatch')
    cfg=tomllib.loads((ROOT/'pyproject.toml').read_text())
    meta=backend.metadata_bytes()
    message=BytesParser().parsebytes(meta)
    require(cfg['project']['version']==message['Version']=='2.2.0', 'Package version mismatch')
    require(cfg['project']['name']==message['Name']=='codadapt', 'Package name mismatch')
    require(message['Author']=='Luca Lullo' and message['License-Expression']=='MIT', 'Author/license metadata mismatch')
    require(meta.split(b'\n\n',1)[1]==(ROOT/'README.md').read_bytes(), 'README metadata mismatch')
    with tempfile.TemporaryDirectory(prefix='codadapt-source-check-') as temp:
        folder=Path(temp)
        first=folder/'first';second=folder/'second'
        w1=first/backend.build_wheel(first);w2=second/backend.build_wheel(second)
        require(w1.read_bytes()==w2.read_bytes(), 'Wheel reproducibility mismatch')
        s1=first/backend.build_sdist(first);s2=second/backend.build_sdist(second)
        require(s1.read_bytes()==s2.read_bytes(), 'Source reproducibility mismatch')
        with zipfile.ZipFile(w1) as wheel:
            require(wheel.testzip() is None, 'Invalid wheel ZIP')
            require(wheel.read(f'{backend.DIST}/METADATA') == meta, 'Wheel metadata mismatch')
            require(all(f'{backend.DIST}/licenses/{n}' in wheel.namelist() for n in message.get_all('License-File', [])), 'Wheel license paths mismatch')
            record=f'{backend.DIST}/RECORD'
            entries=list(csv.reader(io.StringIO(wheel.read(record).decode())))
            require(len(entries)==len(set(wheel.namelist())) and {r[0] for r in entries}==set(wheel.namelist()), 'Wheel RECORD membership mismatch')
            for name,digest,size in entries:
                if name==record:
                    require(digest==size=='', 'RECORD self-hash must be empty');continue
                data=wheel.read(name)
                expected='sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
                require(digest==expected and int(size)==len(data), f'Wheel RECORD mismatch: {name}')
            require({name:sha(wheel.read(name.removeprefix('src/'))) for name in runtime}==runtime, 'Wheel runtime mismatch')
            require(not any('__pycache__/' in n or n.endswith('.pyc') for n in wheel.namelist()), 'Cache in wheel')
        with tarfile.open(s1,'r:gz') as source:
            require({x.name for x in source.getmembers()}=={backend.SDIST+'/'+name for name in [*names, 'PKG-INFO']}, 'Sdist membership mismatch')
            require(source.extractfile(backend.SDIST+'/PKG-INFO').read() == meta, 'Sdist README metadata mismatch')
            for name in names:
                require(source.extractfile(backend.SDIST+'/'+name).read()==(ROOT/name).read_bytes(), f'Sdist content mismatch: {name}')
            source.extractall(folder/'unpacked',filter='data')
        rebuilt=folder/'rebuilt';rebuilt.mkdir()
        subprocess.run([sys.executable,'-B','tools/release_backend.py','--wheel-dir',str(rebuilt)],cwd=folder/'unpacked'/backend.SDIST,check=True,stdout=subprocess.PIPE)
        require((rebuilt/backend.NAME).read_bytes()==w1.read_bytes(), 'Wheel rebuilt from sdist differs')
        print(json.dumps({'source_files':len(names),'runtime_files':len(runtime),'local_markdown_links':links,'license_notices':len(notices),'fixture_digests':3,'measurements':len(measurements),'paired_comparisons':83,'missing_pairs':1,'figures':14,'deterministic_wheel_sha256':sha(w1.read_bytes()),'deterministic_sdist_sha256':sha(s1.read_bytes()),'status':'PASS_SOURCE_AND_PACKAGING_ONLY','new_fits':0,'runtime_qualification':'NOT_PERFORMED_BY_THIS_CHECKER','publication_authorized':False},indent=2))

if __name__=='__main__':
    verify()
