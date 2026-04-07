#!/bin/bash
# Start the local API server for the Chrome Extension

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

echo "=========================================="
echo " Starting AI Newsletter Local API Server"
echo "=========================================="

# Determine Python and Pip commands (use venv if it exists)
if [ -d "venv" ]; then
    PYTHON="$DIR/venv/bin/python3"
    PIP="$DIR/venv/bin/pip3"
else
    PYTHON="python3"
    PIP="pip3"
fi

# Check if Flask is installed, install if missing
$PYTHON -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required API dependencies (Flask, Flask-Cors)..."
    $PIP install Flask Flask-Cors
fi

# Run the server
$PYTHON api.py
