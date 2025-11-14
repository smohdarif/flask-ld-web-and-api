# Flask + LaunchDarkly: Web & API Demo

A production-ready Flask application demonstrating LaunchDarkly feature flag integration with both server-side rendering and REST API endpoints.

## Features

- ✅ **Server-side flag evaluation** for web pages
- ✅ **REST API** for dynamic flag evaluation
- ✅ **Jinja2 template helpers** for seamless flag evaluation in templates
- ✅ **Production-ready** with Gunicorn + LaunchDarkly best practices
- ✅ **Proper worker forking** with `postfork()` support
- ✅ **Idiomatic Flask extension** pattern
- ✅ **Comprehensive test coverage** including template helpers

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

Create a `.env` file with your LaunchDarkly SDK key:

```bash
# Create .env file
touch .env
# Edit .env and add your SDK key
```

Your `.env` should contain:
```
FLASK_LAUNCHDARKLY__SDK_KEY=sdk-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
FLASK_LAUNCHDARKLY__LOG_LEVEL=INFO
```

**Note**: The application uses Flask's `from_prefixed_env()` pattern, so environment variables are prefixed with `FLASK_LAUNCHDARKLY__`.

### LaunchDarkly Logging Configuration

The application supports configurable LaunchDarkly log verbosity through the `FLASK_LAUNCHDARKLY__LOG_LEVEL` environment variable:

- `DEBUG` - Most verbose, includes detailed SDK operations
- `INFO` - Standard information (default)
- `WARNING` - Warnings and errors only
- `ERROR` - Errors only
- `CRITICAL` - Critical errors only

Example usage:
```bash
# Enable debug logging for development
FLASK_LAUNCHDARKLY__LOG_LEVEL=DEBUG python3 app.py

# Reduce verbosity in production
FLASK_LAUNCHDARKLY__LOG_LEVEL=WARNING python3 app.py
```

The logging configuration integrates seamlessly with Flask's logging system, ensuring LaunchDarkly logs are properly formatted and routed through your application's logging infrastructure.

### 3. Create Feature Flags in LaunchDarkly

Create these flags in your LaunchDarkly project:

- **`sample-flag`** (boolean) - Demo flag for API testing with different users
- **`config-welcome-message`** (string) - Demo flag for template helpers on home page
- **`enable-experimental-api`** (boolean) - Gates access to the experimental API endpoint

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
- **GET `/`** - Home page showcasing LaunchDarkly Flask integration and Jinja2 template helpers

### REST API
- **GET `/api/flag/<flag_key>`** - Evaluate any flag for the current request context
  
  Example:
  ```bash
  # Docker
  curl "http://localhost:8000/api/flag/sample-flag"
  
  # Flask dev server (use different port on macOS)
  curl "http://localhost:5002/api/flag/sample-flag"
  
  # Response: {"flag":"sample-flag","value":true,"context":{"key":"...","kind":"x_ld_request"}}
  ```

- **GET `/api/beta/experimental`** - Feature-gated experimental endpoint (requires `enable-experimental-api` flag)
  
  Example:
  ```bash
  # Only accessible when enable-experimental-api flag is True
  curl "http://localhost:8000/api/beta/experimental"
  
  # Response: {"message":"Welcome to the experimental API!","status":"beta","features":["feature-1","feature-2","feature-3"]}
  ```

### Health Check
- **GET `/health`** - Returns `ok` (useful for load balancers)

## Testing Flag Targeting

The application automatically creates request contexts for each API call. To test different flag values:

```bash
# Test the sample flag
curl "http://localhost:8000/api/flag/sample-flag"

# Test the experimental API (will return 404 if flag is False)
curl "http://localhost:8000/api/beta/experimental"

# Test the welcome message flag
curl "http://localhost:8000/api/flag/config-welcome-message"
```

Toggle flags in your LaunchDarkly dashboard and see changes reflected immediately!

## Jinja2 Template Helpers

The extension automatically registers template helpers for seamless flag evaluation in Jinja2 templates:

### Available Helpers

- **`ld_variation(flag_key, default)`** - Evaluate a feature flag
- **`ld_context()`** - Get current LaunchDarkly context

### Template Usage

```jinja2
<!-- Simple flag evaluation -->
{{ ld_variation('config-welcome-message', 'hello there!') }}

<!-- Conditional rendering -->
{% if ld_variation('show-banner', False) %}
    <div class="banner">New feature!</div>
{% endif %}

<!-- Different data types -->
{{ ld_variation('theme', 'light') }}          <!-- String -->
{{ ld_variation('max-items', 10) }}          <!-- Number -->
{{ ld_variation('feature-enabled', False) }}  <!-- Boolean -->

<!-- Context information -->
{{ ld_context() }}
```

### Demo Page

Visit `/` to see the template helpers in action with the `config-welcome-message` flag.

## Flask Extension Usage

The application uses an idiomatic Flask extension pattern:

