"""Fail-closed checks for owner-operated publication of an immutable 2.1.0 bundle.

No upload, OIDC minting, Git operation or build is implemented in this tool.
Network reads occur only in explicitly selected CI commands; unit tests are offline.
"""
from pathlib import Path, PurePosixPath
from email import policy as email_policy
from email.parser import BytesParser
import argparse
import base64
import csv
import hashlib
import io
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 40 * 1024 * 1024
INDEX = {'testpypi': 'https://test.pypi.org', 'pypi': 'https://pypi.org'}
CDN = {'testpypi': {'test-files.pythonhosted.org'}, 'pypi': {'files.pythonhosted.org'}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def config():
    p = read_json(ROOT / 'qualification/PUBLICATION_210.json')
    require(p['project'] == 'codadapt' and p['version'] == '2.1.0', 'Wrong publication contract')
    validate_release_set(p)
    return p


def validate_release_set(p):
    """The missing fourth artifact is a blocker, never an inferred checksum."""
    require(p.get('required_distribution_count') == 4, 'Exactly four distributions are required')
    rows = p.get('distributions', {})
    require(len(rows) == 4, 'HOLD: approved CPython 3.13 manylinux wheel missing; four exact distributions required')
    require(p.get('publication_set_status') == 'READY_FOUR_VERIFIED', 'Four-file publication set not verified')
    names = [Path(n).name for n in rows]
    require(len(set(names)) == 4, 'Duplicate distribution basename')
    fixed = {'codadapt-2.1.0-py3-none-any.whl',
             'codadapt-2.1.0-cp312-cp312-win_amd64.whl', 'codadapt-2.1.0.tar.gz'}
    require(fixed.issubset(names), 'Missing or replaced previously qualified distribution')
    linux = list(set(names) - fixed)
    require(len(linux) == 1 and re.fullmatch(r'codadapt-2\.1\.0-cp313-cp313-manylinux_[A-Za-z0-9_.]+\.whl', linux[0]),
            'Fourth artifact must be the genuine qualified CPython 3.13 manylinux wheel, never linux_x86_64 relabelled')
    for rel, row in rows.items():
        safe_member(rel)
        require(type(row.get('bytes')) is int and row['bytes'] > 0, 'Actual distribution size required')
        require(isinstance(row.get('SHA256'), str) and re.fullmatch('[0-9a-f]{64}', row['SHA256']), 'Actual distribution SHA256 required')
    for key in ('bundle_SHA256', 'distribution_manifest_SHA256'):
        require(isinstance(p.get(key), str) and re.fullmatch('[0-9a-f]{64}', p[key]), 'Verified four-file bundle/manifest hash required')
    e = p.get('manylinux_evidence', {})
    linux_row = next(r for n, r in rows.items() if Path(n).name == linux[0])
    require(e.get('status') == 'VERIFIED_ORIGINAL_ARTIFACT' and e.get('provenance_verified') is True,
            'Original approved Actions provenance must be verified')
    require(e.get('wheel_filename') == linux[0] and e.get('wheel_SHA256') == linux_row['SHA256'], 'Manylinux evidence binds different bytes')
    require(e.get('README_SHA256') == p['README_SHA256'], 'Manylinux README is not the final README')
    commit = e.get('approved_commit')
    require(isinstance(commit, str) and re.fullmatch('[0-9a-f]{40}', commit), 'Approved manylinux build commit required')
    require(e.get('source_commit') == commit, 'Manylinux workflow commit differs from owner-approved commit')
    require(e.get('repository') == p['repository'] and e.get('conclusion') == 'success', 'Successful approved repository run required')
    for key in ('run_id', 'run_attempt', 'artifact_id'):
        require(type(e.get(key)) is int and e[key] > 0, 'Original Actions run/attempt/artifact identification required')
    require(isinstance(e.get('qualification_receipt_SHA256'), str)
            and re.fullmatch('[0-9a-f]{64}', e['qualification_receipt_SHA256']), 'Verified original qualification receipt required')


def release_binding(p):
    validate_release_set(p)
    e = p['manylinux_evidence']
    return {'distribution_count': 4, 'manylinux_wheel_SHA256': e['wheel_SHA256'],
            'manylinux_approved_commit': e['approved_commit'],
            'manylinux_qualification_receipt_SHA256': e['qualification_receipt_SHA256']}


def safe_member(name):
    require(isinstance(name, str) and name and not PurePosixPath(name).is_absolute(), 'Absolute archive path')
    require('\\' not in name and ':' not in name and all(x not in ('', '.', '..') for x in name.rstrip('/').split('/')), 'Unsafe archive path')


def check_hash(raw, expected, label):
    require(digest(raw) == expected['SHA256'] and len(raw) == expected['bytes'], 'Hash/size mismatch: ' + label)


def check_source(p):
    approved = (ROOT / 'README.md').read_bytes()
    require(digest(approved) == p['README_SHA256'], 'README changed')
    current = read_json(ROOT / 'MANIFEST_SHA256.json')
    for manifest in (current, p['source_manifest']):
        for name, expected in manifest['files'].items():
            safe_member(name)
            file = ROOT / name
            require(file.resolve().is_relative_to(ROOT.resolve()) and not file.is_symlink(), 'Source link escape')
            check_hash(file.read_bytes(), expected, name)
    expected = set(current['files']) | {'MANIFEST_SHA256.json'}
    upload_prefix = 'qualification_runs/publication_upload/'
    actual = {f.relative_to(ROOT).as_posix() for f in ROOT.rglob('*') if f.is_file()
              and not any(x in ('.git', '__pycache__', '.pytest_cache') for x in f.relative_to(ROOT).parts)
              and not f.relative_to(ROOT).as_posix().startswith(upload_prefix)}
    require(actual == expected, 'Source file set differs from manifest')
    upload = ROOT / 'qualification_runs/publication_upload'
    if upload.exists():
        require(not upload.is_symlink() and upload.resolve().is_relative_to(ROOT.resolve()), 'Unsafe upload staging directory')
        files = expected_files(p)
        require({f.name for f in upload.iterdir()} == set(files), 'Unexpected upload staging content')
        for name, row in files.items():
            require(not (upload / name).is_symlink(), 'Upload link refused')
            check_hash((upload / name).read_bytes(), row, name)
    return approved


def metadata(raw, approved):
    m = BytesParser(policy=email_policy.default).parsebytes(raw)
    require(m['Name'] == 'codadapt' and m['Version'] == '2.1.0', 'Wrong distribution name/version')
    require(m['Description-Content-Type'] == 'text/markdown', 'Wrong description type')
    require(m.get_payload(decode=True) == approved, 'README bytes differ, including line endings')


def check_distribution(name, raw, approved, p):
    # Hash-pinned data is checked before opening inner archives.
    expected = next((r for n, r in p['distributions'].items() if Path(n).name == name), None)
    require(expected is not None, 'Unapproved distribution')
    check_hash(raw, expected, name)
    if name.endswith('.whl'):
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names = z.namelist()
            require(len(names) == len(set(names)), 'Duplicate wheel member')
            for item in names:
                safe_member(item)
            require(z.testzip() is None, 'Wheel CRC failure')
            metas = [n for n in names if n.endswith('.dist-info/METADATA')]
            require(len(metas) == 1, 'Ambiguous metadata')
            metadata(z.read(metas[0]), approved)
            records = [n for n in names if n.endswith('.dist-info/RECORD')]
            require(len(records) == 1, 'Missing RECORD')
            seen = set()
            for member, hashed, size in csv.reader(io.StringIO(z.read(records[0]).decode())):
                require(member not in seen, 'Duplicate RECORD entry')
                seen.add(member)
                body = z.read(member)
                if member == records[0]:
                    require(not hashed and not size, 'Invalid self RECORD')
                else:
                    encoded = base64.urlsafe_b64encode(hashlib.sha256(body).digest()).rstrip(b'=').decode()
                    require(hashed == 'sha256=' + encoded and int(size) == len(body), 'Invalid RECORD')
            # auditwheel may retain explicit ZIP directory entries. RECORD binds
            # every regular file, while directories have no installable payload.
            require(seen == {m.filename for m in z.infolist() if not m.is_dir()}, 'Incomplete RECORD')
    else:
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as t:
            seen, metacount = set(), 0
            for m in t:
                safe_member(m.name)
                require(m.name not in seen and (m.isfile() or m.isdir()), 'Unsafe/duplicate source member')
                seen.add(m.name)
                if m.isfile() and m.name.endswith('/PKG-INFO'):
                    metadata(t.extractfile(m).read(), approved)
                    metacount += 1
                if m.isfile() and m.name.count('/') == 1 and m.name.endswith('/README.md'):
                    require(t.extractfile(m).read() == approved, 'Source README mismatch')
            require(metacount >= 1, 'Source metadata missing')


def stage(path):
    path = path.resolve()
    require(not path.is_relative_to(ROOT.resolve()), 'Outputs must be outside the source repository')
    path.mkdir(parents=True, exist_ok=True)
    return path


def prepare(directory, p):
    validate_release_set(p)
    approved = check_source(p)
    directory = stage(directory)
    raw = (directory / 'bundle.zip').read_bytes()
    require(digest(raw) == p['bundle_SHA256'], 'Wrong immutable release bundle')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        allowed = set(p['distributions']) | {'DISTRIBUTIONS_SHA256.json'}
        require(len(entries) == len(allowed) and {e.filename for e in entries} == allowed, 'Incomplete/extra bundle files')
        for e in entries:
            safe_member(e.filename)
            require(not e.is_dir() and not (e.flag_bits & 1) and not stat.S_ISLNK(e.external_attr >> 16), 'Unsafe bundle member')
        require(z.testzip() is None, 'Bundle CRC failure')
        require(digest(z.read('DISTRIBUTIONS_SHA256.json')) == p['distribution_manifest_SHA256'], 'Distribution manifest changed')
        dist = directory / 'dist'
        dist.mkdir(exist_ok=True)
        for rel in p['distributions']:
            name = Path(rel).name
            data = z.read(rel)
            check_distribution(name, data, approved, p)
            target = dist / name
            if target.exists():
                require(target.read_bytes() == data, 'Existing staged file differs')
            else:
                target.write_bytes(data)
        require({f.name for f in dist.iterdir()} == {Path(n).name for n in p['distributions']}, 'Extra staged upload file')
    return dist


def upload_set(directory, p):
    dist = prepare(directory, p)
    target = ROOT / 'qualification_runs/publication_upload'
    require(not target.exists(), 'Upload set must be fresh; never replace existing files')
    parent = target.parent
    require(not parent.is_symlink() and parent.resolve().is_relative_to(ROOT.resolve()), 'Unsafe upload staging parent')
    target.mkdir(parents=True)
    for name, row in expected_files(p).items():
        raw = (dist / name).read_bytes()
        check_hash(raw, row, name)
        with (target / name).open('xb') as f:
            f.write(raw)
    check_source(p)


class CheckedRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts):
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        u = urllib.parse.urlsplit(newurl)
        require(u.scheme == 'https' and u.hostname in self.hosts and u.port in (None, 443) and not u.username and not u.password, 'Unsafe redirect')
        require(not req.has_header('Authorization'), 'Authenticated API redirect refused')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def get(url, hosts, token=None, absent=False):
    u = urllib.parse.urlsplit(url)
    require(u.scheme == 'https' and u.hostname in hosts and u.port in (None, 443) and not u.username and not u.password, 'Unsafe URL')
    headers = {'User-Agent': 'CodAdapt-publication-guard/2.1.0', 'Accept': 'application/json'}
    if token:
        require(u.hostname == 'api.github.com', 'Credential destination refused')
        headers['Authorization'] = 'Bearer ' + token
        headers['X-GitHub-Api-Version'] = '2022-11-28'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), CheckedRedirect(hosts))
    try:
        with opener.open(urllib.request.Request(url, headers=headers), timeout=45) as response:
            raw = response.read(MAX_BYTES + 1)
            require(len(raw) <= MAX_BYTES, 'Oversized response')
            return raw
    except urllib.error.HTTPError as error:
        if absent and error.code == 404:
            return None
        raise RuntimeError('Remote check failed with HTTP ' + str(error.code)) from None


