#!/bin/bash
# Restart the pet app. The pkill pattern names the port so it matches only
# this app, and this script's own command line never contains that pattern.
pkill -f 'app.py 8126' || true
sleep 1
cd "$(dirname "$0")"
nohup python3 app.py 8126 > server.log 2>&1 &
echo "pet app pid $!"
