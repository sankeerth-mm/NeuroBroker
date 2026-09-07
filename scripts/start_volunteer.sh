#!/bin/bash
# Start a Volunteer Node Client

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR/volunteer_node"

SERVER_URL=${1:-"http://127.0.0.1:8000"}
TOKEN=${2:-"NB_VOLUNTEER_SECRET_2026"}

echo "========================================================"
echo "  Starting NeuroBroker Volunteer Node"
echo "  Server: $SERVER_URL"
echo "========================================================"

python3 main.py --server "$SERVER_URL" --token "$TOKEN"
