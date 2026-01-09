#!/bin/bash
set -e

# Run dumpsterr immediately on startup
echo "Running dumpsterr on startup..."
cd /app && /usr/local/bin/python src/main.py

# Start cron in foreground
echo "Starting cron scheduler..."
cron -f
