FROM trrimages/actions:python

LABEL "com.github.actions.name"="Okta Whitelist Review Environment URL"
LABEL "com.github.actions.description"="Whitelists a review environments URL with the Okta sandbox"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD okta-whitelist-url-destroy.py /okta-whitelist-url-destroy.py

RUN chmod +x /okta-whitelist-url-destroy.py

ENTRYPOINT ["/okta-whitelist-url-destroy.py"]
