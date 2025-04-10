import multiprocessing
import os

# Server socket - use PORT environment variable provided by Railway
port = os.getenv("PORT", "8000")
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"  # Changed from UvicornWorker to sync
worker_connections = 1000
timeout = 300  # Increased from 30 to 300 seconds
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "freshly_r"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None 