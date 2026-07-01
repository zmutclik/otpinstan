#!/bin/bash
set -e

PORT=8032
APP="main:app"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔍 Checking port $PORT..."

# Kill existing process on port (using ss to avoid lsof DNS hangs)
PID=$(ss -tlnp "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K\d+' || true)
if [ -n "$PID" ]; then
    echo "⚠️  Killing existing process on port $PORT (PID: $PID)..."
    kill -9 $PID 2>/dev/null
    sleep 1
    echo "✅ Killed."
else
    echo "✅ Port $PORT is free."
fi

# Activate venv
echo "🐍 Activating virtual environment..."
source "$DIR/venv/bin/activate"

# Start server
echo "🚀 Starting OTPInstan Bridge on http://0.0.0.0:$PORT ..."
cd "$DIR"
exec uvicorn "$APP" --host 0.0.0.0 --port $PORT --reload
