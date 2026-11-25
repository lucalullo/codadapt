"""Validate workflows; permit only the reviewed manual TestPyPI publication path."""
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
PINNED_ACTION = re.compile(r'^actions/(checkout|setup-python)@[0-9a-f]{40}$')
FORBIDDEN = re.compile(r'(?i)(twine\s+upload|pypa/gh-action-pypi-publish|gh\s+release\s+create|git\s+(push|tag)|curl\b[^\n]*--upload-file|\b(?:secrets|id-token)\b|continue-on-error\s*:\s*true)')

TEST_EVENT = {'workflow_dispatch': {'inputs': {'publish': {'description': 'Publish the verified distributions to TestPyPI '
                                                             '(not PyPI)',
                                              'type': 'boolean',
                                              'required': 'true',
                                              'default': 'false'}}}}

TEST_OUTPUTS = {'wheel_sha256': '${{ steps.package_hashes.outputs.wheel_sha256 }}',
 'sdist_sha256': '${{ steps.package_hashes.outputs.sdist_sha256 }}'}

TEST_TRAILING_STEPS = [{'name': 'Record verified distribution hashes',
  'id': 'package_hashes',
  'shell': 'python',
  'run': 'import hashlib, os\n'
         'from pathlib import Path\n'
         'expected = {"wheel_sha256": "codadapt-2.2.0-py3-none-any.whl", "sdist_sha256": '
         '"codadapt-2.2.0.tar.gz"}\n'
         'assert {p.name for p in Path("dist").iterdir()} == set(expected.values())\n'
         'with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:\n'
         '    for key, name in expected.items():\n'
         '        digest = hashlib.sha256((Path("dist") / name).read_bytes()).hexdigest()\n'
         '        print(f"{key}={digest}", file=output)\n'
         '        print(f"{digest}  {name}")\n'},
 {'name': 'Store verified distributions',
  'uses': 'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02',
  'with': {'name': 'codadapt-testpypi-distributions',
           'path': 'dist/codadapt-2.2.0-py3-none-any.whl\ndist/codadapt-2.2.0.tar.gz\n',
           'if-no-files-found': 'error',
           'retention-days': '7'}}]

TEST_PUBLISH_JOB = {'name': 'Publish verified distributions to TestPyPI',
 'needs': 'verify',
 'if': "${{ github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main' && inputs.publish == "
       'true }}',
 'runs-on': 'ubuntu-24.04',
 'timeout-minutes': '10',
 'environment': {'name': 'testpypi', 'url': 'https://test.pypi.org/project/codadapt/'},
 'permissions': {'id-token': 'write'},
 'steps': [{'name': 'Retrieve verified distributions',
            'uses': 'actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093',
            'with': {'name': 'codadapt-testpypi-distributions', 'path': 'dist'}},
           {'name': 'Authenticate distributions before publication',
            'shell': 'bash',
            'env': {'EXPECTED_WHEEL': '${{ needs.verify.outputs.wheel_sha256 }}',
                    'EXPECTED_SDIST': '${{ needs.verify.outputs.sdist_sha256 }}'},
            'run': "python3 - <<'PYCODE'\n"
                   'import hashlib, os, re\n'
                   'from pathlib import Path\n'
                   'expected = {"codadapt-2.2.0-py3-none-any.whl": os.environ["EXPECTED_WHEEL"], '
                   '"codadapt-2.2.0.tar.gz": os.environ["EXPECTED_SDIST"]}\n'
                   'assert {p.name for p in Path("dist").iterdir()} == set(expected)\n'
                   'for name, digest in expected.items():\n'
                   '    assert re.fullmatch(r"[0-9a-f]{64}", digest)\n'
                   '    assert hashlib.sha256((Path("dist") / name).read_bytes()).hexdigest() == digest, '
                   'name\n'
                   'PYCODE\n'},
           {'name': 'Publish to TestPyPI using Trusted Publishing',
            'uses': 'pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086',
            'with': {'repository-url': 'https://test.pypi.org/legacy/'}}]}

