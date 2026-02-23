#!/bin/bash
PID_FILE="tmp/client.pid"
CLIENT_DIR="/Users/anton/Code/oracle/client"

cd $CLIENT_DIR

if [ -f "$PID_FILE" ]; then
    kill $(cat "$PID_FILE") 2>/dev/null
    rm "$PID_FILE"
    echo "Client killed"
else
    echo "No client PID file found at $PID_FILE"
fi
