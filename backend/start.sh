#!/usr/bin/env bash
set -o errexit

# Find the Python that has gunicorn installed
PYTHON=$(cat /opt/render/project/.python_path 2>/dev/null || which python3 || which python)
echo "Starting gunicorn with: $PYTHON"
exec $PYTHON -m gunicorn config.wsgi:application --bind 0.0.0.0:10000
