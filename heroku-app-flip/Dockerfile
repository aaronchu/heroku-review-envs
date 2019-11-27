FROM trrimages/actions:python

LABEL "com.github.actions.name"="Heroku Review Environment Flip"
LABEL "com.github.actions.description"="Flips a review environment to .com or .ninja"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD heroku-app-flip.py /heroku-app-flip.py

RUN chmod +x /heroku-app-flip.py

ENTRYPOINT ["/heroku-app-flip.py"]
