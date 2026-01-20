# Observability and Logging Guide

## Overview

dumpsterr includes comprehensive observability features for monitoring application health and performance.

## Logging

### Log Formats

Two log formats are supported:

#### Standard Format (Default)
```
2026-01-20 10:30:15 - INFO - All validation checks passed for library "Movies"
```

#### JSON Format (Structured Logging)
```json
{
  "timestamp": "2026-01-20T10:30:15.123Z",
  "level": "INFO",
  "logger": "__main__",
  "message": "All validation checks passed for library \"Movies\"",
  "library_name": "Movies",
  "file_count": 1250,
  "media_count": 1200
}
```

### Configuration

Set log format via environment variable:
```yaml
environment:
  - LOG_FORMAT=json  # or 'standard' (default)
```

### Docker Log Management

#### Recommended: Docker Logging Driver

Configure log rotation in `docker-compose.yml`:

```yaml
services:
  dumpsterr:
    image: neonvariant/dumpsterr:latest
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

This limits logs to 3 files of 10MB each (30MB total).

#### Available Logging Drivers

- **json-file** (default): JSON-formatted logs with rotation
- **syslog**: Send logs to syslog server
- **journald**: systemd journal integration
- **fluentd**: Forward logs to Fluentd
- **awslogs**: Send to AWS CloudWatch
- **gcplogs**: Send to Google Cloud Logging

Example with syslog:
```yaml
logging:
  driver: "syslog"
  options:
    syslog-address: "tcp://192.168.1.100:514"
    tag: "dumpsterr"
```

#### Optional: File-Based Logging with Rotation

Enable file-based logging with automatic rotation:

```yaml
services:
  dumpsterr:
    volumes:
      - ./logs:/app/logs
    environment:
      - LOG_FILE=/app/logs/dumpsterr.log
```

This creates rotating log files:
- `dumpsterr.log` (current)
- `dumpsterr.log.1` (previous)
- `dumpsterr.log.2` (older)
- ... up to 5 backup files

Each file rotates at 10MB.

### Viewing Logs

```bash
# View live logs
docker logs -f dumpsterr

# View last 100 lines
docker logs --tail 100 dumpsterr

# View logs since timestamp
docker logs --since 2026-01-20T10:00:00 dumpsterr

# View logs for specific time range
docker logs --since 2026-01-20T10:00:00 --until 2026-01-20T11:00:00 dumpsterr
```

## Metrics Collection

### Metrics File

Metrics are automatically collected and persisted to `data/metrics.json`.

Example metrics structure:

```json
{
  "last_updated": "2026-01-20T10:30:45.123Z",
  "summary": {
    "total_runs": 24,
    "successful_runs": 20,
    "partial_runs": 3,
    "failed_runs": 1,
    "total_libraries_processed": 48,
    "total_libraries_succeeded": 45,
    "total_libraries_failed": 3
  },
  "runs": [
    {
      "start_time": "2026-01-20T10:30:15.000Z",
      "end_time": "2026-01-20T10:30:45.123Z",
      "duration_seconds": 30.12,
      "exit_code": 0,
      "libraries_total": 2,
      "libraries_successful": 2,
      "libraries_failed": 0,
      "library_details": [
        {
          "name": "Movies",
          "success": true,
          "file_count": 1250,
          "media_count": 1200,
          "threshold_percentage": 104.17,
          "error_message": null
        },
        {
          "name": "TV Shows",
          "success": true,
          "file_count": 3500,
          "media_count": 3400,
          "threshold_percentage": 102.94,
          "error_message": null
        }
      ]
    }
  ]
}
```

### Accessing Metrics

Mount the metrics directory to access metrics from the host:

```yaml
volumes:
  - ./config.yml:/app/data/config.yml:ro
  - ./metrics:/app/metrics  # Metrics directory
```

Metrics are automatically:
- Updated after each run
- Limited to last 100 runs (prevents unlimited growth)
- Include run duration, success rates, and per-library details

### Monitoring Integration

Parse `metrics/metrics.json` with monitoring tools:

**Prometheus (using file_sd_config):**
```yaml
scrape_configs:
  - job_name: 'dumpsterr'
    file_sd_configs:
      - files:
          - '/path/to/data/metrics.json'
```

**Grafana JSON Datasource:**
Point to metrics file URL and create dashboards.

**Custom Scripts:**
```bash
#!/bin/bash
# Check last run success rate
jq '.summary.successful_runs / .summary.total_runs * 100' metrics/metrics.json
```

## Exit Codes

The application uses tri-state exit codes for precise status reporting:

| Code | Status | Description |
|------|--------|-------------|
| 0 | Success | All libraries processed successfully |
| 1 | Partial | Some libraries failed, others succeeded |
| 2 | Complete Failure | No libraries processed successfully |

The entrypoint script handles these appropriately:
- Exit code **0**: Continue normal operations
- Exit code **1**: Log warning but continue (allows retry on next cron)
- Exit code **2**: Stop container to prevent repeated failures

## Health Checks

Docker health check monitors the cron process:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f supercronic > /dev/null || exit 1
```

Check health status:
```bash
docker ps  # Shows health status
docker inspect dumpsterr | jq '.[0].State.Health'
```

## Best Practices

1. **Use JSON logging** for production environments (easier parsing)
2. **Configure Docker log rotation** to prevent disk space issues
3. **Monitor metrics.json** for trends and anomalies
4. **Set appropriate log levels** (INFO for production, DEBUG for troubleshooting)
5. **Preserve data directory** across container recreations to maintain metrics history
6. **Alert on exit code 2** (complete failures require immediate attention)

## Troubleshooting

### High Log Volume

Reduce log level:
```yaml
# In config.yml
settings:
  log_level: WARNING  # or ERROR
```

### Missing Metrics

Ensure metrics directory is writable:
```bash
docker exec dumpsterr ls -la /app/metrics
docker exec dumpsterr touch /app/metrics/test.txt
```

### Log Rotation Not Working

Verify Docker logging driver configuration:
```bash
docker inspect dumpsterr | jq '.[0].HostConfig.LogConfig'
```

### Viewing Structured Logs

For JSON logs:
```bash
docker logs dumpsterr 2>&1 | jq 'select(.level=="ERROR")'
```