def gh(path):
    token = os.environ.get('GH_TOKEN')
    require(bool(token), 'Read-only Actions token required inside CI')
    return json.loads(get('https://api.github.com' + path, {'api.github.com'}, token=token))


def validate_environment(doc, channel, p):
    require(doc.get('name') == p['environments'][channel], 'Existing environment not found')
    if channel == 'pypi':
        rules = [r for r in doc.get('protection_rules', []) if r.get('type') == 'required_reviewers']
        require(len(rules) == 1, 'pypi requires manual approval configured in GitHub')
        reviewers = rules[0].get('reviewers', [])
        require(len(reviewers) == 1 and reviewers[0].get('type') == 'User'
                and reviewers[0].get('reviewer', {}).get('login') == p['owner'], 'Only owner approval may release')
        require(doc.get('can_admins_bypass') is False, 'Disable administrative protection bypass on existing pypi environment')
        require(rules[0].get('prevent_self_review') is False, 'Owner-triggered run needs owner approval; self-review setting prevents it')


def gate(channel, p):
    validate_release_set(p)
    check_source(p)
    e = os.environ
    require(e.get('GITHUB_EVENT_NAME') == 'workflow_dispatch', 'Manual dispatch only')
    require(e.get('GITHUB_REPOSITORY') == p['repository'] and e.get('GITHUB_REF') == 'refs/heads/' + p['branch'], 'Wrong repository/ref')
    require(e.get('GITHUB_ACTOR') == p['owner'] and e.get('GITHUB_TRIGGERING_ACTOR') == p['owner'], 'Owner must start this operation')
    expected_ref = p['repository'] + '/.github/workflows/' + p['workflow_files'][channel] + '@refs/heads/' + p['branch']
    require(e.get('GITHUB_WORKFLOW_REF') == expected_ref, 'Workflow filename/ref does not match approved plan')
    require(e.get('TRUSTED_PUBLISHER_CONFIRMED') == 'true', 'Owner must verify existing registered workflow filenames first')
    expected_approval = ('TEST' if channel == 'testpypi' else 'PUBLISH') + ' codadapt 2.1.0'
    require(e.get('OWNER_APPROVAL') == expected_approval, 'Explicit owner approval phrase required')
    doc = gh('/repos/' + p['repository'] + '/environments/' + channel)
    validate_environment(doc, channel, p)


