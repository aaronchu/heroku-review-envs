FROM debian:9.5-slim

LABEL "com.github.actions.name"="Okta Whitelist Review Environment URL"
LABEL "com.github.actions.description"="Whitelists a review environments URL with the Okta sandbox"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

RUN \
  apt-get update && \
  apt-get install -y python3 python3-dev python3-pip python-virtualenv && \
  rm -rf /var/lib/apt/lists/* && \
  cd /usr/local/bin && \
  ln -s /usr/bin/python3 python && \
  pip3 install --upgrade pip

RUN \
  pip3 install requests

ADD okta-whitelist-url-create.py /okta-whitelist-url-create.py

RUN chmod +x /okta-whitelist-url-create.py

ENTRYPOINT ["/okta-whitelist-url-create.py"]
