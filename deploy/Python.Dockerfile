FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates libgomp1 && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_SYSTEM_PYTHON=1
ARG APP
WORKDIR /app
COPY apps/${APP}/pyproject.toml apps/${APP}/uv.lock ./
RUN uv export --frozen --no-dev --no-emit-project --no-hashes --no-emit-package aisc-plugin-manager --no-emit-package aisc-plugin-interface > /tmp/requirements.txt \
    && uv pip install --system -r /tmp/requirements.txt
COPY shared/plugin-interface /shared/plugin-interface
COPY shared/plugin-manager /shared/plugin-manager
RUN uv pip install --system --no-deps /shared/plugin-interface /shared/plugin-manager
COPY apps/${APP} /app
COPY deploy /deploy
RUN mkdir -p /app/plugins && if [ -f manage.py ]; then python manage.py collectstatic --noinput; fi
