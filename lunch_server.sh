#!/bin/bash
# Watchrat - lunch_server.sh
# Starts or stops the Minecraft server via restricted SSH to the host

SSH_KEY="/home/watchrat/.ssh/bot_ssh_key"
SSH_USER="watchrat"
SSH_HOST="host.docker.internal"
SSH_PORT="40286"
CONTAINER="mceternal2026"

case "$1" in
    start)
        ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "docker start $CONTAINER"
        ;;
    stop)
        ssh -i "$SSH_KEY" -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" "docker stop $CONTAINER"
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac