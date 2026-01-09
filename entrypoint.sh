#!/bin/bash

# Run dumpsterr immediately on startup
echo "Running dumpsterr on startup..." 2>&1
cd /app

if /usr/local/bin/python -u src/main.py 2>&1 | tee -a /var/log/dumpsterr.log; then
    echo "Startup run completed successfully" 2>&1
else
    echo "ERROR: Startup run failed with exit code $?" 2>&1
    echo "Check logs above for details" 2>&1
fi

# Start cron in foreground
echo "Starting cron scheduler..." 2>&1
cron -f
