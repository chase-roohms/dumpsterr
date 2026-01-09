# dumpsterr

Automated Plex trash management tool that validates filesystem state before emptying library trash. Prevents accidental deletion when using network-mounted storage.

# Quickstart
```bash
mkdir dumpsterr && cd dumpsterr
curl -fsSL https://raw.githubusercontent.com/chase-roohms/dumpsterr/refs/heads/main/docker-compose/quickstart.sh | bash
# Edit config.yml and .env
docker compose up -d
```
## Problem

When Plex runs on a different host than your media storage (NFS, SMB, etc.), network interruptions can cause mount failures. If Plex scans while mounts are down, it marks all media as deleted and removes them from your library. Re-mounting triggers a full rescan and metadata rebuild.

## Solution

dumpsterr validates filesystem state before allowing Plex to empty trash:
- Checks directory accessibility
- Verifies minimum file counts
- Confirms file count thresholds match Plex library sizes
- Only empties trash when all validations pass

## Requirements

- Plex Media Server with API access
- Docker (or Python 3.12+)
- Read access to media directories

## Configuration

Create `data/config.yml`:

```yaml
libraries:
  - name: Movies                    # Plex library name
    path: /media/movies/            # Container path to media
    min_files: 100                  # Minimum files required
    min_threshold: 90               # Minimum percentage of expected files

  - name: TV Shows
    path: /media/shows/
    min_files: 50
    min_threshold: 90

settings:
  log_level: INFO                   # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Configuration validation:
- Schema: [src/public/config.schema.yml](src/public/config.schema.yml)
- Validated on startup using jsonschema

## Docker Setup

### Environment Variables

Required:
- `PLEX_URL` - Plex server URL (e.g., `http://192.168.1.100:32400`)
- `PLEX_TOKEN` - [Get your token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)

Optional:
- `TZ` - Timezone (e.g., `America/New_York`)

### Docker Compose

```yaml
services:
  dumpsterr:
    image: neonvariant/dumpsterr:latest
    container_name: dumpsterr
    volumes:
      - ./config.yml:/app/data/config.yml:ro
      - /path/to/movies:/media/movies:ro
      - /path/to/shows:/media/shows:ro
    environment:
      - PLEX_URL=http://192.168.1.100:32400
      - PLEX_TOKEN=your_token_here
      - TZ=America/New_York
    restart: unless-stopped
```

Run:
```bash
docker compose up -d
```

### Docker CLI

```bash
docker run -d \
  --name dumpsterr \
  -v ./config.yml:/app/data/config.yml:ro \
  -v /path/to/movies:/media/movies:ro \
  -v /path/to/shows:/media/shows:ro \
  -e PLEX_URL=http://192.168.1.100:32400 \
  -e PLEX_TOKEN=your_token_here \
  -e TZ=America/New_York \
  --restart unless-stopped \
  neonvariant/dumpsterr:latest
```

## Build from Source

```bash
git clone https://github.com/chase-roohms/dumpsterr.git
cd dumpsterr
docker build -t dumpsterr .
```

## Scheduling

Runs hourly via supercronic (see [src/crontab](src/crontab)). Also executes on container startup.

To modify schedule, edit [src/crontab](src/crontab) and rebuild:
```bash
# Current: hourly
0 * * * * cd /app && /usr/local/bin/python src/main.py

# Example: every 6 hours
0 */6 * * * cd /app && /usr/local/bin/python src/main.py
```

## Validation Process

1. Directory accessibility check
2. Minimum file count verification
3. Plex library size comparison
4. Threshold percentage validation (current files / expected files > minimum threshold)
5. Trash emptying (only if all checks pass)

Validation failure exits without emptying trash.

## Logs

View logs:
```bash
docker logs dumpsterr
docker logs -f dumpsterr  # Follow mode
```

Log levels: DEBUG, INFO (default), WARNING, ERROR, CRITICAL

## Troubleshooting

### IsADirectoryError: Config file is a directory

**Error**: `IsADirectoryError: [Errno 21] Is a directory: 'data/config.yml'`

**Cause**: The config file doesn't exist on your host system. When Docker tries to mount a non-existent file, it creates a directory instead.

**Solution**:
1. Ensure the config file exists on your host at the path specified in your `docker-compose.yml`
2. If using the quickstart, the config file should be in the same directory as your `docker-compose.yml`
3. Recreate the container to remount the volume correctly:
   ```bash
   docker compose down
   docker compose up -d
   ```

**Example**: If your docker-compose.yml has:
```yaml
volumes:
  - ./config.yml:/app/data/config.yml:ro
```
Then `config.yml` must exist in the same directory as `docker-compose.yml` before running `docker compose up`.

### Container starts but nothing happens

Check that:
- `PLEX_URL` is accessible from the container
- `PLEX_TOKEN` is valid
- Media paths in `config.yml` match the container paths (not host paths)

## Plex Configuration

Disable "Empty trash automatically after every scan" in:
- Settings > Library > [Your Library] > Advanced > Scan Library

This lets dumpsterr control trash emptying on its schedule.

## Project Structure

```
src/
├── main.py              # Validation and orchestration
├── config/              # Configuration loading and validation
├── filesystem/          # Directory and file count checks
├── plex_client/         # Plex API interaction
└── public/              # JSON schema for config validation
```

## Dependencies

- PyYAML
- jsonschema
- requests

## License

See LICENSE file.