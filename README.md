# Flask + LaunchDarkly: Web & API Demo

A production-ready Flask application demonstrating LaunchDarkly feature flag integration with both server-side rendering and REST API endpoints.

## Features

- ✅ **Server-side flag evaluation** for web pages
- ✅ **REST API** for dynamic flag evaluation
- ✅ **Production-ready** with Gunicorn + LaunchDarkly best practices
- ✅ **Proper worker forking** with `postfork()` support

## LaunchDarkly Best Practices Implemented

This application follows all [LaunchDarkly best practices for worker-based servers](https://docs.launchdarkly.com/sdk/server-side/python):

1. **✅ Pre-fork initialization**: LD client is initialized before Gunicorn forks workers
2. **✅ postfork() reinitialization**: Each worker reinitializes the client to receive flag updates
3. **✅ Multi-threading enabled**: Workers use 2+ threads for flag updates and event delivery
4. **✅ Preload app mode**: `preload_app = True` ensures single client initialization

📖 **[Read detailed architecture documentation](LAUNCHDARKLY_ARCHITECTURE.md)** to understand how the singleton pattern, postfork(), and worker-based servers work together.

## Setup

### 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your LaunchDarkly SDK key:

```bash
cp .env.example .env
# Edit .env and add your SDK key
```

Your `.env` should contain:
```
LAUNCHDARKLY_SDK_KEY=sdk-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
LD_FLAG_KEY_WEB_BANNER=web-banner
```

### 3. Create Feature Flags in LaunchDarkly

Create these boolean flags in your LaunchDarkly project:

- **`web-banner`** - Controls the promotional banner on the home page
- **`sample-flag`** - Demo flag for API testing with different users

## Running the Application

### 🐳 Docker (Recommended - with LaunchDarkly postfork() best practice)

Docker provides the most reliable environment for LaunchDarkly's postfork() implementation:

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

The Docker setup implements **all LaunchDarkly best practices**:
- ✅ Python 3.11 with proper OpenSSL support
- ✅ `preload_app = True` - Client initialized before worker forking
- ✅ `postfork()` hook - Workers reinitialize after forking
- ✅ Multi-threading enabled (2 workers × 2 threads)

Access the app at: `http://localhost:8000`

### Local Development Mode (Flask dev server)

```bash
source venv/bin/activate
flask run
```

⚠️ **Note**: Development server is single-threaded and doesn't demonstrate worker forking.

### Local Production Mode (Gunicorn)

```bash
source venv/bin/activate
gunicorn --config gunicorn.conf.py app:app
```

⚠️ **Note**: May experience issues with postfork() on some systems (Python 3.9 + LibreSSL). Use Docker for best results.

## API Endpoints

### Web Interface
- **GET `/`** - Home page with feature flag-controlled banner

### REST API
- **GET `/api/flag/<flag_key>?user=<username>`** - Evaluate any flag for a specific user
  
  Example:
  ```bash
  # Docker
  curl "http://localhost:8000/api/flag/sample-flag?user=alice"
  
  # Flask dev server
  curl "http://localhost:5000/api/flag/sample-flag?user=alice"
  
  # Response: {"flag":"sample-flag","user":"alice","value":true}
  ```

### Health Check
- **GET `/health`** - Returns `ok` (useful for load balancers)

## Testing Flag Targeting

Try targeting different users in LaunchDarkly:

```bash
# Test user alice
curl "http://localhost:8000/api/flag/sample-flag?user=alice"

# Test user bob
curl "http://localhost:8000/api/flag/sample-flag?user=bob"
```

Toggle flags in your LaunchDarkly dashboard and see changes reflected immediately!

## Architecture Notes

### Worker-Based Server Considerations

The LaunchDarkly SDK requires special handling in worker-based servers like Gunicorn:

1. **Threads don't survive forking** - When Gunicorn forks workers, the LD client's background threads are lost
2. **Solution: postfork()** - Our `gunicorn.conf.py` calls `postfork()` after each worker forks
3. **Why preload matters** - `preload_app = True` loads the app once, then forks, ensuring consistent initialization

See `gunicorn.conf.py` for the implementation.

## Project Structure

```
flask-ld-web-and-api/
├── app.py                          # Flask application with LD integration
├── gunicorn.conf.py                # Gunicorn config with postfork() hook
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container definition
├── docker-compose.yml              # Docker Compose orchestration
├── .dockerignore                   # Docker build exclusions
├── README.md                       # Project overview (this file)
├── DOCKER_QUICKSTART.md            # Quick start guide for Docker
├── LAUNCHDARKLY_ARCHITECTURE.md    # Technical architecture deep-dive
├── templates/
│   └── index.html                  # Web page template
├── .env                            # Local environment variables (git-ignored)
├── .env.example                    # Environment template for VCS
└── .gitignore                      # Git ignore rules
```

## Troubleshooting

### Flags not updating in workers
- **Docker**: Check logs with `docker-compose logs -f` for `✓ LaunchDarkly postfork() completed` messages
- **Local**: Ensure `preload_app = True` in `gunicorn.conf.py`
- Verify threads > 1 (LD SDK needs multiple threads)

### Worker segfaults (SIGSEGV) with local Gunicorn
- This happens with some Python/LibreSSL combinations (e.g., Python 3.9 + LibreSSL 2.8.3)
- **Solution**: Use Docker (Python 3.11 + OpenSSL) which handles postfork() reliably

### Import errors
- **Docker**: Rebuild the image: `docker-compose build`
- **Local**: Make sure virtual environment is activated and run `pip install -r requirements.txt`

### Port already in use
- **Docker**: Change port in `docker-compose.yml`: `"8080:8000"`
- **Local**: Kill processes: `pkill -9 gunicorn` or `pkill -9 flask`

### Environment variables not loading
- Ensure `.env` file exists and contains your `LAUNCHDARKLY_SDK_KEY`
- **Docker**: Restart containers after updating `.env`: `docker-compose restart`

## License

MIT 