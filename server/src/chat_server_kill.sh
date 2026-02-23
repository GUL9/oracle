#!/bin/bash
PID_FILE="tmp/chat_server.pid"
CHAT_SERVER_DIR="/Users/anton/Code/oracle/server/src"

cd $CHAT_SERVER_DIR 

if [ -f "$PID_FILE" ]; then
    kill $(cat "$PID_FILE") 2>/dev/null
    rm "$PID_FILE"
    echo "Chat server killed"
else
    echo "No chat server PID file found at $PID_FILE"
fi