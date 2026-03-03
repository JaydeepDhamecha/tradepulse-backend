#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Save the Python path so the start command can find installed packages
PYTHON_PATH=$(which python || which python3)
echo "Python at: $PYTHON_PATH"
echo "$PYTHON_PATH" > /opt/render/project/.python_path

python manage.py collectstatic --no-input
