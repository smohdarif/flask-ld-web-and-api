# Flask-Idiomatic Function-Based Approach

This branch demonstrates a Flask-idiomatic implementation of LaunchDarkly integration using **functions instead of direct SDK access**, following Flask best practices.

## Branch Comparison

This repository has two implementations:

| Branch | Approach | Use Case |
|--------|----------|----------|
| **main** | Direct SDK usage | Simple, straightforward, works great |
| **flask-idiomatic-functions** | Flask patterns with helper functions | Larger apps, better testability, Flask conventions |

Both implementations maintain **all LaunchDarkly best practices** (singleton, postfork, etc.).

---

## What's Different in This Branch?

### 1. ✅ Application Factory Pattern

**Main branch (`app.py`):**
```python
app = Flask(__name__)  # Direct instantiation
```

**This branch (`app_idiomatic.py`):**
```python
def create_app(config_name='production'):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    init_launchdarkly(app)
    register_routes(app)
    return app

app = create_app()
```

**Benefits:**
- ✅ Multiple app instances for testing
- ✅ Different configs per environment
- ✅ Better separation of concerns

---

### 2. ✅ Flask Config Object (Not `os.getenv()`)

**Main branch:**
```python
SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
flag_key = os.getenv("LD_FLAG_KEY_WEB_BANNER", "web-banner")
```

**This branch (`config.py`):**
```python
class Config:
    LAUNCHDARKLY_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY", "")
    LD_FLAG_KEY_WEB_BANNER = os.getenv("LD_FLAG_KEY_WEB_BANNER", "web-banner")

# In routes
flag_key = app.config['LD_FLAG_KEY_WEB_BANNER']
```

**Benefits:**
- ✅ Centralized configuration
- ✅ Environment-specific configs (dev/prod/test)
- ✅ Easier testing (override config easily)
- ✅ Flask convention

---

### 3. ✅ Helper Functions (Not Direct SDK Access)

**Main branch:**
```python
ld = ldclient.get()

@app.get("/")
def home():
    banner_on = ld.variation(flag_key, ctx, default=False)
```

**This branch (`launchdarkly_helpers.py`):**
```python
def evaluate_flag(flag_key, context, default=False):
    """Convenience function"""
    client = get_ld_client()
    return client.variation(flag_key, context, default)

# In routes
@app.get("/")
def home():
    banner_on = evaluate_flag(flag_key, ctx, default=False)
```

**Benefits:**
- ✅ Abstraction layer for testing
- ✅ Can add logging/metrics easily
- ✅ Centralized error handling
- ✅ Reusable across routes

---

### 4. ✅ Non-Blocking Initialization

**Main branch:**
```python
ldclient.set_config(Config(SDK_KEY))  # Uses default start_wait=5 (BLOCKS!)
ld = ldclient.get()
```

**This branch:**
```python
ld_config = Config(
    sdk_key=sdk_key,
    start_wait=0  # Non-blocking initialization
)
ldclient.set_config(ld_config)
```

**Benefits:**
- ✅ App starts instantly (no 5-second wait)
- ✅ SDK connects in background
- ✅ Early requests use defaults (graceful degradation)
- ✅ Follows LaunchDarkly best practice

