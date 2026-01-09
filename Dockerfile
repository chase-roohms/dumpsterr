# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install supercronic (cron for containers)
RUN apt-get update && \
    apt-get install -y wget && \
    wget -q https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 -O /usr/local/bin/supercronic && \
    chmod +x /usr/local/bin/supercronic && \
    apt-get remove -y wget && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -g 1000 dumpsterr && \
    useradd -u 1000 -g 1000 -m -s /bin/bash dumpsterr

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy config schema
COPY src/public/ ./src/public/

# Create data directory
RUN mkdir -p /app/data && \
    chown -R dumpsterr:dumpsterr /app

# Copy crontab file
COPY src/crontab /app/crontab
RUN chown dumpsterr:dumpsterr /app/crontab

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    chown dumpsterr:dumpsterr /app/entrypoint.sh

# Switch to non-root user
USER dumpsterr

# Set Python path so imports work correctly
ENV PYTHONPATH=/app/src

# Disable Python output buffering
ENV PYTHONUNBUFFERED=1

# Force Python to write logs to stdout/stderr immediately
ENV PYTHONIOENCODING=utf-8

# Run entrypoint script (runs app once, then starts cron)
CMD ["/bin/bash", "/app/entrypoint.sh"]
