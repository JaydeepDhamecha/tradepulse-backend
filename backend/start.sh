#!/usr/bin/env bash
set -o errexit

# Try multiple known paths for Render's Python environment
for PYTHON in \
    /opt/render/project/src/.venv/bin/python \
    /opt/render/project/.venv/bin/python \
    "$(which python3 2>/dev/null)" \
    "$(which python 2>/dev/null)"; do
    if [ -x "$PYTHON" ]; then
        echo "==> Using Python: $PYTHON"
        exec $PYTHON -m gunicorn config.wsgi:application --bind 0.0.0.0:10000
    fi
done

echo "==> ERROR: No Python found"
exit 1
