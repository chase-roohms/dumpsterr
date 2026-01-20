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
    GOSU_VERSION=1.18

RUN set -eux; \
    apt-get update && \
    apt-get install -y curl procps ca-certificates && \
    \
    # Detect architecture
    dpkgArch="$(dpkg --print-architecture)"; \
    case "$dpkgArch" in \
        amd64) \
            supercronicArch='amd64'; \
            supercronicSha1='f70ad28d0d739a96dc9e2087ae370c257e79b8d7'; \
            gosuArch='amd64'; \
            gosuSha256='ea9eaef7f46ece76a5ce81caabd45a8e39b80cb73dd7aeb82a13b1aeab420827'; \
            ;; \
        arm64) \
            supercronicArch='arm64'; \
            supercronicSha1='44e10e33e8d98b1d1522f6719f15fb9469786ff0'; \
            gosuArch='arm64'; \
            gosuSha256='132ddfb9fcc470325d80326ce8cb7b91536520fe82637b2f96b6336ad2d350ec'; \
            ;; \
        *) echo >&2 "error: unsupported architecture: $dpkgArch"; exit 1 ;; \
    esac; \
    \
    # Install supercronic
    curl -fsSLO "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${supercronicArch}"; \
    echo "${supercronicSha1}  supercronic-linux-${supercronicArch}" | sha1sum -c -; \
    chmod +x "supercronic-linux-${supercronicArch}"; \
    mv "supercronic-linux-${supercronicArch}" /usr/local/bin/supercronic; \
    \
    # Install gosu
    curl -fsSL -o /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/${GOSU_VERSION}/gosu-${gosuArch}"; \
    echo "${gosuSha256}  /usr/local/bin/gosu" | sha256sum -c -; \
    chmod +x /usr/local/bin/gosu; \
    gosu --version; \
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