def verify():
    records=[]
    for path in sorted((ROOT/'.github/workflows').glob('*.yml')):
        text=path.read_text(encoding='utf-8')
        # BaseLoader preserves the YAML key "on" instead of treating it as a
        # YAML 1.1 boolean. GitHub parses workflow mappings using that spelling.
        workflow=yaml.load(text, Loader=yaml.BaseLoader)
        if not isinstance(workflow,dict):raise ValueError(f'Invalid workflow: {path.name}')
        if workflow.get('permissions')!={'contents':'read'}:
            raise ValueError(f'Unexpected workflow permissions: {path.name}')
        is_test_publisher = path.name == 'publish-testpypi.yml'
        checked_workflow = workflow
        if is_test_publisher:
            # Exactly one manual opt-in, on main, with no production registry access.
            if set(workflow) != {'name','on','permissions','jobs'} or workflow.get('on') != TEST_EVENT:
                raise ValueError('Unexpected TestPyPI workflow entry points')
            if set(workflow.get('jobs',{})) != {'verify','publish'} or workflow['jobs']['publish'] != TEST_PUBLISH_JOB:
                raise ValueError('Unexpected TestPyPI publishing job or privileges')
            verify_job = workflow['jobs']['verify']
            if verify_job.get('outputs') != TEST_OUTPUTS or verify_job.get('steps',[])[-2:] != TEST_TRAILING_STEPS:
                raise ValueError('Unexpected TestPyPI distribution transfer')
            # The exception is restricted to the exact structures above. All
            # pre-existing verification steps still receive the original checks.
            import copy
            checked_workflow = copy.deepcopy(workflow)
            del checked_workflow['jobs']['publish']
            del checked_workflow['jobs']['verify']['outputs']
            checked_workflow['jobs']['verify']['steps'] = verify_job['steps'][:-2]
            text = yaml.safe_dump(checked_workflow, sort_keys=False)
        if FORBIDDEN.search(text):raise ValueError(f'Unsafe command or privilege: {path.name}')
        events=workflow.get('on')
        if not isinstance(events,dict) or not events or not set(events)<={'push','pull_request','workflow_dispatch'}:
            raise ValueError(f'Unexpected events: {path.name}')
        if 'tags' in (events.get('push') or {}):raise ValueError('Tag triggers are not part of verification')
        jobs=checked_workflow.get('jobs',{})
        if not jobs:raise ValueError('Workflow without checks')
        for job in jobs.values():
            if is_test_publisher and set(job) != {'runs-on','timeout-minutes','strategy','env','steps'}:
                raise ValueError('Unexpected TestPyPI verification job configuration')
            if 'permissions' in job or 'secrets' in job or 'if' in job:
                raise ValueError(f'Unreviewed job override: {path.name}')
            steps=job.get('steps',[])
            commands=[]
            for step in steps:
                if 'if' in step or 'continue-on-error' in step:
                    raise ValueError(f'Conditional or ignored check: {path.name}')
                if 'uses' in step:
                    if not PINNED_ACTION.fullmatch(step['uses']):raise ValueError('Action must be reviewed and SHA-pinned')
                    if '/checkout@' in step['uses'] and step.get('with',{}).get('persist-credentials')!='false':
                        raise ValueError('Checkout must not retain credentials')
                commands.append(step.get('run',''))
            joined='\n'.join(commands)
            for required in ('tools/verify_repository.py','tools/check_workflows.py','python -m build','twine','pytest','pip", "check'):
                if required not in joined:raise ValueError(f'Missing mandatory {required} in {path.name}')
        records.append({'workflow':path.name,'jobs':len(workflow['jobs']),'permissions':'contents:read; isolated TestPyPI job id-token:write' if is_test_publisher else 'contents:read','publishing_steps':1 if is_test_publisher else 0})
    if len(records)!=7:raise ValueError('Expected all seven reviewed workflows')
    print(json.dumps({'status':'PASS_STATIC_WORKFLOW_POLICY','workflows':records,'hosted_execution':'NOT_PERFORMED'},indent=2))

if __name__=='__main__':verify()
