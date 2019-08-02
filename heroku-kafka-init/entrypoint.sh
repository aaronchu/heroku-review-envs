#!/bin/bash

set -e
sh -c "$*"


cat $GITHUB_EVENT_PATH

echo "machine api.heroku.com
  login $HEROKU_USER_EMAIL
  password $HEROKU_API_TOKEN
machine git.heroku.com
  login $HEROKU_USER_EMAIL
  password $HEROKU_API_TOKEN
" >> ~/.netrc

for CGROUP in `cat kafka.cgroups`
do
    heroku kafka:consumer-groups:create -a $APP_NAME ${CGROUP}
done

for TOPIC in `cat kafka.topics`
do
    heroku kafka:topics:create -a $APP_NAME ${TOPIC} --partitions 1 --replication-factor 3 --retention-time 2d
done
