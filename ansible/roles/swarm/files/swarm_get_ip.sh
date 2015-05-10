#!/usr/bin/env bash

docker -H tcp://0.0.0.0:2375 inspect --format='{{.Node.Ip}}' $1
