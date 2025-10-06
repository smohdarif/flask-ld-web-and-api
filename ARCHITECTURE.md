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
├── app.py                      # Application entry point (28 lines)
├── config.py                   # Configuration management
│
├── launchdarkly/               # LaunchDarkly integration
│   ├── __init__.py            # Client initialization & lifecycle
│   ├── contexts.py            # Context builders (user, request)
│   └── flags.py               # Flag evaluation wrappers
│
├── middleware/                 # Request/response middleware
│   ├── __init__.py            # Middleware registration
│   ├── context.py             # Context building middleware
│   └── tracking.py            # Duration & error tracking
│
├── routes/                     # HTTP route handlers
│   ├── __init__.py            # Blueprint registration
│   ├── web.py                 # Web pages (home, health)
│   └── api.py                 # REST API endpoints
│
├── templates/                  # Jinja2 templates
│   └── index.html
│
├── gunicorn.conf.py           # Gunicorn configuration
├── requirements.txt           # Python dependencies
└── Dockerfile                 # Container definition
```

## 🔧 Module Responsibilities

### `app.py` - Application Entry Point
**Responsibility**: Minimal orchestration
- Creates Flask app instance
- Imports launchdarkly package (triggers client initialization)
- Registers middleware
- Registers routes

**Size**: 28 lines (down from 173 lines!)

### `config.py` - Configuration Management
**Responsibility**: Environment variable loading and validation
- Loads `.env` file
- Defines `Config` class with all settings
- Validates required configuration

### `launchdarkly/` - LaunchDarkly Integration

#### `__init__.py` - Client Lifecycle
**Responsibility**: Singleton client initialization
- Initializes LD client before Gunicorn forking
- Registers shutdown handler
- Provides `get_client()` accessor

#### `contexts.py` - Context Builders
**Responsibility**: Build LD contexts from various sources
- `user_to_ld_context()` - Build user contexts
- `request_to_ld_context()` - Build request contexts with metadata

#### `flags.py` - Flag Evaluation
**Responsibility**: Convenient flag evaluation wrappers
- `get_flag()` - Uses `g.ld_context` from request
- `get_flag_with_context()` - Uses explicit context

### `middleware/` - Request/Response Middleware

#### `__init__.py` - Middleware Registration
**Responsibility**: Central middleware registration
- `register_middleware()` - Registers all middleware

#### `context.py` - Context Middleware
**Responsibility**: Build contexts before each request
- Extracts user key from query params
- Builds user context → `g.ld_context`
- Builds request context → `g.ld_request_context`
- Tracks request start time → `g.request_start_time`

#### `tracking.py` - Tracking Middleware
**Responsibility**: Monitor requests and errors
- `@app.after_request` - Tracks request duration
- `@app.errorhandler` - Tracks errors
- Sends events to LaunchDarkly with `ld.track()`

### `routes/` - HTTP Routes

#### `__init__.py` - Route Registration
**Responsibility**: Central blueprint registration
- `register_routes()` - Registers all blueprints

#### `web.py` - Web Routes
**Responsibility**: Server-side rendered pages
- `GET /` - Home page with feature flag
- `GET /health` - Health check endpoint

#### `api.py` - API Routes
**Responsibility**: REST API endpoints
- `GET /api/flag/<flag_key>` - Flag evaluation API

## 🔄 Request Flow

```
1. Request arrives
   ↓
2. middleware/context.py
   - Builds g.ld_context (user context)
   - Builds g.ld_request_context (request metadata)
   - Records g.request_start_time
   ↓
3. Route handler (routes/web.py or routes/api.py)
   - Calls get_flag() which uses g.ld_context
   - Returns response
   ↓
4. middleware/tracking.py (@app.after_request)
   - Calculates duration
   - Tracks "request_completed" event
   ↓
5. Response sent

If error occurs:
   ↓
4. middleware/tracking.py (@app.errorhandler)
   - Tracks "request_error" event
   - Re-raises exception
```

## ✅ Benefits of This Architecture

### 1. **Separation of Concerns**
Each module has a single, well-defined responsibility:
- Routes only handle HTTP requests/responses
- Middleware only handles cross-cutting concerns
- LaunchDarkly package only handles LD integration

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
- Easy to add new middleware (add to middleware package)
- Easy to add new context types (add to contexts.py)

### 5. **Reusability**
- LaunchDarkly package can be reused in other projects
- Middleware can be selectively enabled/disabled
- Context builders can be used independently

## 🔐 LaunchDarkly Best Practices Maintained

This refactoring maintains all LaunchDarkly best practices:

✅ **Pre-fork initialization** - Client initialized in `launchdarkly/__init__.py` before app creation  
✅ **Singleton pattern** - Single client instance via `get_client()`  
✅ **Proper shutdown** - `atexit` handler closes client  
✅ **Context per request** - Built in middleware, stored in `g`  
✅ **Tracking events** - Request duration and errors tracked  

## 🚀 Adding New Features

### Adding a New Route
1. Add function to `routes/web.py` or `routes/api.py`
2. Use `get_flag()` to evaluate flags
3. Done! Middleware automatically handles context and tracking

### Adding New Middleware
1. Create new file in `middleware/` (e.g., `auth.py`)
2. Define registration function (e.g., `register_auth_middleware(app)`)
3. Call from `middleware/__init__.py`

### Adding New Context Type
1. Add builder function to `launchdarkly/contexts.py`
2. Call from `middleware/context.py` to build and store in `g`
3. Use in routes as needed

## 📊 Code Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lines in app.py | 173 | 28 | **-84%** |
| Number of files | 1 | 11 | Better organization |
| Concerns mixed | Yes | No | Clear separation |
| Testability | Hard | Easy | Modular design |
| Reusability | Low | High | Package structure |

## 🎯 Design Principles Applied

1. **Single Responsibility Principle** - Each module has one reason to change
2. **Open/Closed Principle** - Easy to extend, hard to break
3. **Dependency Inversion** - High-level modules don't depend on low-level details
4. **Don't Repeat Yourself** - Common logic centralized
5. **Keep It Simple** - Clear, understandable structure