```python
# app.py
from launchdarkly import LaunchDarkly
from launchdarkly.contexts import add_context, create_request_context
from flask import request

app = Flask(__name__)

# Initialize extension with LaunchDarkly client
ld = LaunchDarkly(ldclient.get(), app)

# Add contexts to the request
@app.before_request
def build_request_context():
    add_context(create_request_context())

# Use in routes
from launchdarkly import variation, track

@app.route('/dashboard')
def dashboard():
    show_beta = variation('show-beta-features', default=False)
    track('dashboard-viewed', data={'user_type': 'premium'})
    return render_template('dashboard.html', beta=show_beta)
```

### Context Management

Context management is handled through dedicated functions in `launchdarkly.contexts`:

```python
from launchdarkly.contexts import create_request_context, add_context, replace_context, get_context
from ldclient import Context

# Create contexts
request_ctx = create_request_context()
user_ctx = Context.builder('user123').kind('user').set('email', 'user@example.com').build()

# Manage request contexts
replace_context(user_ctx)  # Replace entire context
add_context(request_ctx)   # Add to existing context (creates multi-context)

# Get current context
current_ctx = get_context()
```

The extension supports both global and per-route context building:

```python
# Global context builders (run for all requests)
@app.before_request
def build_user_context():
    if hasattr(g, 'current_user') and g.current_user:
        user_ctx = Context.builder(g.current_user.id).kind('user').set('email', g.current_user.email).build()
        add_context(user_ctx)

# Per-route context (only for specific routes)
from launchdarkly.decorators import with_context

@with_context(lambda: Context.builder('admin').kind('role').build())
def admin_route():
    if variation('admin-dashboard', False):
        return render_template('admin.html')
    abort(403)
```

### Global Tracking

The extension automatically tracks request duration and errors by default:

```python
from launchdarkly import LaunchDarkly

app = Flask(__name__)

# Automatic tracking enabled by default
ld = LaunchDarkly(ldclient.get(), app, auto_track_duration=True, auto_track_errors=True)

# Disable automatic tracking if you want manual control
ld = LaunchDarkly(ldclient.get(), app, auto_track_duration=False, auto_track_errors=False)
```

This automatically tracks:
- Request duration (`flask.response_time` events)
- Errors (`flask.error` events)

### Route-Level Tracking

For fine-grained control, use individual decorators on specific routes:

```python
from launchdarkly.decorators import track_after, track_before, require_flag

# Track request duration
@track_after('user-profile-viewed', data={'endpoint': 'user-profile'})
def get_user_profile():
    return jsonify({'user': 'data'})

# Track errors only
@track_before('api-call', data={'component': 'payment'})
def process_payment():
    return process_payment_logic()

# Feature-gated routes
@require_flag("enable-experimental-api", default=False)
def experimental_endpoint():
    return jsonify({'message': 'Experimental feature!'})

# Combine decorators
@track_after('api-call', data={'endpoint': 'user-profile'}, metric_value=1)
@require_flag("enable-v2-api", default=False)
def get_user_profile_v2():
    return jsonify({'user': 'data', 'version': 'v2'})
```

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
├── app.py                          # Flask application with LD extension
├── config.py                       # Configuration management
├── gunicorn.conf.py                # Gunicorn config with postfork() hook
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker container definition
├── docker-compose.yml              # Docker Compose orchestration
├── README.md                       # Project overview (this file)
├── ARCHITECTURE.md                 # Application architecture overview
├── DOCKER_QUICKSTART.md            # Quick start guide for Docker
├── LAUNCHDARKLY_ARCHITECTURE.md    # Technical architecture deep-dive
├── GUNICORN_FAQ.md                 # Workers, ports & architecture FAQ
├── launchdarkly/                   # LaunchDarkly Flask extension
│   ├── __init__.py                 # Extension class and core functionality
│   ├── contexts.py                 # Context builders and management
│   ├── decorators.py               # Route decorators (require_flag, track_*, etc.)
│   └── middleware.py               # Request tracking middleware
├── routes/                         # HTTP route handlers
│   ├── __init__.py                 # Blueprint registration
│   ├── api.py                      # API endpoints
│   └── web.py                      # Web routes
├── templates/                      # Jinja2 templates
│   └── demo.html                   # Home page with Jinja2 template helpers
├── tests/                          # Test suite
│   ├── conftest.py                 # Pytest configuration
│   ├── test_contexts.py            # Context management tests
│   ├── test_decorators.py          # Decorator tests
│   ├── test_launchdarkly_extension.py # Extension tests
│   ├── test_middleware.py          # Middleware tests
│   └── test_template_helpers.py    # Template helper tests
├── pytest.ini                      # Pytest configuration
├── .env                            # Local environment variables (git-ignored)
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
- Ensure `.env` file exists and contains your `FLASK_LAUNCHDARKLY__SDK_KEY`
- **Docker**: Restart containers after updating `.env`: `docker-compose restart`

## License

MIT 