def fetch(directory, p):
    url = os.environ['BUNDLE_URL']
    u = urllib.parse.urlsplit(url)
    require(u.hostname == 'github.com' and not u.query and not u.fragment, 'Use a public GitHub attachment/release URL without credentials')
    valid = u.path.startswith('/' + p['repository'] + '/releases/download/') or re.fullmatch(r'/user-attachments/files/\d+/[^/]+\.zip', u.path)
    require(bool(valid), 'Owner-staged public ZIP URL required')
    hosts = {'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com', 'github-production-release-asset-2e65be.s3.amazonaws.com', 'github-production-user-asset-6210df.s3.amazonaws.com'}
    raw = get(url, hosts)
    require(digest(raw) == p['bundle_SHA256'], 'Downloaded bundle is not the qualified bytes')
    target = stage(directory) / 'bundle.zip'
    require(not target.exists(), 'Refusing to overwrite staged bundle')
    target.write_bytes(raw)
    prepare(directory, p)


def expected_files(p):
    validate_release_set(p)
    return {Path(n).name: {'SHA256': r['SHA256'], 'bytes': r['bytes']} for n, r in p['distributions'].items()}


def classify_index(doc, p):
    if doc is None:
        return 'EMPTY'
    require(doc.get('info', {}).get('name', '').lower() == 'codadapt' and doc['info'].get('version') == '2.1.0', 'Wrong index release')
    urls = doc.get('urls', [])
    by_name = {r['filename']: r for r in urls}
    require(len(by_name) == len(urls), 'Duplicate index filename')
    expected = expected_files(p)
    require(set(by_name) == set(expected), 'Partial or unexpected existing release: stop for owner review')
    for n, r in expected.items():
        remote = by_name[n]
        require(remote.get('digests', {}).get('sha256') == r['SHA256'] and remote.get('size') == r['bytes'], 'Existing release differs; never overwrite/relabel')
        require(not remote.get('yanked', False), 'Yanked release cannot be promoted')
    return 'COMPLETE_IDENTICAL'


