#!/bin/bash
CLIENT_DIR="/Users/anton/Code/oracle/client"
PID_FILE="tmp/client.pid"

cd $CLIENT_DIR

# Create tmp directory if it doesn't exist
mkdir -p tmp

# Save the PID to a file
echo $$ > "$PID_FILE"

python src/client.py