Reference: [LaunchDarkly Best Practices](https://docs.launchdarkly.com/sdk/concepts/client-side-server-side#application-does-not-block-on-initialization)

---

### 5. ✅ Flask Extensions Dict

**Main branch:**
```python
ld = ldclient.get()  # Module-level variable
```

**This branch:**
```python
# Store in Flask's extensions (Flask convention)
app.extensions['launchdarkly'] = client

# Access via helper
def get_ld_client():
    return current_app.extensions.get('launchdarkly')
```

**Benefits:**
- ✅ Flask convention (like Flask-SQLAlchemy, Flask-Login)
- ✅ Proper app context handling
- ✅ Easier to inspect what's registered
- ✅ Works with Flask's application context

---

## File Structure Comparison

### Main Branch:
```
flask-ld-web-and-api/ (main branch)
├── app.py                    # Single file, direct SDK usage
└── requirements.txt
```

### This Branch:
```
flask-ld-web-and-api/ (flask-idiomatic-functions branch)
├── app_idiomatic.py          # Factory pattern, uses helpers
├── config.py                 # Flask config classes
├── launchdarkly_helpers.py   # Helper functions
└── requirements.txt
```

---

## Running This Branch

### Development:
```bash
# Using the factory with development config
python app_idiomatic.py

# Or with flask command
export FLASK_APP=app_idiomatic:create_app('development')
flask run
```

### Production with Gunicorn:
```bash
# Using factory function
gunicorn "app_idiomatic:create_app()" --config gunicorn.conf.py

# Or with Docker
docker-compose up
```

### Update `docker-compose.yml` for this branch:
Change the CMD in Dockerfile to:
```dockerfile
CMD ["gunicorn", "app_idiomatic:create_app()", "--config", "gunicorn.conf.py"]
```

---

## Testing Benefits

The function-based approach makes testing much easier:

```python
# test_app.py
import pytest
from app_idiomatic import create_app
from config import TestingConfig

@pytest.fixture
def app():
    """Create test app with testing config"""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page(client, mocker):
    """Test home page with mocked LaunchDarkly"""
    # Mock the evaluate_flag function
    mocker.patch('launchdarkly_helpers.evaluate_flag', return_value=True)
    
    response = client.get('/')
    assert response.status_code == 200
    assert b'Feature flag' in response.data

def test_api_endpoint(client, mocker):
    """Test API with mocked flag evaluation"""
    mocker.patch('launchdarkly_helpers.evaluate_flag', return_value=True)
    
    response = client.get('/api/flag/test-flag?user=alice')
    data = response.get_json()
    
    assert data['flag'] == 'test-flag'
    assert data['user'] == 'alice'
    assert data['value'] == True
```

---

## Key Differences Summary

| Feature | Main Branch | This Branch |
|---------|-------------|-------------|
| **App Creation** | Direct `Flask(__name__)` | Factory `create_app()` |
| **Configuration** | `os.getenv()` | `app.config` object |
| **LD Access** | Direct `ld.variation()` | Helper `evaluate_flag()` |
| **Initialization** | Module-level | In `init_launchdarkly()` |
| **Blocking** | Default (5sec wait) | Non-blocking (`start_wait=0`) |
| **Testability** | Harder to mock | Easy to mock helpers |
| **Flask Patterns** | Minimal | Full Flask conventions |

---

## Which Approach Should You Use?

### Use **Main Branch** if:
- ✅ Simple, single-file app
- ✅ Direct SDK usage is clear enough
- ✅ Don't need multiple environments
- ✅ Straightforward is preferred

### Use **This Branch** if:
- ✅ Larger application
- ✅ Multiple environments (dev/prod/test)
- ✅ Extensive testing needed
- ✅ Following Flask conventions important
- ✅ Team familiar with Flask patterns

---

## LaunchDarkly Best Practices (Both Branches)

Both implementations maintain:

1. ✅ **Singleton pattern** - One client instance
2. ✅ **Pre-fork initialization** - Client created before forking  
3. ✅ **postfork() hook** - Workers reinitialize (in gunicorn.conf.py)
4. ✅ **Proper Context API** - Using Context.builder()
5. ✅ **Clean shutdown** - Client closed on teardown

**This branch adds:**
6. ✅ **Non-blocking init** - `start_wait=0`
7. ✅ **Flask config pattern** - `app.config` instead of env vars
8. ✅ **Helper abstractions** - Easier testing and maintenance

---

## New Features in This Branch

### 1. Status Endpoint
```bash
curl http://localhost:8000/status
```

Response:
```json
{
  "launchdarkly_initialized": true,
  "status": "ready"
}
```

### 2. Request Context Builder
```python
# Automatically extracts user from request
ctx = build_context_from_request(request)
```

### 3. Environment Configs
```python
# Development
app = create_app('development')  # DEBUG=True

# Production  
app = create_app('production')   # DEBUG=False

# Testing
app = create_app('testing')      # Mock SDK key
```

---

## Migration Guide

To switch from main to this approach:

1. **Add new files:**
   - `config.py`
   - `launchdarkly_helpers.py`

2. **Update app.py to app_idiomatic.py** (or refactor existing)

3. **Update Dockerfile CMD:**
   ```dockerfile
   CMD ["gunicorn", "app_idiomatic:create_app()", "--config", "gunicorn.conf.py"]
   ```

4. **No changes needed to:**
   - `gunicorn.conf.py` (postfork still works)
   - `templates/`
   - Environment variables
   - Docker setup

---

## Additional Resources

- [Flask Application Factories](https://flask.palletsprojects.com/en/latest/patterns/appfactories/)
- [Flask Configuration Handling](https://flask.palletsprojects.com/en/latest/config/)
- [Flask Application Context](https://flask.palletsprojects.com/en/latest/appcontext/)
- [LaunchDarkly Python SDK](https://docs.launchdarkly.com/sdk/server-side/python/)

---

## Try It Out

```bash
# Switch to this branch
git checkout flask-idiomatic-functions

# Run with Flask dev server
python app_idiomatic.py

# Or with Gunicorn
gunicorn "app_idiomatic:create_app()" --config gunicorn.conf.py
```

Both branches are production-ready. Choose the style that fits your needs! 