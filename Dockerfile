# Use Python 3.12 slim image as base
# Known vulnerability: CVE-2025-45582 (MEDIUM) in Debian tar package (>=1.35+dfsg-3.1)
# - No fixed version available as of 2026-01-09
# - EPSS score: 0.00049 (0.15% exploitation probability)
# - Risk accepted: Application does not directly use tar functionality
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install supercronic (cron for containers)
# Latest releases available at https://github.com/aptible/supercronic/releases
ENV SUPERCRONIC_URL=https://github.com/aptible/supercronic/releases/download/v0.2.41/supercronic-linux-amd64 \
    SUPERCRONIC_SHA1SUM=f70ad28d0d739a96dc9e2087ae370c257e79b8d7 \
    SUPERCRONIC=supercronic-linux-amd64

RUN apt-get update && \
    apt-get install -y curl procps && \
    curl -fsSLO "$SUPERCRONIC_URL" && \
    echo "${SUPERCRONIC_SHA1SUM}  ${SUPERCRONIC}" | sha1sum -c - && \
    chmod +x "$SUPERCRONIC" && \
    mv "$SUPERCRONIC" /usr/local/bin/supercronic && \
    # Install su-exec for dropping privileges
    apt-get install -y su-exec && \
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
