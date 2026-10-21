"""Download the original default plugins and prepare their runtime environments.

Repositories and external dependencies are downloaded only into Docker volumes.
Revisions are pinned in plugins.json; a failed install blocks application startup.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tomllib

ROOT = Path('/plugin-runtime')
PLUGINS = Path('/app/plugins')
ROOT.mkdir(parents=True, exist_ok=True)
PLUGINS.mkdir(parents=True, exist_ok=True)
manifest = json.loads(Path('/deploy/plugins.json').read_text())
results = []
support_hash = hashlib.sha256(Path(__file__).read_bytes())
for path in sorted(Path('/shared').rglob('*')):
    if path.is_file() and path.suffix in ('.py', '.toml'):
        support_hash.update(path.read_bytes())


def run(arguments):
    print('+', ' '.join(map(str, arguments)), flush=True)
    subprocess.run(list(map(str, arguments)), check=True, timeout=2400)


def publish():
    temporary = ROOT / 'status.tmp'
    temporary.write_text(json.dumps({'plugins': results}, indent=2))
    temporary.replace(ROOT / 'status.json')


for item in manifest:
    folder = 'aisc-plugin-' + item['id']
    source = PLUGINS / folder
    environment = ROOT / 'envs' / folder
    python = environment / 'bin/python'
    marker = environment / 'ready.json'
    signature = hashlib.sha256((json.dumps(item, sort_keys=True) + sys.version +
                               support_hash.hexdigest()).encode()).hexdigest()
    result = {**item, 'status': 'installing'}
    results.append(result)
    publish()
    try:
        if marker.exists() and python.exists() and (source / 'pyproject.toml').exists():
            cached = json.loads(marker.read_text())
            if cached.get('signature') == signature:
                result.update(cached)
                print('Already installed:', folder, flush=True)
                continue
        marker.unlink(missing_ok=True)
        if not (source / '.git').exists():
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
        run(['uv', 'venv', '--clear', environment, '--python', sys.executable])
        run(['uv', 'pip', 'install', '--python', python,
             '/shared/plugin-interface', '/shared/plugin-manager', *dependencies])
        run(['uv', 'pip', 'install', '--python', python, '--no-deps', source])
        validation = subprocess.run([str(python), '-c',
            'import json, importlib; from aisc_plugin_manager import Loader; '
            "loader=Loader('/not-used','',''); "
            f"module=importlib.import_module({project['name'].replace('-', '_')!r}); "
            'classes=loader._extract_plugin_classes(module); '
            'instances={name:cls() for name,cls in classes.items()}; '
            'assert instances, "No plugin implementations"; '
            'print(json.dumps(list(instances)))'], capture_output=True, text=True, timeout=240)
        if validation.returncode:
            raise RuntimeError(validation.stderr[-4000:])
        result.update(status='ready', package=project['name'], version=project['version'],
                      classes=json.loads(validation.stdout.strip().splitlines()[-1]), signature=signature)
        marker.write_text(json.dumps(result, indent=2))
        print('READY:', folder, ', '.join(result['classes']), flush=True)
    except Exception as error:
        result.update(status='failed', error=str(error)[-4000:])
        print('FAILED:', folder, str(error), flush=True)
    finally:
        publish()

failed = [item['id'] for item in results if item['status'] != 'ready']
if failed:
    raise SystemExit('Plugin installation failed: ' + ', '.join(failed) +
                     '. See docker compose logs plugin-downloader.')
print(f'All {len(results)} default plugin packages installed and validated.', flush=True)
