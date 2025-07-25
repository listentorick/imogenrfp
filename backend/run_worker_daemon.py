#!/usr/bin/env python3
"""
Run the document worker as a daemon process
"""
import os
import sys
import time
import signal
import atexit
from pathlib import Path

def daemonize():
    """Convert current process to daemon"""
    try:
        pid = os.fork()
        if pid > 0:
            # Exit parent process
            sys.exit(0)
    except OSError as e:
        print(f"Fork failed: {e}")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        print(f"Second fork failed: {e}")
        sys.exit(1)
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Write PID file
    with open('/tmp/worker.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Register cleanup
    atexit.register(lambda: os.remove('/tmp/worker.pid') if os.path.exists('/tmp/worker.pid') else None)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down worker...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check if already running
    if os.path.exists('/tmp/worker.pid'):
        try:
            with open('/tmp/worker.pid', 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process is actually running
            os.kill(pid, 0)
            print(f"Worker already running with PID {pid}")
            sys.exit(1)
        except (OSError, ValueError):
            # Process not running, remove stale PID file
            os.remove('/tmp/worker.pid')
    
    print("Starting document processing worker daemon...")
    
    # Start the worker
    from start_worker import run_worker
    run_worker()