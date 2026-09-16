# ---------- Etapa 1: compilar CSS con Tailwind (binario standalone, sin Node) ----------
FROM debian:bookworm-slim AS css

ARG TAILWIND_VERSION=v4.1.13
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN case "$TARGETARCH" in arm64) ARCH=arm64 ;; *) ARCH=x64 ;; esac \
    && curl -fsSL -o /usr/local/bin/tailwindcss \
       "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-${ARCH}" \
    && chmod +x /usr/local/bin/tailwindcss

WORKDIR /build
COPY tailwind ./tailwind
COPY app/templates ./app/templates
RUN tailwindcss -i tailwind/input.css -o app.css --minify


# ---------- Etapa 2: imagen final de la app ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
COPY app ./app
COPY --from=css /build/app.css ./app/static/css/app.css

COPY docker/app/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

USER appuser
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
