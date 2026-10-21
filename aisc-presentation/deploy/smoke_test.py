"""Read-only smoke tests. Run with any Python 3.10+ after Compose is healthy."""
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

base = 'http://localhost:' + os.environ.get('AISC_PORT', '8090')
for path in ['/', '/controls', '/qualification', '/api/openapi.json', '/auth/realms/aisc/.well-known/openid-configuration', '/plugins-help']:
    with urlopen(base + path, timeout=30) as response:
        assert response.status == 200, path
    print('PASS', path)
token_request = Request(base + '/auth/realms/aisc/protocol/openid-connect/token', data=urlencode({
    'grant_type': 'password', 'client_id': 'aisc-webapp', 'username': 'demo', 'password': 'demo-presentation',
}).encode())
with urlopen(token_request, timeout=30) as response:
    token = json.load(response)['access_token']
for path in ['/api/v1/plugins', '/api/v1/projects']:
    request = Request(base + path, headers={'Authorization': 'Bearer ' + token})
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    print('PASS authenticated', path, type(data).__name__)
try:
    urlopen(base + '/api/v1/projects', timeout=10)
except HTTPError as error:
    assert error.code in (401, 403), error.code
    print('PASS unauthenticated requests rejected')
else:
    raise AssertionError('API must require authentication')
try:
    urlopen(base + '/api/v1/internal/evaluations', timeout=10)
except HTTPError as error:
    assert error.code == 403, error.code
    print('PASS internal API blocked at proxy')
else:
    raise AssertionError('Internal API must not be public')
