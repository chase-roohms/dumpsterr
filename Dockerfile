# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

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

# Apply cron job
RUN crontab /etc/cron.d/dumpsterr-cron

# Create log file
RUN touch /var/log/dumpsterr.log

# Set Python path so imports work correctly
ENV PYTHONPATH=/app/src

# Run cron in foreground
CMD ["cron", "-f"]
