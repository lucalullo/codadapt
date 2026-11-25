"""Offline regression tests for the manual Trusted Publishing gates."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication_guard', ROOT / 'tools/publication_guard.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


@pytest.fixture
def distributions(tmp_path):
    for name in guard.FILES:
        (tmp_path / name).write_bytes(name.encode())
    return tmp_path


def registry_doc(directory, channel='testpypi'):
    host = next(iter(guard.CDNS[channel]))
    return {'info': {'name': 'codadapt', 'version': guard.VERSION}, 'urls': [
        {'filename': name, 'size': rec['size'], 'digests': {'sha256': rec['sha256']},
         'yanked': False, 'url': f'https://{host}/{name}'}
        for name, rec in guard.distribution_files(directory).items()]}


def test_exact_or_empty_registry(distributions):
    files = guard.distribution_files(distributions)
    assert guard.classify_index(None, files) == 'EMPTY'
    assert guard.classify_index(registry_doc(distributions), files) == 'COMPLETE_IDENTICAL'


@pytest.mark.parametrize('case', ['partial', 'extra', 'duplicate', 'digest', 'size', 'yanked', 'version', 'project'])
def test_registry_refuses_unsafe_release(distributions, case):
    doc = registry_doc(distributions)
    if case == 'partial':
        doc['urls'].pop()
    elif case == 'extra':
        doc['urls'].append(dict(doc['urls'][0], filename='unexpected.whl'))
    elif case == 'duplicate':
        doc['urls'].append(doc['urls'][0])
    elif case == 'digest':
        doc['urls'][0]['digests']['sha256'] = '0' * 64
    elif case == 'size':
        doc['urls'][0]['size'] += 1
    elif case == 'yanked':
        doc['urls'][0]['yanked'] = True
    elif case == 'version':
        doc['info']['version'] = '2.1.0'
    else:
        doc['info']['name'] = 'other'
    with pytest.raises(RuntimeError):
        guard.classify_index(doc, guard.distribution_files(distributions))


def test_verified_distribution_authentication(distributions, monkeypatch):
    files = guard.distribution_files(distributions)
    for filename, key in zip(guard.FILES, ['EXPECTED_WHEEL', 'EXPECTED_SDIST']):
        monkeypatch.setenv(key, files[filename]['sha256'])
    guard.authenticate(distributions)
    (distributions / guard.FILES[0]).write_bytes(b'changed')
    with pytest.raises(RuntimeError, match='digest mismatch'):
        guard.authenticate(distributions)


def test_registry_download_checks_actual_bytes(distributions, monkeypatch):
    doc = registry_doc(distributions)
    responses = {guard.INDEXES['testpypi'] + '/pypi/codadapt/json': json.dumps({'info': {'name': 'codadapt'}}).encode(),
                 guard.INDEXES['testpypi'] + '/pypi/codadapt/2.2.0/json': json.dumps(doc).encode()}
    for row in doc['urls']:
        responses[row['url']] = (distributions / row['filename']).read_bytes()
    monkeypatch.setattr(guard, 'get', lambda url, hosts, **kwargs: responses[url])
    guard.index('testpypi', distributions, 'post')
    responses[doc['urls'][0]['url']] = b'wrong downloaded bytes'
    with pytest.raises(RuntimeError, match='Downloaded bytes differ'):
        guard.index('testpypi', distributions, 'post')


@pytest.fixture
def protected_environment():
    return {'name': 'pypi', 'can_admins_bypass': False, 'protection_rules': [
        {'type': 'required_reviewers', 'prevent_self_review': False,
         'reviewers': [{'type': 'User', 'reviewer': {'login': guard.OWNER}}]}]}


def test_original_production_environment(protected_environment):
    guard.validate_environment(protected_environment, 'pypi')
    for change in ('reviewer', 'bypass', 'self-review', 'name', 'rules'):
        doc = deepcopy(protected_environment)
        if change == 'reviewer':
            doc['protection_rules'][0]['reviewers'][0]['reviewer']['login'] = 'not-owner'
        elif change == 'bypass':
            doc['can_admins_bypass'] = True
        elif change == 'self-review':
            doc['protection_rules'][0]['prevent_self_review'] = True
        elif change == 'name':
            doc['name'] = 'testpypi'
        else:
            doc['protection_rules'] = []
        with pytest.raises(RuntimeError):
            guard.validate_environment(doc, 'pypi')


@pytest.mark.parametrize('channel', ['testpypi', 'pypi'])
def test_explicit_owner_dispatch_only(channel, protected_environment, monkeypatch):
    env = {'GITHUB_EVENT_NAME': 'workflow_dispatch', 'GITHUB_REPOSITORY': guard.REPO,
           'GITHUB_REF': 'refs/heads/main', 'GITHUB_ACTOR': guard.OWNER, 'GITHUB_TRIGGERING_ACTOR': guard.OWNER,
           'GITHUB_WORKFLOW_REF': f'{guard.REPO}/.github/workflows/publish-{channel}.yml@refs/heads/main',
           'PUBLISH_CONFIRMED': 'true', 'TRUSTED_PUBLISHER_CONFIRMED': 'true',
           'OWNER_APPROVAL': ('TEST' if channel == 'testpypi' else 'PUBLISH') + ' codadapt 2.2.0'}
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(guard, 'gh', lambda path: protected_environment if channel == 'pypi' else {'name': channel})
    guard.gate(channel)
    for key, invalid in [('GITHUB_EVENT_NAME', 'push'), ('GITHUB_REF', 'refs/heads/other'),
                         ('GITHUB_ACTOR', 'someone-else'), ('GITHUB_TRIGGERING_ACTOR', 'someone-else'),
                         ('PUBLISH_CONFIRMED', 'false'), ('TRUSTED_PUBLISHER_CONFIRMED', 'false'),
                         ('OWNER_APPROVAL', ''), ('GITHUB_WORKFLOW_REF', 'wrong')]:
        monkeypatch.setenv(key, invalid)
        with pytest.raises(RuntimeError):
            guard.gate(channel)
        monkeypatch.setenv(key, env[key])


def test_promotion_requires_matching_completed_run_and_artifact(monkeypatch, tmp_path):
    sha = 'a' * 40
    doc = {'id': 123, 'status': 'completed', 'conclusion': 'success', 'event': 'workflow_dispatch',
           'path': '.github/workflows/publish-testpypi.yml', 'head_sha': sha, 'head_branch': 'main',
           'repository': {'full_name': guard.REPO}, 'head_repository': {'full_name': guard.REPO},
           'actor': {'login': guard.OWNER}, 'triggering_actor': {'login': guard.OWNER}, 'run_attempt': 1}
    jobs = {'total_count': 2, 'jobs': [{'name': name, 'conclusion': 'success'} for name in
           ['Publish verified distributions to TestPyPI', 'Verify published TestPyPI distributions']]}
    artifacts = {'total_count': 1, 'artifacts': [{'id': 456, 'name': 'codadapt-testpypi-distributions-123-1',
                 'expired': False, 'size_in_bytes': 100, 'workflow_run': {'id': 123}}]}
    monkeypatch.setenv('GITHUB_SHA', sha)
    output = tmp_path / 'output'
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    monkeypatch.setattr(guard, 'gh', lambda path: jobs if '/jobs?' in path else artifacts if '/artifacts?' in path else doc)
    guard.verify_test_run('123')
    assert output.read_text().strip() == 'artifact_id=456'
    for key, wrong in [('head_sha', 'b' * 40), ('conclusion', 'failure'), ('head_branch', 'other'),
                       ('event', 'push'), ('path', '.github/workflows/publish-pypi.yml')]:
        before = doc[key]
        doc[key] = wrong
        with pytest.raises(RuntimeError):
            guard.verify_test_run('123')
        doc[key] = before
    jobs['jobs'][0]['conclusion'] = 'skipped'
    with pytest.raises(RuntimeError, match='Missing successful job'):
        guard.verify_test_run('123')
    jobs['jobs'][0]['conclusion'] = 'success'
    artifacts['artifacts'][0]['expired'] = True
    with pytest.raises(RuntimeError, match='expired'):
        guard.verify_test_run('123')


def test_record_hashes_outputs_valid_job_keys(distributions, monkeypatch, tmp_path):
    # GITHUB_OUTPUT must be outside the distribution directory.
    output = tmp_path.parent / (tmp_path.name + "-job-output")
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    guard.record_hashes(distributions)
    hashes = dict(line.split('=', 1) for line in output.read_text().splitlines())
    assert hashes == dict(zip(('wheel_sha256', 'sdist_sha256'),
                             (rec['sha256'] for rec in guard.distribution_files(distributions).values())))
