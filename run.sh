#!/bin/bash
# run.sh — ICS Rack Demo API launcher
#
# Automatically restarts the API whenever it exits (crash, /system/restart, etc.)
# This means Save & Exit in the UI will cleanly restart the pipeline without
# any manual terminal intervention.
#
# Usage:
#   chmod +x run.sh   (first time only)
#   ./run.sh

set -e

cd "$(dirname "$0")"

while true; do
    echo ""
    echo "=== ICS API starting ==="
    uvicorn backend.main.database_manager:database_manager \
        --host 0.0.0.0 \
        --port 8000 \
        --log-level info
    EXIT=$?
    echo "=== ICS API exited (code $EXIT), restarting in 2s... ==="
    sleep 2
done
