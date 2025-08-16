# Network
bind = "0.0.0.0:8000"

# Worker
workers = 5
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeouts
timeout = 60
graceful_timeout = 30
keepalive = 5

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
capture_output = True

# Security and limits
limit_request_fields = 100
limit_request_field_size = 8190

# PID
pidfile = "./gunicorn.pid"
