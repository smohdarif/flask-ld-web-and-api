# 🐳 Docker Quick Start Guide

This guide helps you run the Flask + LaunchDarkly app with proper **postfork() best practices** using Docker.

## Prerequisites

1. ✅ Docker Desktop installed and **running**
2. ✅ `.env` file with your `LAUNCHDARKLY_SDK_KEY`

## Steps to Run

### 1. Start Docker Desktop
- Open Docker Desktop application
- Wait for it to start (you'll see the Docker icon in your menu bar)

### 2. Build the Docker Image
```bash
docker-compose build
```

This creates a containerized environment with:
- Python 3.11 (with proper OpenSSL support)
- All dependencies pre-installed
- Optimized for LaunchDarkly postfork()

### 3. Start the Application
```bash
# Start in detached mode (background)
docker-compose up -d

# OR start with logs visible
docker-compose up
```

### 4. Verify It's Working

**Check the logs for successful postfork():**
```bash
docker-compose logs -f
```

You should see:
```
✓ LaunchDarkly postfork() completed successfully in worker 7
✓ LaunchDarkly postfork() completed successfully in worker 8
```

**Test the endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Home page
curl http://localhost:8000/

# API with different users
curl "http://localhost:8000/api/flag/sample-flag?user=alice"
curl "http://localhost:8000/api/flag/sample-flag?user=bob"
```

### 5. View in Browser
Open: http://localhost:8000

## Common Commands

```bash
# View logs
docker-compose logs -f

# Restart after code changes
docker-compose restart

# Rebuild after dependency changes
docker-compose up --build

# Stop the application
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## What's Implemented: LaunchDarkly Best Practices ✅

### 1. Pre-fork Initialization
```python
# app.py - Lines 20-21
ldclient.set_config(Config(SDK_KEY))
ld = ldclient.get()
```
Client initialized **before** Gunicorn forks workers.

### 2. Preload App in Gunicorn
```python
# gunicorn.conf.py
preload_app = True  # Ensures single client initialization
```

### 3. Postfork Hook
```python
# gunicorn.conf.py
def post_fork(server, worker):
    client = ldclient.get()
    client.postfork()  # Reinitialize threads after forking
```

### 4. Multi-threading Enabled
```python
# gunicorn.conf.py
workers = 2   # Multiple worker processes
threads = 2   # For concurrent HTTP requests
```
**Note**: LaunchDarkly SDK creates its own internal threads automatically. The `threads` setting is for HTTP concurrency, not a LaunchDarkly requirement.

## Architecture

```
┌─────────────────────────────────────┐
│      Docker Container               │
│  ┌───────────────────────────────┐ │
│  │   Gunicorn (preload_app=True)  │ │
│  │   LD Client Initialized        │ │
│  └───────────────────────────────┘ │
│              │ fork()               │
│              ├──────────┬───────────│
│     ┌────────▼────┐  ┌──▼─────────┐│
│     │  Worker 1   │  │  Worker 2  ││
│     │  postfork() │  │ postfork() ││
│     │  ✓ Threads  │  │ ✓ Threads  ││
│     │  ✓ Events   │  │ ✓ Events   ││
│     └─────────────┘  └────────────┘│
└─────────────────────────────────────┘
         Port 8000
```

## Troubleshooting

### "Cannot connect to Docker daemon"
- Start Docker Desktop application
- Check Docker icon in menu bar is running

### "Port already in use"
- Kill processes: `lsof -i :8000 | tail -n +2 | awk '{print $2}' | xargs kill -9`
- Or change port in `docker-compose.yml`

### "postfork() failed"
- Check `.env` file exists with valid SDK key
- Rebuild image: `docker-compose build --no-cache`
- Check logs: `docker-compose logs -f`

### Environment changes not reflected
```bash
# Restart after .env changes
docker-compose restart

# Rebuild after code changes
docker-compose up --build
```

## Why Docker for LaunchDarkly?

The Docker setup avoids common local issues:
- ✅ No LibreSSL vs OpenSSL conflicts
- ✅ No Python version compatibility issues
- ✅ No segmentation faults (SIGSEGV)
- ✅ Consistent behavior across all machines
- ✅ Production-ready configuration

## Production Deployment

For production, remove the volume mounts from `docker-compose.yml`:

```yaml
# Comment out these lines in docker-compose.yml
# volumes:
#   - ./app.py:/app/app.py
#   - ./templates:/app/templates
```

Then rebuild and deploy! 