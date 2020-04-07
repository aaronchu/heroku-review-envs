FROM trrimages/actions:python

LABEL "com.github.actions.name"="Launchdarkly Destroy Review Environment"
LABEL "com.github.actions.description"="Destroys a Launchdarkly Env for a Review Environment"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "homepage"="http://github.com/TheRealReal/heroku-review-envs"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD launchdarkly-remove-env.py /launchdarkly-remove-env.py
ADD github_event.json /github_event.json

RUN chmod +x /launchdarkly-remove-env.py

ENTRYPOINT ["/launchdarkly-remove-env.py"]
