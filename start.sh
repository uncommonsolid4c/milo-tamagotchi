#!/bin/bash
# Milo the Tamagotchi, homelab edition. Runs the pet app on port 8126.
cd "$(dirname "$0")"
nohup python3 app.py 8126 > server.log 2>&1 &
echo "pet app pid $!"
