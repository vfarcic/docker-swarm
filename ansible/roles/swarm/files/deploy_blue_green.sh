#!/usr/bin/env bash

IMAGE=$1
NAME=$2
DOCKER_PORT=$3
BLUE_PORT=$4
GREEN_PORT=$5
VOLUMES=$6
ENVS=$7

set -e

CURRENT_PORT=$(curl http://localhost:8500/v1/kv/$NAME/port?raw)
if [[ "$CURRENT_PORT" = "$BLUE_PORT" ]]; then
    NEW_PORT=$GREEN_PORT
    NEW_COLOR=green
    COLOR=blue
else
    NEW_PORT=$BLUE_PORT
    NEW_COLOR=blue
    COLOR=green
fi

if [[ "$VOLUMES" == "none" ]]; then
    VOLUMES=""
fi

if [[ "$ENVS" == "none" ]]; then
    ENVS=""
fi

NEW_FULL_NAME=$NAME-$NEW_COLOR
FULL_NAME=$NAME-$COLOR

set +e

echo ">>> Removing $NEW_FULL_NAME..."
docker -H tcp://0.0.0.0:2375 rm -f $NEW_FULL_NAME

set -e

echo ">>> Pulling latest version of $NEW_FULL_NAME..."
docker -H tcp://0.0.0.0:2375 pull $IMAGE

echo ">>> Starting $NEW_FULL_NAME..."
docker -H tcp://0.0.0.0:2375 run -d \
  --name $NEW_FULL_NAME \
  -p $NEW_PORT:$DOCKER_PORT \
  $VOLUMES \
  $ENVS \
  $IMAGE

echo ">> Putting new data to Consul..."
CONTAINER_IP=$(docker -H tcp://0.0.0.0:2375 inspect --format='{{.Node.Ip}}' $NEW_FULL_NAME)
curl -X PUT -d "$CONTAINER_IP" http://localhost:8500/v1/kv/$NAME/ip
curl -X PUT -d "$NEW_PORT" http://localhost:8500/v1/kv/$NAME/port
curl -X PUT -d "$NEW_COLOR" http://localhost:8500/v1/kv/$NAME/color
curl -X PUT -d "$PORT" http://localhost:8500/v1/kv/$NAME/old_port
curl -X PUT -d "$COLOR" http://localhost:8500/v1/kv/$NAME/old_color
