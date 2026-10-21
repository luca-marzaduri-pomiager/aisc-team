#!/bin/sh
# Presentation adaptation: inject only public frontend settings; do not log values.
set -eu
for key in APP_API_URL APP_KEYCLOAK_URL APP_CATALOG_URL APP_SHOW_PLUGIN_VISUALIZATION APP_SHOW_CELERY_TASKS; do
    value=$(printenv "$key")
    escaped=$(printf '%s' "$value" | sed 's/[&|\\]/\\&/g')
    find /usr/share/nginx/html -type f -name '*.js' -exec sed -i "s|$key|$escaped|g" '{}' +
done
