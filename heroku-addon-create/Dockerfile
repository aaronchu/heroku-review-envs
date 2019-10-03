FROM trrimages/actions:python

LABEL "com.github.actions.name"="Heroku Create Review Environment Addon"
LABEL "com.github.actions.description"="Creates a Heroku Addon for a Review Environment"
LABEL "com.github.actions.icon"="plus-square"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD heroku-addon-create.py /heroku-addon-create.py

RUN chmod +x /heroku-addon-create.py

ENTRYPOINT ["/heroku-addon-create.py"]
