#!/bin/bash
set -e

# Run dumpsterr immediately on startup
echo "Running dumpsterr on startup..." 2>&1
cd /app && /usr/local/bin/python -u src/main.py 2>&1 | tee -a /var/log/dumpsterr.log

# Start cron in foreground
echo "Starting cron scheduler..." 2>&1
cron -f