def output(name, value):
    require(re.fullmatch(r'[a-z_]+', name) and '\n' not in str(value), 'Unsafe output')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
            f.write(name + '=' + str(value) + '\n')


def index(channel, directory, phase, p):
    prepare(directory, p)
    # The project must already exist; this tool cannot create one.
    project = json.loads(get(INDEX[channel] + '/pypi/codadapt/json', {urllib.parse.urlsplit(INDEX[channel]).hostname}))
    require(project.get('info', {}).get('name', '').lower() == 'codadapt', 'Existing project required')
    doc = None
    for attempt in range(6 if phase == 'post' else 1):
        raw = get(INDEX[channel] + '/pypi/codadapt/2.1.0/json', {urllib.parse.urlsplit(INDEX[channel]).hostname}, absent=True)
        doc = json.loads(raw) if raw is not None else None
        try:
            state = classify_index(doc, p)
            if phase == 'pre' or state == 'COMPLETE_IDENTICAL':
                break
        except ValueError:
            if phase != 'post' or attempt == 5:
                raise
        if phase == 'post' and attempt < 5:
            time.sleep(5)
    state = classify_index(doc, p)
    if phase == 'pre':
        output('needs_upload', 'true' if state == 'EMPTY' else 'false')
        return state
    require(state == 'COMPLETE_IDENTICAL', 'Release absent/incomplete after upload')
    approved = (ROOT / 'README.md').read_bytes()
    target = stage(directory) / 'index_downloads' / channel
    target.mkdir(parents=True, exist_ok=True)
    for row in doc['urls']:
        name = row['filename']
        raw = get(row['url'], CDN[channel])
        check_distribution(name, raw, approved, p)
        file = target / name
        if file.exists():
            require(file.read_bytes() == raw, 'Downloaded file differs')
        else:
            file.write_bytes(raw)
    receipt = {'status': state, 'channel': channel, 'files': expected_files(p), 'README_SHA256': p['README_SHA256'],
               **release_binding(p)}
    receipt_path = stage(directory) / ('INDEX_' + channel + '.json')
    if receipt_path.exists():
        require(read_json(receipt_path) == receipt, 'Index receipt changed')
    else:
        write_json(receipt_path, receipt)
    return state


