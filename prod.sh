#!/bin/bash

# QuizApp Production Script
# Simple production deployment with Uvicorn and Tailwind

PYTHON_PATH=".venv/bin/python"
PROJECT_DIR="/home/super/Documents/QuizAppFull"
TAILWIND_DIR="$PROJECT_DIR/youtube/static_src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Build Tailwind CSS
build_tailwind() {
    print_info "Building Tailwind CSS..."
    cd "$TAILWIND_DIR" && npm run build
}

# Collect static files
collect_static() {
    print_info "Collecting static files..."
    cd "$PROJECT_DIR"
    DJANGO_SETTINGS_MODULE=config.settings_production $PYTHON_PATH manage.py collectstatic --noinput
}

# Run migrations
migrate() {
    print_info "Running migrations..."
    cd "$PROJECT_DIR"
    DJANGO_SETTINGS_MODULE=config.settings_production $PYTHON_PATH manage.py migrate
}

# Start server
start_server() {
    local host="${1:-127.0.0.1}"
    local port="${2:-8000}"
    local workers="${3:-2}"
    
    print_info "Starting server on $host:$port with $workers workers..."
    cd "$PROJECT_DIR"
    DJANGO_SETTINGS_MODULE=config.settings_production .venv/bin/uvicorn config.asgi:application \
        --host "$host" --port "$port" --workers "$workers" \
        --access-log --loop uvloop
}

# Main deployment
deploy() {
    print_info "Starting production deployment..."
    build_tailwind && migrate && collect_static && start_server "$@"
}

# Command handling
case "$1" in
    "deploy") deploy "${@:2}" ;;
    "start") start_server "${@:2}" ;;
    "build") build_tailwind ;;
    "migrate") migrate ;;
    "static") collect_static ;;
    *)
        echo "QuizApp Production Script"
        echo "Usage: ./prod.sh [command] [options]"
        echo ""
        echo "Commands:"
        echo "  deploy [host] [port] [workers]  - Full deployment"
        echo "  start [host] [port] [workers]   - Start server only"
        echo "  build                           - Build Tailwind CSS"
        echo "  migrate                         - Run migrations"
        echo "  static                          - Collect static files"
        echo ""
        echo "Examples:"
        echo "  ./prod.sh deploy                # Deploy on 127.0.0.1:8000"
        echo "  ./prod.sh deploy 0.0.0.0 8080 4 # Deploy on 0.0.0.0:8080 with 4 workers"
        echo "  ./prod.sh start                 # Start server only"
        ;;
esac
