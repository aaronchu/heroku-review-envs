FROM trrimages/actions:python

LABEL "com.github.actions.name"="Heroku Whitelist Toggle"
LABEL "com.github.actions.description"="Toggles the Okta environment that a review environment is whitelisted with"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD okta-whitelist-toggle.py /okta-whitelist-toggle.py

RUN chmod +x /okta-whitelist-toggle.py

ENTRYPOINT ["/okta-whitelist-toggle.py"]