def validate_run(doc, run_id, p):
    require(str(doc.get('id')) == str(run_id) and doc.get('status') == 'completed' and doc.get('conclusion') == 'success', 'TestPyPI run must be successfully completed')
    require(doc.get('event') == 'workflow_dispatch' and doc.get('path') == '.github/workflows/publish-testpypi.yml', 'Wrong TestPyPI workflow/event')
    require(doc.get('head_sha') == os.environ.get('GITHUB_SHA') and doc.get('head_branch') == p['branch'], 'Promotion must use the exact tested source commit')
    require(doc.get('repository', {}).get('full_name') == p['repository'] and doc.get('head_repository', {}).get('full_name') == p['repository'], 'Foreign repository run')
    require(doc.get('actor', {}).get('login') == p['owner'] and doc.get('triggering_actor', {}).get('login') == p['owner'], 'TestPyPI run not owner-operated')
    require(type(doc.get('run_attempt')) is int and doc['run_attempt'] > 0, 'Missing attempt provenance')


def test_run(run_id, p):
    require(re.fullmatch(r'[1-9]\d*', str(run_id)), 'Numeric successful TestPyPI run ID required')
    doc = gh('/repos/' + p['repository'] + '/actions/runs/' + str(run_id))
    validate_run(doc, run_id, p)
    data = gh('/repos/' + p['repository'] + '/actions/runs/' + str(run_id) + '/artifacts?per_page=100')
    require(data.get('total_count', 0) <= 100, 'Artifact list requires explicit review')
    name = 'codadapt-210-testpypi-verified-' + str(run_id) + '-' + str(doc['run_attempt'])
    matches = [a for a in data['artifacts'] if a['name'] == name and not a.get('expired', True)]
    require(len(matches) == 1, 'Missing/ambiguous/expired successful TestPyPI receipt artifact')
    item = matches[0]
    require(item['size_in_bytes'] <= MAX_BYTES and item.get('workflow_run', {}).get('id') == int(run_id), 'Artifact provenance/size mismatch')
    output('artifact_id', int(item['id']))
    output('test_attempt', doc['run_attempt'])


