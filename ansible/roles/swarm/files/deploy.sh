#!/usr/bin/env bash

IMAGE=$1
NAME=$2
DOCKER_PORT=$3
VOLUMES=$4

set -e

if [[ "$VOLUMES" == "none" ]]; then
    VOLUMES=""
fi

set +e

QUERY=$(curl http://localhost:8500/v1/kv/services/${IMAGE}/${NAME})

if [[ -z "$QUERY" ]]; then
    echo ">>> Removing the old $NAME container..."
    set +e
    docker -H tcp://0.0.0.0:2375 rm -f ${NAME}
    set -e
    echo ">>> Pulling the $NAME container..."
    docker -H tcp://0.0.0.0:2375 pull ${IMAGE}
    echo ">>> Running the $NAME container..."
    docker -H tcp://0.0.0.0:2375 run -d \
        --name ${NAME} \
        -p ${DOCKER_PORT} \
        --env SERVICE_ID=${NAME} \
        ${VOLUMES} \
        ${IMAGE}
else
    echo ">>> The $NAME container is already running"
fi
