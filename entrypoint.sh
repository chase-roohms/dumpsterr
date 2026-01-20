#!/bin/bash

# Validate required environment variables
if [ -z "$PLEX_URL" ]; then
    echo "ERROR: PLEX_URL environment variable is not set"
    exit 1
fi

if [ -z "$PLEX_TOKEN" ]; then
    echo "ERROR: PLEX_TOKEN environment variable is not set"
    exit 1
fi

# Run dumpsterr immediately on startup
# Using -u flag for unbuffered output to ensure logs are immediately visible
echo "Running dumpsterr on startup..."
cd /app

if /usr/local/bin/python -u src/main.py; then
    echo "Startup run completed successfully"
else
    echo "ERROR: Startup run failed with exit code $?"
    # Exit with error code to prevent starting the cron scheduler
    exit 1
fi

# Set default cron schedule if not provided (every hour at minute 0)
CRON_SCHEDULE="${CRON_SCHEDULE:-0 * * * *}"
echo "Using cron schedule: '$CRON_SCHEDULE'"

# Write the cron schedule to the crontab file
echo "$CRON_SCHEDULE cd /app && /usr/local/bin/python src/main.py" > /app/crontab

# Start supercronic in foreground (handles scheduling)
# Use -passthrough-logs to prevent wrapping each log line with cron metadata
echo "Starting cron scheduler..."
exec /usr/local/bin/supercronic -passthrough-logs /app/crontab
