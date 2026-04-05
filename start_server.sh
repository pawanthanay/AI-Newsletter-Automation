#!/bin/bash
# Start the local API server for the Chrome Extension

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

echo "=========================================="
echo " Starting AI Newsletter Local API Server"
echo "=========================================="

# Check if Flask is installed, install if missing
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required API dependencies (Flask, Flask-Cors)..."
    pip3 install Flask Flask-Cors --break-system-packages
fi

# Run the server
python3 api.py
