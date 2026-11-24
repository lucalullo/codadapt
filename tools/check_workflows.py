"""Validate every workflow and reject publishing privileges or commands."""
from pathlib import Path
import json
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
PINNED_ACTION = re.compile(r'^actions/(checkout|setup-python)@[0-9a-f]{40}$')
FORBIDDEN = re.compile(r'(?i)(twine\s+upload|pypa/gh-action-pypi-publish|gh\s+release\s+create|git\s+(push|tag)|curl\b[^\n]*--upload-file|\b(?:secrets|id-token)\b|continue-on-error\s*:\s*true)')

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
        if FORBIDDEN.search(text):raise ValueError(f'Unsafe command or privilege: {path.name}')
        events=workflow.get('on')
        if not isinstance(events,dict) or not events or not set(events)<={'push','pull_request','workflow_dispatch'}:
            raise ValueError(f'Unexpected events: {path.name}')
        if 'tags' in (events.get('push') or {}):raise ValueError('Tag triggers are not part of verification')
        jobs=workflow.get('jobs',{})
        if not jobs:raise ValueError('Workflow without checks')
        for job in jobs.values():
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
        records.append({'workflow':path.name,'jobs':len(jobs),'permissions':'contents:read','publishing_steps':0})
    if len(records)!=7:raise ValueError('Expected all seven reviewed workflows')
    print(json.dumps({'status':'PASS_STATIC_WORKFLOW_POLICY','workflows':records,'hosted_execution':'NOT_PERFORMED'},indent=2))

if __name__=='__main__':verify()