def consumers(directory, p):
    require(platform.system() == 'Windows' and platform.python_version() == '3.12.10' and platform.machine().lower() in ('amd64', 'x86_64'), 'Exact qualified consumer Windows x64 Python 3.12.10 required')
    directory = stage(directory)
    require(read_json(directory / 'INDEX_testpypi.json')['status'] == 'COMPLETE_IDENTICAL', 'Download from TestPyPI first')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', PIP_CONFIG_FILE=os.devnull,
               NETRC=os.devnull, PIP_CACHE_DIR=str(directory / 'pip-cache'), TEMP=str(directory / 'tmp'), TMP=str(directory / 'tmp'))
    # No access to OIDC or API credentials from package consumer processes.
    for key in list(env):
        if 'TOKEN' in key or key.startswith('ACTIONS_ID_TOKEN'):
            env.pop(key)
    (directory / 'tmp').mkdir(exist_ok=True)
    results = {}
    for kind, file in [('pure', 'codadapt-2.1.0-py3-none-any.whl'), ('native', 'codadapt-2.1.0-cp312-cp312-win_amd64.whl')]:
        home = directory / ('consumer_' + kind)
        require(not home.exists(), 'Do not reuse an existing consumer')
        commands = [
            [sys.executable, '-I', '-B', '-m', 'venv', str(home)],
            [str(home / 'Scripts/python.exe'), '-I', '-B', '-m', 'pip', '--isolated', '--disable-pip-version-check', '--no-input', '--keyring-provider', 'disabled', 'install', '--index-url', 'https://pypi.org/simple', '--only-binary=:all:', '-r', str(ROOT / 'requirements/windows312.txt'), '-r', str(ROOT / 'requirements/external-tests.txt')],
            [str(home / 'Scripts/python.exe'), '-I', '-B', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', '--no-compile', str(directory / 'index_downloads/testpypi' / file)],
            [str(home / 'Scripts/python.exe'), '-I', '-B', '-m', 'pip', '--isolated', 'check'],
            [str(home / 'Scripts/python.exe'), '-I', '-B', str(ROOT / 'tools/native_smoke.py'), '--backend', 'python' if kind == 'pure' else 'native', '--output', str(directory / ('probe_' + kind))],
        ]
        for i, cmd in enumerate(commands):
            with (directory / (kind + '_' + str(i) + '.log')).open('xb') as log:
                subprocess.run(cmd, cwd=directory, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
        result = read_json(directory / ('probe_' + kind) / 'RESULT.json')
        require(result['status'] == 'PASS_ACTUAL_INSTALLED_BACKEND', 'Consumer failed')
        results[kind] = result
    write_json(directory / 'CONSUMERS.json', results)


def receipt(directory, p):
    prepare(directory, p)
    data = read_json(directory / 'CONSUMERS.json')
    require(set(data) == {'pure', 'native'} and data['pure']['native_calls'] == 0, 'Both real consumers required')
    native = data['native']
    require(native['native_calls'] == 200 and sum(c['exact_arrays'] for c in native['cases']) == 35, 'Native calls/parity insufficient')
    expected = next(r['native_kernel_SHA256'] for n, r in p['distributions'].items()
                    if Path(n).name == 'codadapt-2.1.0-cp312-cp312-win_amd64.whl')
    require(native['extension_SHA256'] == expected, 'Wrong installed extension')
    for r in data.values():
        require({c['task'] for c in r['cases']} == {'binary', 'multiclass', 'regression'} and r['status'] == 'PASS_ACTUAL_INSTALLED_BACKEND', 'Tasks not qualified')
    require(read_json(directory / 'INDEX_testpypi.json')['files'] == expected_files(p), 'Wrong TestPyPI files')
    write_json(directory / 'VERIFIED.json', {
        'status': 'PASS_TESTPYPI_DOWNLOAD_AND_CONSUMERS', 'repository': p['repository'],
        'workflow': 'publish-testpypi.yml', 'head_sha': os.environ['GITHUB_SHA'],
        'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': os.environ['GITHUB_RUN_ATTEMPT'],
        'bundle_SHA256': p['bundle_SHA256'], 'README_SHA256': p['README_SHA256'],
        'files': expected_files(p), 'native_calls': 200, 'exact_arrays': 35,
        'consumers': data, 'source_manifest_SHA256': p['source_manifest_SHA256'],
        **release_binding(p)})


def validate_receipt(r, run_id, attempt, p):
    expected = {'status': 'PASS_TESTPYPI_DOWNLOAD_AND_CONSUMERS', 'repository': p['repository'],
        'workflow': 'publish-testpypi.yml', 'head_sha': os.environ.get('GITHUB_SHA'),
        'run_id': str(run_id), 'run_attempt': str(attempt), 'bundle_SHA256': p['bundle_SHA256'],
        'README_SHA256': p['README_SHA256'], 'files': expected_files(p),
        'native_calls': 200, 'exact_arrays': 35, 'source_manifest_SHA256': p['source_manifest_SHA256'],
        **release_binding(p)}
    require(all(r.get(k) == v for k, v in expected.items()), 'TestPyPI receipt does not bind this promotion')


def promotion(directory, run_id, attempt, p):
    require(re.fullmatch(r'[1-9]\d*', str(attempt)), 'Missing successful attempt')
    test_run(run_id, p)
    doc = gh('/repos/' + p['repository'] + '/actions/runs/' + str(run_id))
    require(doc['run_attempt'] == int(attempt), 'TestPyPI attempt changed')
    prepare(directory, p)
    validate_receipt(read_json(directory / 'VERIFIED.json'), run_id, attempt, p)
    index('testpypi', directory, 'post', p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['contract', 'gate', 'fetch', 'prepare', 'upload-set', 'index', 'test-run', 'consumers', 'receipt', 'promotion', 'record'])
    parser.add_argument('--channel', choices=['testpypi', 'pypi'])
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--phase', choices=['pre', 'post'])
    parser.add_argument('--run-id')
    parser.add_argument('--attempt')
    args = parser.parse_args()
    p = config()
    if args.directory is not None:
        args.directory = stage(args.directory)
    if args.command == 'contract':
        validate_release_set(p)
        print(json.dumps(release_binding(p)))
    elif args.command == 'gate': gate(args.channel, p)
    elif args.command == 'fetch': fetch(args.directory, p)
    elif args.command == 'prepare': prepare(args.directory, p)
    elif args.command == 'upload-set': upload_set(args.directory, p)
    elif args.command == 'index': index(args.channel, args.directory, args.phase, p)
    elif args.command == 'test-run': test_run(args.run_id, p)
    elif args.command == 'consumers': consumers(args.directory, p)
    elif args.command == 'receipt': receipt(args.directory, p)
    elif args.command == 'promotion': promotion(args.directory, args.run_id, args.attempt, p)
    elif args.command == 'record':
        require(read_json(args.directory / ('INDEX_' + args.channel + '.json'))['status'] == 'COMPLETE_IDENTICAL', 'Post-upload verification required')
        write_json(args.directory / 'PUBLICATION.json', {'status': 'PASS_ALL_FILES_DOWNLOADED_EXACT', 'channel': args.channel,
            'files': expected_files(p), 'README_SHA256': p['README_SHA256'], 'bundle_SHA256': p['bundle_SHA256'],
            'head_sha': os.environ['GITHUB_SHA'], 'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': os.environ['GITHUB_RUN_ATTEMPT'],
            **release_binding(p)})
    print(json.dumps({'command': args.command, 'status': 'PASS_COMMAND'}))


if __name__ == '__main__':
    main()
