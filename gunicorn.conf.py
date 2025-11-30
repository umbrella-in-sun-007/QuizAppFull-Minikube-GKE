import multiprocessing

# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file

# The socket to bind
bind = "0.0.0.0:8000"

# The number of worker processes for handling requests
workers = multiprocessing.cpu_count() * 2 + 1

# The type of workers to use
worker_class = "gthread"

# The number of worker threads for handling requests
threads = 8

# The maximum number of pending connections
backlog = 4096

# The maximum number of simultaneous clients
worker_connections = 2000

# Timeout for graceful workers restart
timeout = 60

# The maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Access log - records incoming HTTP requests
accesslog = "-"

# Error log - records Gunicorn errors
errorlog = "-"

# Log level
loglevel = "info"

# Process name
proc_name = "quizapp_gunicorn"
