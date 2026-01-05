# Application Architecture

This document describes the modular architecture of the Flask + LaunchDarkly application.

## 🏗️ Architecture Overview

The application follows a **layered, modular architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                         app.py                               │
│                   (Application Entry Point)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
        ┌───────────┐  ┌──────────┐  ┌──────────┐
        │ LaunchDarkly│  │Middleware│  │  Routes  │
        │   Package  │  │ Package  │  │ Package  │
        └───────────┘  └──────────┘  └──────────┘
```

## 📁 Directory Structure

```
flask-ld-web-and-api/
├── app.py                      # Application entry point (66 lines)
├── config.py                   # Configuration management
│
├── launchdarkly/               # LaunchDarkly integration
│   ├── __init__.py            # Flask extension & client lifecycle
│   ├── contexts.py            # Context builders and management
│   ├── decorators.py          # Route decorators (require_flag, track_*, etc.)
│   └── middleware.py           # Request tracking middleware
│
├── routes/                     # HTTP route handlers
│   ├── __init__.py            # Blueprint registration
│   ├── web.py                 # Web pages (home, health)
│   └── api.py                 # REST API endpoints
│
├── templates/                  # Jinja2 templates
│   └── demo.html              # Home page with template helpers
│
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest configuration
│   ├── test_contexts.py       # Context management tests
│   ├── test_decorators.py     # Decorator tests
│   ├── test_launchdarkly_extension.py # Extension tests
│   ├── test_middleware.py     # Middleware tests
│   └── test_template_helpers.py # Template helper tests
│
├── gunicorn.conf.py           # Gunicorn configuration
├── requirements.txt           # Python dependencies
├── pytest.ini                # Pytest configuration
└── Dockerfile                 # Container definition
```

## 🔧 Module Responsibilities

### `app.py` - Application Entry Point
**Responsibility**: Minimal orchestration
- Creates Flask app instance
- Configures LaunchDarkly client with environment variables
- Initializes LaunchDarkly extension
- Registers context builders
- Registers routes

**Size**: 66 lines (streamlined Flask extension pattern)

### `config.py` - Configuration Management
**Responsibility**: Environment variable loading and logging configuration
- Loads `.env` file
- Provides logging configuration for Flask and LaunchDarkly
- Centralizes configuration management

### `launchdarkly/` - LaunchDarkly Integration

#### `__init__.py` - Flask Extension
**Responsibility**: Flask extension pattern implementation
- Provides `LaunchDarkly` extension class
- Manages client lifecycle and shutdown
- Registers Jinja2 template helpers
- Provides `variation()` and `track()` convenience functions

#### `contexts.py` - Context Management
**Responsibility**: Context builders and management functions
- `create_request_context()` - Build request contexts with metadata
- `add_context()`, `replace_context()`, `remove_context()` - Context management
- `get_context()` - Access current request context
- `use_context()` - Context manager for temporary contexts

#### `decorators.py` - Route Decorators
**Responsibility**: Convenient decorators for common patterns
- `require_flag()` - Feature-gate routes based on flag values
- `with_context()` - Add specific contexts to routes
- `track_after()`, `track_before()` - Event tracking decorators

#### `middleware.py` - Request Tracking
**Responsibility**: Automatic request tracking middleware
- `register_track_request_duration()` - Track request timing
- `register_track_errors()` - Track application errors

### `routes/` - HTTP Routes

#### `__init__.py` - Route Registration
**Responsibility**: Central blueprint registration
- `register_routes()` - Registers all blueprints with Flask app

#### `web.py` - Web Routes
**Responsibility**: Server-side rendered pages
- `GET /` - Home page showcasing LaunchDarkly Flask integration and Jinja2 template helpers
- `GET /health` - Health check endpoint

#### `api.py` - API Routes
**Responsibility**: REST API endpoints
- `GET /api/flag/<flag_key>` - Flag evaluation API
- `GET /api/beta/experimental` - Feature-gated experimental endpoint

## 🔄 Request Flow

```
1. Request arrives
   ↓
2. app.py (@app.before_request)
   - Creates request context with metadata
   - Adds context to Flask's g object
   ↓
3. Route handler (routes/web.py or routes/api.py)
   - Uses variation() to evaluate flags with current context
   - Returns response
   ↓
4. middleware.py (@app.after_request)
   - Calculates request duration
   - Tracks "flask.response_time" event
   ↓
5. Response sent

If error occurs:
   ↓
4. middleware.py (@app.teardown_request)
   - Tracks "flask.error" event
   - Logs error details
```

## ✅ Benefits of This Architecture

### 1. **Separation of Concerns**
Each module has a single, well-defined responsibility:
- Routes only handle HTTP requests/responses
- LaunchDarkly package only handles LD integration
- Templates only handle presentation logic
- Tests only handle validation

### 2. **Testability**
- Each module can be unit tested independently
- Easy to mock dependencies
- Clear interfaces between modules

### 3. **Maintainability**
- Changes are localized to specific modules
- Easy to find where functionality lives
- Clear dependency graph

### 4. **Scalability**
- Easy to add new routes (create new blueprint)
- Easy to add new decorators (add to decorators.py)
- Easy to add new context types (add to contexts.py)
- Easy to add new tests (add to tests/)

### 5. **Reusability**
- LaunchDarkly package can be reused in other projects
- Decorators can be used across different routes
- Context builders can be used independently
- Template helpers work in any Jinja2 template

## 🔐 LaunchDarkly Best Practices Maintained

This architecture maintains all LaunchDarkly best practices:

✅ **Pre-fork initialization** - Client initialized in `app.py` before Gunicorn forking  
✅ **Singleton pattern** - Single client instance via `ldclient.get()`  
✅ **Proper shutdown** - `atexit` handler closes client  
✅ **Context per request** - Built in `@app.before_request`, stored in `g`  
✅ **Tracking events** - Request duration and errors tracked automatically  
✅ **Jinja2 integration** - Template helpers for seamless flag evaluation  

## 🚀 Adding New Features

### Adding a New Route
1. Add function to `routes/web.py` or `routes/api.py`
2. Use `variation()` to evaluate flags
3. Done! Context and tracking handled automatically

### Adding New Decorators
1. Add decorator function to `launchdarkly/decorators.py`
2. Use in routes as needed
3. Add tests to `tests/test_decorators.py`

### Adding New Context Types
1. Add builder function to `launchdarkly/contexts.py`
2. Use in `@app.before_request` or route decorators
3. Add tests to `tests/test_contexts.py`

## 📊 Code Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines in app.py | 173 | 66 | **-62%** |
| Number of files | 1 | 12 | Better organization |
| Concerns mixed | Yes | No | Clear separation |
| Testability | Hard | Easy | Modular design |
| Reusability | Low | High | Package structure |
| Flask patterns | Basic | Extension | Idiomatic Flask |

## 🎯 Design Principles Applied

1. **Single Responsibility Principle** - Each module has one reason to change
2. **Open/Closed Principle** - Easy to extend, hard to break
3. **Dependency Inversion** - High-level modules don't depend on low-level details
4. **Don't Repeat Yourself** - Common logic centralized
5. **Keep It Simple** - Clear, understandable structure
