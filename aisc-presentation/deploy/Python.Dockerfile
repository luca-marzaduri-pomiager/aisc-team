# Presentation adaptation: build local libraries; no Git downloads or plugins.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates libgomp1 && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1
COPY shared /shared
RUN uv pip install --system /shared/plugin-interface /shared/plugin-manager
ARG APP
WORKDIR /app
COPY apps/${APP}/pyproject.toml /tmp/app.toml
RUN python -c "import tomllib; p=tomllib.load(open('/tmp/app.toml','rb')); print('\n'.join(d for d in p['project']['dependencies'] if not d.startswith(('aisc-plugin-interface','aisc-plugin-manager'))))" > /tmp/requirements.txt
RUN uv pip install --system -r /tmp/requirements.txt
COPY apps/${APP} /app
COPY deploy /deploy
RUN mkdir -p /app/plugins /plugin-packages && if [ -f manage.py ]; then python manage.py collectstatic --noinput; fi
ENV PYTHONPATH=/plugin-packages
