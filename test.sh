#!/bin/sh

echo $@

APP=$1
shift

ENV=$(for i in "$@"; do echo " -e $i"; done)

docker build -t $APP:latest $APP
docker run $ENV -it $APP:latest
