FROM trrimages/actions:python

LABEL "com.github.actions.name"="Heroku Create Review Environment App"
LABEL "com.github.actions.description"="Creates a Review App for a Review Environment"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD heroku-app-create.py /heroku-app-create.py

RUN chmod +x /heroku-app-create.py

ENTRYPOINT ["/heroku-app-create.py"]
