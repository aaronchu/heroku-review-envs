FROM trrimages/actions:python

LABEL "com.github.actions.name"="Heroku Config Var Set"
LABEL "com.github.actions.description"="Sets config variables on a heroku review environment"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD heroku-config-var-set.py /heroku-config-var-set.py

RUN chmod +x /heroku-config-var-set.py

ENTRYPOINT ["/heroku-config-var-set.py"]
