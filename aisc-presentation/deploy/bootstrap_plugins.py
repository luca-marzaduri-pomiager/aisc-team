"""Download, install and validate each default plugin independently at startup.

Only runtime volumes receive downloaded code, wheels and virtual environments.
One plugin failure is reported and does not prevent other plugins from loading.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib

ROOT = Path('/plugin-runtime')
ACTIVE = Path('/app/plugins')
ROOT.mkdir(parents=True, exist_ok=True)
ACTIVE.mkdir(parents=True, exist_ok=True)
manifest = json.loads(Path('/deploy/plugins.json').read_text())
results = []

def run(arguments, **kwargs):
    print('+', ' '.join(map(str, arguments)), flush=True)
    return subprocess.run(list(map(str, arguments)), check=True, timeout=2400, **kwargs)

def publish():
    temporary = ROOT / 'status.tmp'
    temporary.write_text(json.dumps({'plugins': results}, indent=2))
    temporary.replace(ROOT / 'status.json')

for item in manifest:
    plugin_id = item['id']
    result = {**item, 'status': 'installing'}
    results.append(result)
    publish()
    folder = 'aisc-plugin-' + plugin_id
    source = ROOT / 'sources' / folder
    environment = ROOT / 'envs' / folder
    python = environment / 'bin/python'
    target = ACTIVE / folder
    signature = hashlib.sha256((json.dumps(item, sort_keys=True) + sys.version + 'bootstrap-v1').encode()).hexdigest()
    marker = environment / 'ready.json'
    try:
        if marker.exists() and python.exists() and (target / 'pyproject.toml').exists() and json.loads(marker.read_text()).get('signature') == signature:
            result.update(json.loads(marker.read_text()))
            print('Using verified plugin:', plugin_id, flush=True)
            continue
        if target.exists():
            shutil.rmtree(target)
        if not (source / '.git').exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                shutil.rmtree(source)
            run(['git', 'clone', '--filter=blob:none', '--no-checkout', item['repository'], source])
        run(['git', '-C', source, 'checkout', '--force', item['revision']])
        project = tomllib.loads((source / 'pyproject.toml').read_text())['project']
        dependencies = []
        for dependency in project.get('dependencies', []):
            name = dependency.split('[')[0].split('>')[0].split('<')[0].split('=')[0].split('@')[0].strip()
            if name == 'aisc-plugin-interface':
                continue
            replacement = item.get('sources', {}).get(name)
            dependencies.append(f'{name} @ {replacement}' if replacement else dependency)
        # CPU wheels avoid implicitly downloading CUDA runtimes for this local demo.
        # Every plugin gets an independent environment to avoid pandas/NumPy conflicts.
        if environment.exists():
            shutil.rmtree(environment)
        run(['uv', 'venv', '--system-site-packages', environment, '--python', sys.executable])
        run(['uv', 'pip', 'install', '--python', python, '/shared/plugin-interface', '/shared/plugin-manager', *dependencies])
        run(['uv', 'pip', 'install', '--python', python, '--no-deps', source])
        validation = subprocess.run([str(python), '-c',
            'import json; from aisc_plugin_manager import Loader; '
            "l=Loader('/not-used','',''); "
            f"import importlib; m=importlib.import_module({project['name'].replace('-', '_')!r}); "
            'classes=l._extract_plugin_classes(m); instances={n:c() for n,c in classes.items()}; '
            'assert instances, "No plugin implementations"; '
            'print(json.dumps(list(instances)))'], capture_output=True, text=True, timeout=180)
        if validation.returncode:
            raise RuntimeError(validation.stderr[-4000:])
        classes = json.loads(validation.stdout.strip().splitlines()[-1])
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('.git', '.env', '.env.*', '.venv', '__pycache__', 'datasets'))
        result.update(status='ready', package=project['name'], version=project['version'], classes=classes, signature=signature)
        marker.write_text(json.dumps(result, indent=2))
        print('READY', plugin_id, ', '.join(classes), flush=True)
    except Exception as error:
        result.update(status='failed', error=str(error)[-4000:])
        print('FAILED', plugin_id, str(error), flush=True)
    finally:
        publish()

ready = sum(item['status'] == 'ready' for item in results)
print(f'Plugin bootstrap complete: {ready}/{len(results)} ready. See /plugin-status.json for failures.', flush=True)
