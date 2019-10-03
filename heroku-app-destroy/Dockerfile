FROM trrimages/actions:python

LABEL "com.github.actions.name"="Heroku Destroy Review Environment App"
LABEL "com.github.actions.description"="Destroys a Review App for a Review Environment"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD heroku-app-destroy.py /heroku-app-destroy.py

RUN chmod +x /heroku-app-destroy.py

ENTRYPOINT ["/heroku-app-destroy.py"]
