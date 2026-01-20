# Use Python 3.12 slim image as base
# Known vulnerability: CVE-2025-45582 (MEDIUM) in Debian tar package (>=1.35+dfsg-3.1)
# - No fixed version available as of 2026-01-09
# - EPSS score: 0.00049 (0.15% exploitation probability)
# - Risk accepted: Application does not directly use tar functionality
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install supercronic (cron for containers) and gosu (privilege dropping)
# Latest releases:
# - supercronic: https://github.com/aptible/supercronic/releases
# - gosu: https://github.com/tianon/gosu/releases
ENV SUPERCRONIC_VERSION=v0.2.41 \
    GOSU_VERSION=1.19

RUN set -eux; \
    apt-get update && \
    apt-get install -y curl procps ca-certificates && \
    \
    # Detect architecture (TARGETARCH from buildx, fallback to dpkg)
    if [ -n "${TARGETARCH:-}" ]; then \
        arch="$TARGETARCH"; \
    else \
        arch="$(dpkg --print-architecture)"; \
    fi; \
    case "$arch" in \
        amd64|x86_64) \
            supercronicUrl="https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-amd64"; \
            supercronicSha256='798d0f6cf11cb74109b6408c50b1222cdd7678e8e70895dcfa9c2701b4bd03d5'; \
            gosuUrl="https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-amd64"; \
            gosuSha256='52c8749d0142edd234e9d6bd5237dff2d81e71f43537e2f4f66f75dd4b243dd0'; \
            ;; \
        arm64|aarch64) \
            supercronicUrl="https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-arm64"; \
            supercronicSha256='5f8d5ed5e02734b68d2d908719297f8558c2edbeb407072f86ed024a7b6ac74e'; \
            gosuUrl="https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-arm64"; \
            gosuSha256='3a8ef022d82c0bc4a98bcb144e77da714c25fcfa64dccc57f6aba7ae47ff1a44'; \
            ;; \
        *) echo >&2 "error: unsupported architecture: $arch"; exit 1 ;; \
    esac; \
    \
    # Install supercronic
    curl -fsSL -o /usr/local/bin/supercronic "$supercronicUrl"; \
    echo "$supercronicSha256  /usr/local/bin/supercronic" | sha256sum -c -; \
    chmod +x /usr/local/bin/supercronic; \
    \
    # Install gosu
    curl -fsSL -o /usr/local/bin/gosu "$gosuUrl"; \
    echo "$gosuSha256  /usr/local/bin/gosu" | sha256sum -c -; \
    chmod +x /usr/local/bin/gosu; \
    gosu --version; \
    supercronic -version; \
    \
    # Clean up
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 dumpsterr && \
    useradd -u 1000 -g 1000 -m -s /bin/bash dumpsterr

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip to fix CVE-2025-8869
RUN pip install --no-cache-dir --upgrade "pip>=25.3"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy config schema
COPY schemas/ ./schemas/

# Create data and metrics directories
RUN mkdir -p /app/data /app/metrics && \
    chown -R dumpsterr:dumpsterr /app

# Copy crontab file
COPY src/crontab /app/crontab
RUN chown dumpsterr:dumpsterr /app/crontab

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    chown dumpsterr:dumpsterr /app/entrypoint.sh

# Note: Entrypoint runs as root to fix permissions, then switches to dumpsterr user

# Set Python path so imports work correctly
ENV PYTHONPATH=/app/src

# Disable Python output buffering
ENV PYTHONUNBUFFERED=1

# Force Python to write logs to stdout/stderr immediately
ENV PYTHONIOENCODING=utf-8

# Health check to ensure the application is responsive
# Checks if the cron process (supercronic) is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f supercronic > /dev/null || exit 1

# Run entrypoint script (runs app once, then starts cron)
CMD ["/bin/bash", "/app/entrypoint.sh"]
