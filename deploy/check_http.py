"""Read-only smoke test for a running stack.

Run: python deploy/check_http.py
Override AISC_PORT, AISC_TEST_PASSWORD when needed.
"""
import json
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'http://localhost:' + os.getenv('AISC_PORT', '8092')


def request(path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(BASE + path, data=body, headers=headers), timeout=240) as response:
        content = response.read()
        return json.loads(content) if 'json' in response.headers.get('Content-Type', '') else content


for path in ['/', '/controls', '/qualification', '/api/openapi.json']:
    request(path)
    print('PASS', path, flush=True)
discovery = request('/auth/realms/aisc/.well-known/openid-configuration')
assert discovery['issuer'] == BASE + '/auth/realms/aisc', discovery['issuer']
token_request = Request(discovery['token_endpoint'], data=urlencode({
    'grant_type': 'password', 'client_id': 'aisc-webapp', 'username': 'user',
    'password': os.getenv('AISC_TEST_PASSWORD', 'user'),
}).encode())
with urlopen(token_request, timeout=30) as response:
    token = json.load(response)['access_token']
print('PASS Keycloak login and public issuer', flush=True)
for path, expected in [('/api/v1/projects', (401, 403)),
                       ('/api/v1/internal/evaluations', (403,))]:
    try:
        request(path)
    except HTTPError as error:
        assert error.code in expected, (path, error.code)
    else:
        raise AssertionError('Protected path accepted an unauthenticated request: ' + path)
print('PASS API authentication and internal proxy restriction', flush=True)
packages = request('/api/v1/plugins', token=token)
expected = {'predictive-insights', 'data-monitor', 'fairness-awareness',
            'aisc-plugin-langbite', 'aisc-plugin-llm-eval',
            'aisc-plugin-strongreject', 'explitest-plugin'}
assert {p['package_name'] for p in packages} == expected, packages
print('PASS all seven default plugin packages discovered; no data created.', flush=True)
