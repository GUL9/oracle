#!/bin/bash
CHAT_SERVER_DIR="/Users/anton/Code/oracle/server/src"
PID_FILE="tmp/chat_server.pid"
host=127.0.0.1
port=8000

cd $CHAT_SERVER_DIR 

# Save the PID to a file
echo $$ > "$PID_FILE"

uvicorn chat_server:app --host $host --port $port --reload --log-level info