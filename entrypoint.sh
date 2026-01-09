#!/bin/bash

# Run dumpsterr immediately on startup
echo "Running dumpsterr on startup..."
cd /app

if /usr/local/bin/python -u src/main.py 2>&1 | tee -a /app/logs/dumpsterr.log; then
    echo "Startup run completed successfully"
else
    echo "ERROR: Startup run failed with exit code $?"
    echo "Check logs above for details"
fi

# Start supercronic in foreground (handles scheduling)
echo "Starting cron scheduler..."
exec /usr/local/bin/supercronic /app/crontab
