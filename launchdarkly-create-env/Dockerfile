FROM trrimages/actions:python

LABEL "com.github.actions.name"="Launchdarkly Create Environment"
LABEL "com.github.actions.description"="Creates a Launchdarkly app for a Review Environment"
LABEL "com.github.actions.icon"="box"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="http://github.com/TheRealReal/launchdarkly-create-env"
LABEL "homepage"="http://github.com/TheRealReal/launchdarkly-create-env"
LABEL "maintainer"="The RealReal DevOps <devops@therealreal.com>"

ADD launchdarkly-create-env.py /launchdarkly-create-env.py

RUN chmod +x /launchdarkly-create-env.py

ENTRYPOINT ["/launchdarkly-create-env.py"]
