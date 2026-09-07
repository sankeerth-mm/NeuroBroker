#!/bin/bash
# Start NeuroBroker React + Vite Frontend Dashboard

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR/frontend"

echo "========================================================"
echo "  Starting NeuroBroker React Web Dashboard"
echo "  Port: 5173"
echo "========================================================"

npm run dev
