#!/usr/bin/env bash

IMAGE=$1
NAME=$2
DOCKER_PORT=$3
VOLUME=$4
PORT=$5

set -e

if [[ "$VOLUME" != "none" ]]; then
    VOLUME="-v $VOLUME"
else
    VOLUME=""
fi

set +e

QUERY=$(docker -H tcp://0.0.0.0:2375 ps -a | grep $NAME)

if [[ "$QUERY" == *"Exited"* ]]; then
    echo ">>> Starting the $NAME container..."
    docker -H tcp://0.0.0.0:2375 start $NAME
elif [[ -z "$QUERY" ]]; then
    echo ">>> Running the $NAME container..."
    docker -H tcp://0.0.0.0:2375 run -d \
        --name $NAME \
        -p $PORT:$DOCKER_PORT \
        $VOLUME \
        $IMAGE
    echo ">>> Putting new data to Consul..."
    CONTAINER_IP=$(docker -H tcp://0.0.0.0:2375 inspect --format='{{.Node.Ip}}' $NAME)
    curl -X PUT -d "$CONTAINER_IP" http://localhost:8500/v1/kv/$NAME/ip
    curl -X PUT -d "$PORT" http://localhost:8500/v1/kv/$NAME/port
else
    echo ">>> The $NAME container is already running"
fi
