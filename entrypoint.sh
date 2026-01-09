#!/bin/bash

# Run dumpsterr immediately on startup
echo "Running dumpsterr on startup..."
cd /app

if /usr/local/bin/python -u src/main.py; then
    echo "Startup run completed successfully"
else
    echo "ERROR: Startup run failed with exit code $?"
fi

# Start supercronic in foreground (handles scheduling)
# Use -passthrough-logs to prevent wrapping each log line with cron metadata
echo "Starting cron scheduler..."
exec /usr/local/bin/supercronic -passthrough-logs /app/crontab
