#!/bin/bash
set -euo pipefail
mkdir -p /opt/keycloak/data/import
# Preserve the upstream realm. Only the public origin depends on the host port.
sed 's|${API_URL_EXTERNAL}|'"$PUBLIC_URL"'|g' /tmp/realm.json > /opt/keycloak/data/import/aisc.json
exec /opt/keycloak/bin/kc.sh start-dev --import-realm --proxy-headers=xforwarded --hostname "$PUBLIC_URL/auth"
