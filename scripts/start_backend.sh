#!/bin/bash
# Start NeuroBroker Backend FastAPI Server

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

echo "========================================================"
echo "  Starting NeuroBroker Central Broker Server"
echo "  Port: 8000"
echo "========================================================"

python3 scripts/seed_database.py
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --timeout-keep-alive 65 --reload
