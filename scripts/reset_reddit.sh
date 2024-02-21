#!/bin/bash

# Define variables
CONTAINER_NAME="forum"

docker stop $CONTAINER_NAME
docker rm $(docker ps -a | grep $CONTAINER_NAME | awk '{print $1}')
docker run --name $CONTAINER_NAME -p 9999:80 -p 9998:5432 -d postmill-populated-exposed-withimg:v3
# wait ~15 secs for all services to start
sleep 15
