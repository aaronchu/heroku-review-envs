FROM debian:9.5-slim

LABEL "com.github.actions.name"="Hello World"
LABEL "com.github.actions.description"="Write arguments to the standard output"
LABEL "com.github.actions.icon"="mic"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/github-actions-test"
LABEL "homepage"="http://github.com/actions"
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

ADD heroku-app-create.py /heroku-app-create.py

RUN chmod +x /heroku-app-create.py

ENTRYPOINT ["/heroku-app-create.py"]
