# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

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

# Create data directory for config
RUN mkdir -p /app/data

# Copy crontab file
COPY crontab /etc/cron.d/dumpsterr-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/dumpsterr-cron

# Create log file with proper permissions
RUN touch /var/log/dumpsterr.log && \
    chown dumpsterr:dumpsterr /var/log/dumpsterr.log

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set ownership of app directory
RUN chown -R dumpsterr:dumpsterr /app

# Switch to non-root user
USER dumpsterr

# Set Python path so imports work correctly
ENV PYTHONPATH=/app/src

# Disable Python output buffering
ENV PYTHONUNBUFFERED=1

# Run entrypoint script (runs app once, then starts cron)
ENTRYPOINT ["/entrypoint.sh"]
