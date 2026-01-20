#!/bin/bash
set -e

# Validate required environment variables
if [ -z "$PLEX_URL" ]; then
    echo "ERROR: PLEX_URL environment variable is not set"
    exit 1
fi

if [ -z "$PLEX_TOKEN" ]; then
    echo "ERROR: PLEX_TOKEN environment variable is not set"
    exit 1
fi

# Fix permissions for mounted volumes (runs as root)
echo "Setting up directories and permissions..."

# Ensure metrics directory exists and is owned by dumpsterr user
mkdir -p /app/metrics
chown -R dumpsterr:dumpsterr /app/metrics
chmod -R 755 /app/metrics

# Ensure data directory is accessible
if [ -d "/app/data" ]; then
    chown dumpsterr:dumpsterr /app/data
fi

echo "Permissions set. Running as dumpsterr user (UID 1000)..."

# Run dumpsterr immediately on startup
# Using -u flag for unbuffered output to ensure logs are immediately visible
echo "Running dumpsterr on startup..."
cd /app

gosu dumpsterr /usr/local/bin/python -u src/main.py
EXIT_CODE=$?

# Handle tri-state exit codes:
# 0 = Success (all libraries processed)
# 1 = Partial failure (some libraries processed successfully)
# 2 = Complete failure (no libraries processed successfully)
case $EXIT_CODE in
    0)
        echo "Startup run completed successfully - all libraries processed"
        ;;
    1)
        echo "WARNING: Startup run completed with partial failures - some libraries processed"
        echo "Continuing with cron scheduler..."
        ;;
    2)
        echo "ERROR: Startup run failed completely - no libraries processed"
        echo "Exiting to prevent starting cron scheduler with broken configuration"
        exit 2
        ;;
    *)
        echo "ERROR: Startup run failed with unexpected exit code $EXIT_CODE"
        exit 1
        ;;
esac

# Set default cron schedule if not provided (every hour at minute 0)
CRON_SCHEDULE="${CRON_SCHEDULE:-0 * * * *}"
echo "Using cron schedule: '$CRON_SCHEDULE'"

# Write the cron schedule to the crontab file
echo "$CRON_SCHEDULE cd /app && /usr/local/bin/python src/main.py" > /app/crontab

# Start supercronic in foreground (handles scheduling)
# Use -passthrough-logs to prevent wrapping each log line with cron metadata
echo "Starting cron scheduler..."
exec gosu dumpsterr /usr/local/bin/supercronic -passthrough-logs /app/crontab
