# Gunicorn Workers & Architecture FAQ

Common questions about how Gunicorn workers, ports, and the master-worker architecture work in this Flask + LaunchDarkly application.

## Table of Contents

1. [Do workers automatically get created?](#do-workers-automatically-get-created)
2. [Which port do workers listen on?](#which-port-do-workers-listen-on)
3. [How does the master-worker architecture work?](#how-does-the-master-worker-architecture-work)
4. [What's the difference between workers and threads?](#whats-the-difference-between-workers-and-threads)
5. [How many concurrent requests can be handled?](#how-many-concurrent-requests-can-be-handled)
6. [How does load balancing work?](#how-does-load-balancing-work)

---

## Do workers automatically get created?

**Yes!** Workers are automatically created based on your `gunicorn.conf.py` configuration.

### Configuration:
```python
# gunicorn.conf.py - Line 6
workers = 2  # Gunicorn will automatically create 2 worker processes
threads = 2  # Each worker will have 2 threads
```

### What happens when you start Gunicorn:

```bash
# You run:
gunicorn --config gunicorn.conf.py app:app

# Or with Docker:
docker-compose up
```

### Automatic startup sequence:

```
1. Master Process Starts
   └─ Reads workers = 2 from config
   └─ Loads app (because preload_app = True)
   └─ Initializes LaunchDarkly client

2. Master Automatically Forks Workers
   ├─ Worker 1 created with PID (e.g., 18)
   │  └─ postfork() called automatically
   │  └─ 2 threads created
   │
   └─ Worker 2 created with PID (e.g., 30)
      └─ postfork() called automatically
      └─ 2 threads created

3. Workers Start Listening
   └─ Ready to handle requests
```

### Real example from logs:

```
[INFO] Starting gunicorn 23.0.0
[INFO] Using worker: gthread
[INFO] Booting worker with pid: 18              ← Worker 1 auto-created
[INFO] Booting worker with pid: 30              ← Worker 2 auto-created
[INFO] ✓ LaunchDarkly postfork() completed successfully in worker 18
[INFO] ✓ LaunchDarkly postfork() completed successfully in worker 30
```

**Everything is 100% automatic!** No manual worker management needed.

---

## Which port do workers listen on?

**All workers listen on the SAME port** - they don't each get their own port.

### Configuration:
```python
# gunicorn.conf.py - Line 5
bind = "0.0.0.0:8000"  # All workers share this single port
```

### Master-Worker Port Architecture:

```
                    Port 8000
                       │
                       ▼
              ┌─────────────────┐
              │  Master Process │ ← ONLY the master binds to port 8000
              │   (PID: 1)      │ ← Accepts incoming connections
              └─────────────────┘
                       │
                       │ Distributes requests to workers
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
    ┌──────────┐             ┌──────────┐
    │ Worker 1 │             │ Worker 2 │
    │ (PID: 18)│             │ (PID: 30)│
    │ No Port  │             │ No Port  │ ← Workers DON'T bind to ports
    │ 2 threads│             │ 2 threads│
    └──────────┘             └──────────┘
```

### Key Points:

1. ✅ **Master binds to port**: Only master process binds to `0.0.0.0:8000`
2. ✅ **Workers don't have ports**: Workers communicate with master via internal IPC
3. ✅ **Single entry point**: All requests come through port 8000
4. ✅ **Internal distribution**: Master distributes work to available workers

### Why don't workers need their own ports?

Workers communicate with the master through **Unix sockets** or **pipes** (inter-process communication), not TCP ports. This is:
- ✅ More efficient
- ✅ Lower overhead
- ✅ Automatic load balancing
- ✅ Easier to manage

---

## How does the master-worker architecture work?

Gunicorn uses a **pre-fork worker model** where the master process manages multiple worker processes.

### Architecture Diagram:

```
┌──────────────────────────────────────────────────────┐
│                   Docker Container                    │
│                                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │            Master Process (PID: 1)             │ │
│  │                                                │ │
│  │  • Binds to 0.0.0.0:8000                      │ │
│  │  • Accepts incoming connections                │ │
│  │  • Distributes to workers                      │ │
│  │  • Monitors worker health                      │ │
│  │  • Restarts crashed workers                    │ │
│  └────────────────────────────────────────────────┘ │
│                        │                             │
│                        │ fork()                      │
│                        │                             │
│        ┌───────────────┴───────────────┐            │
│        │                               │            │
│        ▼                               ▼            │
│  ┌──────────┐                   ┌──────────┐       │
│  │ Worker 1 │                   │ Worker 2 │       │
│  │ PID: 18  │                   │ PID: 30  │       │
│  │          │                   │          │       │
│  │ Thread 1 │                   │ Thread 1 │       │
│  │ Thread 2 │                   │ Thread 2 │       │
│  │          │                   │          │       │
│  │ LD Client│                   │ LD Client│       │
│  │ postfork │                   │ postfork │       │
│  └──────────┘                   └──────────┘       │
└──────────────────────────────────────────────────────┘
                    ↑
                    │
            HTTP Requests on Port 8000
```

### Request Flow:

```
1. Client sends request
   ↓
2. Request arrives at port 8000
   ↓
3. Master accepts connection
   ↓
4. Master selects available worker
   ↓
5. Worker processes request
   ↓
6. Worker evaluates LaunchDarkly flags
   ↓
7. Worker sends response back
   ↓
8. Master forwards response to client
```

### Master's Responsibilities:

1. ✅ Bind to the configured port
2. ✅ Fork worker processes
3. ✅ Distribute requests to workers
4. ✅ Monitor worker health
5. ✅ Restart crashed workers
6. ✅ Graceful shutdowns
7. ✅ Handle signals (reload, shutdown)

### Worker's Responsibilities:

1. ✅ Process HTTP requests
2. ✅ Run application code
3. ✅ Evaluate LaunchDarkly flags
4. ✅ Handle multiple threads
5. ✅ Send responses

---

## What's the difference between workers and threads?

Both allow concurrent processing, but they work differently.

### Workers (Processes)

```python
workers = 2  # 2 separate processes
```

**Characteristics:**
- ✅ Separate memory space (isolated)
- ✅ True parallelism (multi-core)
- ✅ More memory (each has its own copy)
- ✅ Crash isolation (one worker crashes, others continue)
- ⚠️ Higher overhead (forking is expensive)

### Threads (Within a worker)

```python
threads = 2  # 2 threads per worker
```

**Characteristics:**
- ✅ Shared memory space
- ✅ Lower memory overhead
- ✅ Fast creation/switching
- ⚠️ Python GIL limits (good for I/O, not CPU)
- ⚠️ Less isolation (error can affect thread pool)

### In Our Configuration:

```python
workers = 2   # 2 processes
threads = 2   # 2 threads per process
```

**Total capacity**: 2 workers × 2 threads = **4 concurrent connections**

### Visual Comparison:

```
WORKERS (Processes)
┌─────────────┐    ┌─────────────┐
│  Worker 1   │    │  Worker 2   │
│  (Process)  │    │  (Process)  │
│             │    │             │
│  Memory: 50MB│   │  Memory: 50MB│
│  CPU: Core 1│    │  CPU: Core 2│
└─────────────┘    └─────────────┘
     ↑ Isolated         ↑ Isolated
     
THREADS (Within Worker 1)
┌─────────────────────────────┐
│       Worker 1 Process      │
│                             │
│  ┌──────────┐ ┌──────────┐ │
│  │ Thread 1 │ │ Thread 2 │ │
│  │          │ │          │ │
│  │ Shared   │ │ Shared   │ │
│  │ Memory   │ │ Memory   │ │
│  └──────────┘ └──────────┘ │
└─────────────────────────────┘
```

### When to use what?

**More Workers (processes)**:
- ✅ CPU-intensive tasks
- ✅ Need process isolation
- ✅ Multi-core utilization
- ✅ Crash resilience

**More Threads**:
- ✅ I/O-bound operations (like LaunchDarkly API calls)
- ✅ Lower memory footprint
- ✅ Shared state needed
- ✅ Quick context switching

**Our setup (2 workers × 2 threads)**: Balanced approach good for most web apps with I/O operations.

---

## How many concurrent requests can be handled?

**Answer: 4 concurrent requests** with the default configuration.

### Calculation:

```python
# gunicorn.conf.py
workers = 2   # Number of processes
threads = 2   # Threads per process

# Total concurrent capacity:
2 workers × 2 threads = 4 concurrent requests
```

### Request Handling:

```
Request Flow on Port 8000:

Request 1 → Master → Worker 1 (Thread 1) ✓ Handling
Request 2 → Master → Worker 1 (Thread 2) ✓ Handling
Request 3 → Master → Worker 2 (Thread 1) ✓ Handling
Request 4 → Master → Worker 2 (Thread 2) ✓ Handling
Request 5 → Master → Queue (waiting for available thread)
Request 6 → Master → Queue (waiting for available thread)
```

### Scaling Up:

To handle more concurrent requests, increase workers or threads:

```python
# Option 1: More workers (better for CPU tasks)
workers = 4   # 4 workers × 2 threads = 8 concurrent
threads = 2

# Option 2: More threads (better for I/O tasks)
workers = 2   
threads = 4   # 2 workers × 4 threads = 8 concurrent

# Option 3: Both (maximum capacity)
workers = 4   
threads = 4   # 4 workers × 4 threads = 16 concurrent
```

### Rule of Thumb:

```python
# For CPU-bound applications:
workers = (2 × num_cores) + 1

# For I/O-bound applications (like ours with LaunchDarkly):
workers = 2-4
threads = 2-4
```

### LaunchDarkly Consideration:

**Important Note**: The LaunchDarkly SDK **creates its own internal threads automatically** for:
- Background streaming (flag updates)
- Event processing (analytics)

These are **separate from Gunicorn worker threads**. You can set `threads` to any value ≥ 1 based on your HTTP concurrency needs. What matters for LaunchDarkly is calling `postfork()` after forking so the SDK can recreate its internal threads.

```python
threads = 2  # Good for I/O concurrency, not a LaunchDarkly requirement
```

Reference: [LaunchDarkly Python SDK Documentation](https://docs.launchdarkly.com/sdk/server-side/python/#considerations-with-worker-based-servers)

---

## How does load balancing work?

Gunicorn's master process automatically distributes requests across workers.

### Load Balancing Strategy:

Gunicorn uses a **simple round-robin** or **least-busy** strategy depending on the worker class.

```
Request Distribution:

Time    Request    Master Decision       Worker Used
──────────────────────────────────────────────────────
T1      Req 1   →  Worker 1 idle      →  Worker 1
T2      Req 2   →  Worker 2 idle      →  Worker 2
T3      Req 3   →  Worker 1 available →  Worker 1
T4      Req 4   →  Worker 2 available →  Worker 2
T5      Req 5   →  All busy, queue    →  (waiting)
```

### Factors Master Considers:

1. ✅ **Worker availability**: Is worker ready to accept?
2. ✅ **Thread availability**: Does worker have free threads?
3. ✅ **Worker health**: Is worker responsive?
4. ✅ **Fairness**: Distribute evenly

### Thread-Level Load Balancing:

Within each worker, threads handle requests concurrently:

```
Worker 1 Load Distribution:
┌────────────────────────────┐
│       Worker 1             │
│                            │
│  Thread 1: [Request A]     │ ← Processing
│  Thread 2: [Request B]     │ ← Processing
│                            │
│  Queue: [C, D, E]          │ ← Waiting
└────────────────────────────┘
```

### Automatic Features:

1. ✅ **Automatic restart**: If worker crashes, master spawns new one
2. ✅ **Graceful shutdown**: Workers finish current requests before stopping
3. ✅ **Health checks**: Master monitors worker responsiveness
4. ✅ **Signal handling**: Reload workers without downtime

### Monitoring Load:

Check active connections and worker status:
```bash
# View Gunicorn stats
docker-compose logs -f

# Look for:
[INFO] Booting worker with pid: 18
[INFO] Worker timeout (pid:30)    ← Worker issue
[INFO] Shutting down: Master
```

### What if a worker crashes?

```
1. Worker crashes or hangs
   ↓
2. Master detects unresponsive worker
   ↓
3. Master kills unresponsive worker
   ↓
4. Master spawns new worker
   ↓
5. New worker calls postfork()
   ↓
6. Service continues with minimal disruption
```

**Result**: High availability with automatic recovery! 🎯

---

## Summary

### Key Takeaways:

1. 🔧 **Workers are automatic** - Created based on config, no manual management
2. 🔌 **Single port for all** - Master binds to port, distributes to workers
3. ⚖️ **Load balancing built-in** - Master automatically distributes requests
4. 🧵 **Workers ≠ Threads** - Processes vs threads, different use cases
5. 📊 **Capacity = workers × threads** - 2×2 = 4 concurrent in our setup
6. 🔄 **Auto-recovery** - Master restarts crashed workers automatically

### Configuration Reference:

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"      # Port master listens on
workers = 2                 # Number of worker processes
threads = 2                 # Threads per worker
preload_app = True         # Load before forking
timeout = 30               # Worker timeout (seconds)
```

### Your Setup Performance:

- **Port**: 8000 (single entry point)
- **Workers**: 2 processes
- **Threads**: 4 total (2 per worker)
- **Concurrent requests**: 4
- **LaunchDarkly**: postfork() working correctly ✓

Perfect for a production web application! 🚀

---

## Related Documentation

- [LAUNCHDARKLY_ARCHITECTURE.md](LAUNCHDARKLY_ARCHITECTURE.md) - Deep dive into LaunchDarkly integration
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Quick start guide
- [README.md](README.md) - Project overview
- [Gunicorn Documentation](https://docs.gunicorn.org/) - Official Gunicorn docs 