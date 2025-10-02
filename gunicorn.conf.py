# Gunicorn config for Flask + LaunchDarkly (with postfork best practice)
# Use with: gunicorn --config gunicorn.conf.py app:app
import ldclient

bind = "0.0.0.0:8000"
workers = 2
# Use multiple threads for better concurrency with I/O-bound operations
# LaunchDarkly SDK manages its own internal threads automatically
threads = 2
timeout = 30
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Preload app before forking workers (LaunchDarkly best practice #1)
preload_app = True

def post_fork(server, worker):
    """
    LaunchDarkly best practice #2: Reinitialize client after forking.
    
    When using worker-based servers like Gunicorn, threads don't survive
    the forking process. This hook ensures each worker reinitializes the
    LaunchDarkly client so it can properly receive flag updates and send events.
    
    This requires LaunchDarkly SDK v9.11+ and works in Docker environments
    with proper Python/OpenSSL setup.
    """
    try:
        client = ldclient.get()
        client.postfork()
        server.log.info(f"✓ LaunchDarkly postfork() completed successfully in worker {worker.pid}")
    except Exception as e:
        server.log.exception(f"✗ LaunchDarkly postfork() failed in worker {worker.pid}: {e}")
