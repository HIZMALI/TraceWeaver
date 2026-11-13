# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54 AS frontend
WORKDIR /build
COPY web/package.json web/package-lock.json ./web/
RUN npm --prefix web ci
COPY web/ ./web/
RUN npm --prefix web run build:public

FROM python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39 AS wheel
WORKDIR /build
COPY pyproject.toml README.md LICENSE NOTICE requirements-dev.lock ./
COPY src/ ./src/
COPY --from=frontend /build/src/traceweaver/public_static ./src/traceweaver/public_static
RUN python -m pip wheel --no-cache-dir -c requirements-dev.lock --wheel-dir /wheels .

FROM python:3.11-slim-bookworm@sha256:a83ba18aef0f865b1a4a611c2cf460fe446f2795673bbb9fe43be570439e3b39 AS runtime
LABEL org.opencontainers.image.source="https://github.com/HIZMALI/TraceWeaver"
LABEL org.opencontainers.image.licenses="Apache-2.0"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=10000
ENV TRACEWEAVER_PUBLIC_BUNDLE=/app/judge-demo
WORKDIR /app
COPY --from=wheel /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels traceweaver==0.1.0 \
    && rm -rf /wheels \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin demo
COPY examples/judge-demo/traceweaver-demo.rl examples/judge-demo/MANIFEST.json ./judge-demo/
COPY LICENSE NOTICE ./
RUN chmod 0555 /app /app/judge-demo && chmod 0444 /app/judge-demo/* /app/LICENSE /app/NOTICE
USER 10001:10001
EXPOSE 10000
CMD ["python", "-m", "traceweaver.public_server"]
