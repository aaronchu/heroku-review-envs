FROM debian:9.5-slim

LABEL "com.github.actions.name"="Heroku Kafka Init"
LABEL "com.github.actions.description"="Creates topics and consumer groups for a Kafka add-on"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

RUN \
  apt-get update && \
  apt-get install -y curl jq && \
  curl https://cli-assets.heroku.com/install.sh | sh && \
  heroku plugins:install heroku-kafka

ENV PATH="$PATH:$(yarn global bin)"

ADD entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
