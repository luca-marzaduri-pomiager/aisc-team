"""Manual installation into runtime volumes, never into the source repository."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

NAMES = ('performance', 'data-evaluation', 'fairness', 'langbite', 'llm-eval', 'strongreject', 'explitest')
if len(sys.argv) != 2 or sys.argv[1] not in NAMES:
    raise SystemExit('Usage: docker compose run --rm plugin-installer [' + '|'.join(NAMES) + ']')
name = 'aisc-plugin-' + sys.argv[1]
source = Path('/sources') / name
target = Path('/app/plugins') / name
project = tomllib.loads((source / 'pyproject.toml').read_text())['project']
dependencies = [d for d in project['dependencies'] if not d.startswith('aisc-plugin-interface')]
print('Installing dependencies for', name, flush=True)
# Explicit invocation by the operator; external code stays in local runtime volumes.
if dependencies:
    subprocess.run(['uv', 'pip', 'install', '--target', '/plugin-packages', *dependencies], check=True)
staging = target.with_name('.installing-' + name)
if staging.exists():
    shutil.rmtree(staging)
shutil.copytree(source, staging)
if target.exists():
    shutil.rmtree(target)
staging.rename(target)
print('Installed. Restart aisc-backend and aisc-eval-worker, then refresh the plugin list.')
