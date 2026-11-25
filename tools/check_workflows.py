"""Verify workflows; allow only the two explicitly reviewed manual publication paths."""
from pathlib import Path
import hashlib
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
PINNED_ACTION = re.compile(r'^actions/(checkout|setup-python)@[0-9a-f]{40}$')
FORBIDDEN = re.compile(r'(?i)(twine\s+upload|pypa/gh-action-pypi-publish|gh\s+release\s+create|git\s+(push|tag)|curl\b[^\n]*--upload-file|\b(?:secrets|id-token)\b|continue-on-error\s*:\s*true)')
# Byte-level policy pins cover the complete reviewed publication workflows,
# including their verification steps, exact registry, conditions and privileges.
# An intentional future workflow revision must be separately reviewed before updating a pin.
PUBLICATION_WORKFLOWS_SHA256 = {'publish-pypi.yml': 'e2057131667136cf4fb8f7308849a469c54a16061f1dc139f05cc785fa94422c', 'publish-testpypi.yml': '8647eea14fc8368b7edc7882762f63bcc9a2c8aa16045cddfb098a13fa05222c'}


def verify_publication(path, workflow):
    if hashlib.sha256(path.read_bytes()).hexdigest() != PUBLICATION_WORKFLOWS_SHA256[path.name]:
        raise ValueError(f'Unreviewed publication workflow revision: {path.name}')
    channel = 'testpypi' if path.name == 'publish-testpypi.yml' else 'pypi'
    events = workflow.get('on', {})
    if set(events) != {'workflow_dispatch'} or events['workflow_dispatch'] not in (None, '', {}):
        raise ValueError('Publication must be manual with no additional inputs')
    jobs = workflow.get('jobs', {})
    if set(jobs) != {'verify', 'publish', 'verify_release'}:
        raise ValueError('Unexpected publishing job set')
    if jobs['publish'].get('needs') != 'verify' or jobs['verify_release'].get('needs') != ['verify','publish']:
        raise ValueError('Publication must follow successful verification')
    if jobs['publish'].get('environment', {}).get('name') != channel:
        raise ValueError('Wrong publishing environment')
    for job_name, job in jobs.items():
        if job_name != 'publish' and job.get('permissions', {}).get('id-token') is not None:
            raise ValueError('OIDC outside publishing job')
    if jobs['publish'].get('permissions') != {'contents':'read','actions':'read','id-token':'write'}:
        raise ValueError('Unexpected OIDC job permissions')
    steps = [step for step in jobs['publish']['steps'] if step.get('uses','').startswith('pypa/gh-action-pypi-publish@')]
    endpoint = 'https://test.pypi.org/legacy/' if channel == 'testpypi' else 'https://upload.pypi.org/legacy/'
    if len(steps) != 1 or steps[0].get('with', {}).get('repository-url') != endpoint:
        raise ValueError('Wrong publication endpoint')
    return {'workflow':path.name,'jobs':len(jobs),'permissions':'contents:read; verification actions:read; isolated publication id-token:write','publishing_steps':1}


def verify():
    records = []
    expected = {'ci.yml','native-complete.yml','native-platform-r3.yml','native-release-linux.yml',
                'qualification.yml',*PUBLICATION_WORKFLOWS_SHA256}
    paths = sorted((ROOT / '.github/workflows').iterdir())
    actual = {path.name for path in paths if path.suffix in {'.yml','.yaml'}}
    if actual != expected:
        raise ValueError('Expected all seven reviewed workflows, without additions')
    for path in paths:
        if path.name not in expected:
            continue
        text = path.read_text(encoding='utf-8')
        workflow = yaml.load(text, Loader=yaml.BaseLoader)
        if not isinstance(workflow, dict):
            raise ValueError(f'Invalid workflow: {path.name}')
        if workflow.get('permissions') != {'contents':'read'}:
            raise ValueError(f'Unexpected workflow permissions: {path.name}')
        if path.name in PUBLICATION_WORKFLOWS_SHA256:
            records.append(verify_publication(path, workflow))
            continue
        if FORBIDDEN.search(text):
            raise ValueError(f'Unsafe command or privilege: {path.name}')
        events = workflow.get('on')
        if not isinstance(events, dict) or not events or not set(events) <= {'push','pull_request','workflow_dispatch'}:
            raise ValueError(f'Unexpected events: {path.name}')
        if 'tags' in (events.get('push') or {}):
            raise ValueError('Tag triggers are not part of verification')
        jobs = workflow.get('jobs', {})
        if not jobs:
            raise ValueError('Workflow without checks')
        for job in jobs.values():
            if 'permissions' in job or 'secrets' in job or 'if' in job:
                raise ValueError(f'Unreviewed job override: {path.name}')
            commands = []
            for step in job.get('steps', []):
                if 'if' in step or 'continue-on-error' in step:
                    raise ValueError(f'Conditional or ignored check: {path.name}')
                if 'uses' in step:
                    if not PINNED_ACTION.fullmatch(step['uses']):
                        raise ValueError('Action must be reviewed and SHA-pinned')
                    if '/checkout@' in step['uses'] and step.get('with', {}).get('persist-credentials') != 'false':
                        raise ValueError('Checkout must not retain credentials')
                commands.append(step.get('run', ''))
            joined = '\n'.join(commands)
            for required in ('tools/verify_repository.py','tools/check_workflows.py','python -m build','twine','pytest','pip','check'):
                if required not in joined:
                    raise ValueError(f'Missing mandatory {required} in {path.name}')
        records.append({'workflow':path.name,'jobs':len(jobs),'permissions':'contents:read','publishing_steps':0})
    print(json.dumps({'status':'PASS_STATIC_WORKFLOW_POLICY','workflows':records,'hosted_execution':'NOT_PERFORMED'},indent=2))


if __name__ == '__main__':
    verify()
