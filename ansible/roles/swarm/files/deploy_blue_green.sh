#!/usr/bin/env bash

OWNER=$1
IMAGE=$2
NAME=$3
DOCKER_PORT=$4
VOLUMES=$5
ENVS=$6

set -e

if [[ -n "$OWNER" ]]; then
    OWNER="$OWNER/"
fi

CURRENT_COLOR=$(curl http://localhost:8500/v1/kv/services/${IMAGE}/${NAME}-blue)
if [[ -z "$CURRENT_COLOR" ]]; then
    NEW_COLOR=blue
    COLOR=green
else
    NEW_COLOR=green
    COLOR=blue
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
docker -H tcp://0.0.0.0:2375 pull $OWNER$IMAGE

echo ">>> Starting $NEW_FULL_NAME..."
docker -H tcp://0.0.0.0:2375 run -d \
  --name $NEW_FULL_NAME \
  -p $DOCKER_PORT \
  --env SERVICE_ID=${NEW_FULL_NAME} \
  $ENVS \
  $VOLUMES \
  $OWNER$IMAGE


echo ">> Putting new data to Consul..."
curl -X PUT -d "$NEW_COLOR" http://localhost:8500/v1/kv/services/$IMAGE/color
curl -X PUT -d "$COLOR" http://localhost:8500/v1/kv/services/$IMAGE/old-color