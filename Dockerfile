FROM node:24.22.3-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY index.html tsconfig.json vite.config.ts ./
COPY public/ public/
COPY src/ src/
RUN VITE_HUNTWICK_WEB=1 npm run build

FROM ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d AS uv
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS python-base

FROM python-base AS dependencies
WORKDIR /app
COPY --from=uv /uv /usr/local/bin/uv
COPY web/pyproject.toml web/uv.lock ./web/
COPY engine/pyproject.toml ./engine/
RUN uv sync --project web --locked --no-dev --no-cache --python /usr/local/bin/python

FROM python-base
WORKDIR /app
COPY --from=dependencies /app/web/.venv/ /app/web/.venv/
COPY --from=frontend --chown=10001:10001 /app/dist/ ./dist/
COPY --chown=10001:10001 engine/ ./engine/
COPY --chown=10001:10001 web/ ./web/
COPY --chown=10001:10001 LICENSE THIRD_PARTY_NOTICES.md ./
ENV PATH="/app/web/.venv/bin:${PATH}" \
    HOME=/tmp \
    PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn web.app:app --host 0.0.0.0 --port \"$PORT\" --workers 1 --no-access-log --no-proxy-headers"]
