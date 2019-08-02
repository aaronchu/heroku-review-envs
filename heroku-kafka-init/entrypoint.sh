#!/bin/bash

set -e
sh -c "$*"

echo "machine api.heroku.com
  login $HEROKU_USER_EMAIL
  password $HEROKU_API_TOKEN
machine git.heroku.com
  login $HEROKU_USER_EMAIL
  password $HEROKU_API_TOKEN
" >> ~/.netrc

PR_NUMBER=$(jq '.pull_request.number' $GITHUB_EVENT_PATH)
HEROKU_APP_NAME="${APP_PREFIX}-${APP_NAME}-pr-${PR_NUMBER}"

heroku ps -a $HEROKU_APP_NAME
heroku plugins

for CGROUP in `cat kafka.cgroups`
do
    heroku kafka:consumer-groups:create -a $HEROKU_APP_NAME ${CGROUP}
done

for TOPIC in `cat kafka.topics`
do
    heroku kafka:topics:create -a $HEROKU_APP_NAME ${TOPIC} --partitions 1 --replication-factor 3 --retention-time 2d
done
