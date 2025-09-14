"""
Gunicorn configuration for production-quality benchmark testing
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
graceful_timeout = 30

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "glpi_dashboard_backend"

# Performance tuning
preload_app = True  # Load application code before the worker processes are forked
enable_stdio_inheritance = True
worker_tmp_dir = "/dev/shm"  # Use memory for temporary files

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
