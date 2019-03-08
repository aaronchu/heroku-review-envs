#!/usr/bin/env python3

import json
import os
import requests
import re
import sys
import time

# some constants
timeout = 20
microservice_suffix = '.herokuapp.com'
label_name = 'review-env'

# tokens
github_token = os.environ['GITHUB_TOKEN']
gha_user_token = os.environ['GHA_USER_TOKEN']
heroku_token = os.environ['HEROKU_API_TOKEN']

# Heroku Related Functions #####################################################

# basic headers for communicating with the Heroku API
headers_heroku = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
    'Authorization': 'Bearer %s' % heroku_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
headers_heroku_review_pipelines = {
    'Accept': 'application/vnd.heroku+json; version=3.pipelines',
    'Authorization': 'Bearer %s' % heroku_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }

api_url_heroku = 'https://api.heroku.com'

def get_review_app_by_branch( pipeline_id, branch_name ):
    r = requests.get(api_url_heroku+'/pipelines/'+pipeline_id+'/review-apps', headers=headers_heroku)
    reviewapps = json.loads(r.text)
    reviewapp = next((x for x in reviewapps if x['branch'] == branch_name), None)
    try:
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except:
        pass
    return None

def get_review_app_by_id( pipeline_id, id ):
    r = requests.get(api_url_heroku+'/pipelines/'+pipeline_id+'/review-apps', headers=headers_heroku)
    reviewapps = json.loads(r.text)
    reviewapp = next((x for x in reviewapps if x['id'] == id), None)
    try:
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except:
        pass
    return None

def get_app_setup_by_id( app_setup_id ):
    r = requests.get(api_url_heroku+'/app-setups/'+app_setup_id, headers=headers_heroku)
    app_setup = json.loads(r.text)
    return app_setup

def delete_app_by_name( app_name ):
    if '-pr-' not in app_name:
        sys.exit("Tried to delete app "+app_name+" - refusing for safety's sake.")
    r = requests.delete(api_url_heroku+'/apps/'+app_name, headers=headers_heroku)
    response = json.loads(r.text)
    return response

def get_app_by_name( app_name ):
    r = requests.get(api_url_heroku+'/apps', headers=headers_heroku)
    apps = json.loads(r.text)
#    print(json.dumps(apps, sort_keys=True, indent=4))
    app = next((x for x in apps if x['name'] == app_name), None)
    try:
        if app is not None and 'id' in app:
            return app
    except:
        pass
    return None

def get_app_by_id( app_id ):
    r = requests.get(api_url_heroku+'/apps', headers=headers_heroku)
    apps = json.loads(r.text)
#    print(json.dumps(apps, sort_keys=True, indent=4))
    app = next((x for x in apps if x['id'] == app_id), None)
    try:
        if app is not None and 'id' in app:
            return app
    except:
        pass
    return None

def rename_app( app_id, app_name ):
    r = requests.patch(api_url_heroku+'/apps/'+app_id, headers=headers_heroku, data=json.dumps( {'name': app_name[:30]} ))
    return r.status_code is 200

def get_pipeline_by_name( pipeline_name ):
    r = requests.get(api_url_heroku+'/pipelines', headers=headers_heroku)
    pipelines = json.loads(r.text)
    pipeline = next((x for x in pipelines if x['name'] == pipeline_name), None)
    if pipeline is not None and 'id' in pipeline:
        return pipeline
    else:
        return None

def get_download_url( repo, branch, token ):
    # pulls the 302 location out of the redirect
    download_url = 'https://api.github.com/repos/'+repo+'/tarball/'+branch+'?access_token='+token
    try:
        r = requests.get(download_url, allow_redirects=False)
        if r.status_code == 302:
            return r.headers['location']
    except:
        pass
    return None

def create_team_app( name, team ):
    r = requests.post(api_url_heroku+'/teams/apps', headers=headers_heroku, data=json.dumps( {'name': name, 'team': team} ))
    app = json.loads(r.text)
    print(json.dumps(app, sort_keys=True, indent=4))
    if 'id' in app:
        return app
    else:
        return None

def create_app_setup( name, team, source_code_tgz_url, commit_sha, envs ):
    payload = {
        'source_blob': {
            'url': source_code_tgz_url,
            'version': commit_sha,
        },
        'app': {
            'name': name,
            'organization': team
        },
        'overrides': {
            'env': envs
        }
    }
    print(json.dumps(payload, sort_keys=True, indent=4))
    r = requests.post(api_url_heroku+'/app-setups', headers=headers_heroku, data=json.dumps(payload))
    app_setup = json.loads(r.text)
    print(json.dumps(app_setup, sort_keys=True, indent=4))
    if 'id' in app_setup:
        return app_setup
    else:
        return None

def add_to_pipeline( pipeline_id, app_id, stage ):
    payload = {
        'app': app_id,
        'pipeline': pipeline_id,
        'stage': stage if stage in [ 'test',' review', 'development', 'staging', 'production' ] else 'development'
    }
    r = requests.post(api_url_heroku+'/pipeline-couplings', headers=headers_heroku, data=json.dumps(payload))
    coupling = json.loads(r.text)
    print(json.dumps(coupling, sort_keys=True, indent=4))
    if 'created_at' in coupling:
        return True
    else:
        return None

def deploy_to_app( app_id, source_code_tgz_url, commit_sha ):
    payload = {
        'source_blob': {
            'url': source_code_tgz_url,
            'version': commit_sha,
        },
    }
    r = requests.post(api_url_heroku+'/apps/'+app_id+'/builds', headers=headers_heroku, data=json.dumps(payload))
    response = json.loads(r.text)
    if 'status' in response:
        return response
    else:
        return None

def get_features_for_app( app_id ):
    r = requests.get(api_url_heroku+'/apps/'+app_id+'/features', headers=headers_heroku)
    features = json.loads(r.text)
    try:
        if features[0]['id'] and features[0]['doc_url']:
            return features
    except:
        pass
    return None

def get_config_vars_for_app( app_id ):
    r = requests.get(api_url_heroku+'/apps/'+app_id+'/config-vars', headers=headers_heroku)
    config_vars = json.loads(r.text)
    return config_vars

def set_config_vars_for_app( app_id, config_vars ):
    r = requests.patch(api_url_heroku+'/apps/'+app_id+'/config-vars', headers=headers_heroku, data=json.dumps(config_vars))
    result = json.loads(r.text)
    if r.status_code != 200:
        return None
    for key, value in result.items():
        if key in config_vars and result[key] != config_vars[key]:
            return None
    return config_vars

def add_buildpacks_to_app( app_id, buildpack_urls ):
    buildpack_changes = {
        'updates': [{ 'buildpack': x } for x in buildpack_urls]
    }
    buildpack_changes['updates']
    r = requests.put(api_url_heroku+'/apps/'+app_id+'/buildpack-installations', headers=headers_heroku, data=json.dumps(buildpack_changes))
    result = json.loads(r.text)
    if r.status_code != 200:
        return None
    return result

def get_review_app_config_vars_for_pipeline( pipeline_id, stage ):
    r = requests.get(api_url_heroku+'/pipelines/'+pipeline_id+'/stage/'+stage+'/config-vars', headers=headers_heroku_review_pipelines)
    config_vars = json.loads(r.text)
    return config_vars


# GitHub Related Functions #####################################################

# basic headers for communicating with the GitHub API
headers_github = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % gha_user_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
api_url_github = 'https://api.github.com'

def get_latest_commit_for_branch( repo, branch_name ):
    r = requests.get(api_url_github+'/repos/'+repo+'/branches/'+branch_name, headers=headers_github)
    branch = json.loads(r.text)
    try:
        return branch['commit']['sha']
    except:
        return None

def get_pr_labels( repo, pr_num ):
    r = requests.get(api_url_github+'/repos/'+repo+'/pulls/'+str(pr_num), headers=headers_github)
    pr = json.loads(r.text)
    return [x['name'] for x in pr['labels']]

def get_pr_name( repo, branch_name ):
    r = requests.get(api_url_github+'/repos/'+repo+'/pulls?per_page=100', headers=headers_github)
    prs = json.loads(r.text)
    return next((x for x in prs if x['head']['ref'] == branch_name), None)

def create_deployment( repo, sha, message ):
    payload = {
        'ref': sha,
        'task': 'deploy',
        'auto_merge': False,
        'description': message
    }
    r = requests.post(api_url_github+'/repos/'+repo+'/deployments', headers=headers_github, data=json.dumps(payload))
    deployment = json.loads(r.text)
    return deployment

def update_deployment_status( repo, deployment_id, app_name, build_id, message ):
    payload = {
        'description': message,
        'environment': 'staging',
        'state': 'success',
        'target_url': 'https://dashboard.heroku.com/apps/%s' % app_name,
        'environment_url': 'https://%s.herokuapp.com/' % app_name,
    }
    r = requests.post(api_url_github+'/repos/'+repo+'/deployments/'+str(deployment_id)+'/statuses', headers=headers_github, data=json.dumps(payload))
    deployment_status = json.loads(r.text)
    return deployment_status

def get_pr_comment( repo, pr_id, sha ):
    r = requests.get(api_url_github+'/repos/'+repo+'/issues/'+str(pr_id)+'/comments', headers=headers_github)
    comments = json.loads(r.text)
    return next((x for x in comments if sha in x['body']), None)

def add_pr_comment( repo, pr_id, message):
    payload = {
        'body': message
    }
    r = requests.post(api_url_github+'/repos/'+repo+'/issues/'+str(pr_id)+'/comments', headers=headers_github, data=json.dumps(payload))
    comment = json.loads(r.text)
    return comment

def edit_pr_comment( repo, pr_id, comment_id, message):
    payload = {
        'body': message
    }
    r = requests.patch(api_url_github+'/repos/'+repo+'/issues/comments/'+str(comment_id), headers=headers_github, data=json.dumps(payload))
    comment = json.loads(r.text)
    return comment


# Non-API-Related Functions ####################################################

def get_app_name( svc_origin, svc_name, pr_num, prefix ):
    if svc_origin != svc_name:
        # if related microservice, we append the service name
        name = "%s-%s-pr-%s-%s" % ( prefix, svc_origin, pr_num, svc_name )
    else:
        # if this is the originatine app, juset name it like vanilla review apps
        name = "%s-%s-pr-%s" % ( prefix, svc_origin, pr_num )
    # truncate to 30 chars for Heroku
    return name[:30]


# PROCESS ENV and ARGS #########################################################

print ("Start "+sys.argv[0])
def mask( k, v ):
    if 'TOKEN' in k or 'SECRET' in k:
        return '***'
    else:
        return v
print ("Environment: " + str({k: mask(k,v) for k, v in os.environ.items()}))

# support arguments passed in via the github actions workflow via the syntax
# args = ["HEROKU_PIPELINE_NAME=github-actions-test"]
args = {}
for arg in sys.argv:
    pair = arg.split('=')
    if len(pair) > 1:
        args[pair[0]] = '='.join(pair[1:])
    else:
        args[arg] = arg

# for quick testing, we want these to be alternatively passed in via environment
args_or_envs = [
    'BRANCH',
    'BUILDPACKS',
    'HEROKU_TEAM_NAME',
    'HEROKU_PIPELINE_NAME',
    'REPO',
    'REPO_ORIGIN',
    'MSVC_REF',
    'MSVC_PREFIX',
    'SERVICE_NAME',
    'SERVICE_ORIGIN'
]
for i in args_or_envs:
    if i not in args and i in os.environ:
        args[i] = os.environ[i]

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

# GET THE INPUTS SET UP RIGHT ##################################################

# determine the service_name - short name that references the type of service
service_name = args['SERVICE_NAME']
print ("Service Name: "+service_name)

# if this SERVICE_ORIGIN is not specified, then we are deploying the originating
# service. Fill in the value of this var just for ease of use.
service_origin = service_name
if 'SERVICE_ORIGIN' in args:
    service_origin = args['SERVICE_ORIGIN']
print("Originating Service: "+service_origin)

# pipeline name that we deploy into
pipeline_name = args['HEROKU_PIPELINE_NAME']
print ("Pipeline Name: "+pipeline_name)

# pull branch name from the GITHUB_REF
branch_origin = os.environ['GITHUB_REF'][11:] # this dumps the preceding 'refs/heads/'
commit_sha = os.environ['GITHUB_SHA']
origin_commit_sha = commit_sha

# set the app name prefix properly
microservice_prefix = args['MSVC_PREFIX']

# we always need to know the originating repo:
repo_origin = os.environ['GITHUB_REPOSITORY']

# are we deploying the originating service, or a related microservice?
if service_origin == service_name:
    # originating service
    repo = repo_origin
    branch = branch_origin
else:
    # related microservice
    repo = args['REPO']
    branch = args['BRANCH']
    commit_sha = get_latest_commit_for_branch( args['REPO'], branch)

github_org = repo.split('/')[0]
print ("GitHub Org: "+github_org)
print ("Repo: "+repo)
print ("Branch to deploy: "+branch)

# DETERMINE THE APP NAME #######################################################

# look up the PR number for origin repo
try:
    pr = get_pr_name( repo_origin, branch_origin )
    pr_num = pr['number']
    print ("Found Pull Request: \"" + pr['title'] + "\" id: " + str(pr_num))
except Exception as ex:
    print(ex)
    sys.exit("Couldn't find a PR for this branch - " + repo_origin + '@' + branch_origin)

# determine the app_name
app_name = get_app_name( service_origin, service_name, pr_num, microservice_prefix )

print ("App Name: "+app_name)

# find the pipeline where we want to spawn the app
try:
    pipeline = get_pipeline_by_name( pipeline_name )
    print ("Found pipeline: " + pipeline['name'] + ' - id: ' + pipeline['id'])
except:
    sys.exit("Couldn't find the pipeline named " + pipeline_name)

# if this is not a labelled PR
labels = get_pr_labels( repo_origin, pr_num )
print ("Detected Labels: " + ', '.join(labels))
if label_name not in labels:
    if get_app_by_name( app_name ):
        # if app is already spun up, shut it down
        print("Spinning down app "+app_name)
        delete_app_by_name( app_name )
    else:
        # If nothing is spun up so far
        print("To spin up a review environment, label your pr with "+label_name)
    sys.exit(0)

# START CREATING/DEPLOYING #####################################################

# see if there's a review app for this branch already
reviewapp = get_app_by_name( app_name )

# Heroku wants us to pull the 302 location for the actual code download by
# using this URL - the token gets modified, we don't know how, so we gotta pull
# it before submitting to Heroku.
source_code_tgz = get_download_url( repo, branch, gha_user_token )
if source_code_tgz is None:
    sys.exit("Couldn't get the redirect location for source code download.")

app_id = None
if reviewapp is not None:
    app_id = reviewapp['id']
    print ("Found reviewapp id: " + app_id )

    # Deploy to the reviewapp as it already exists.
    print ("Deploying...")
    try:
        response = deploy_to_app( app_id, source_code_tgz, commit_sha )
        print ("Created Build:")
        print(json.dumps(response, sort_keys=True, indent=4))
        print ("Status is currently " + response['status'])
    except:
        sys.exit("Couldn't deploy to app id " + reviewapp['id'])

else:
    print ("Found no existing app.")

    # CHECK AND SET CONFIG VARIABLES FOR APP REFERENCES ############################

    # MSVC_REF is a list of config vars referencing other microservices. The config
    # vars are delimited by '|' and key=value pairs are separated by '%'.
    # This code will expand the value provided into:
    #   {MSVC_PREFIX}-{MAIN_APP}-{value}-{branch}
    #
    # for example:
    #   MSVC_REF=MY_API_URL%https://<microsvc>/graphql|MY_HOST%https://<microsvc>/
    # this will result in 2 config vars:
    #   MY_API_URL=https://myteam-someappname.herokuapp.com/graphql
    #   MY_HOST=https://myteam-someappname.herokuapp.com
    set_vars = {}
    if 'MSVC_REF' in args:
        for pair in args['MSVC_REF'].split('|'):
            (msvc_var, msvc_url) = pair.split('%')
            m = re.match(r'^(.*)<(.+)>(.*)$', msvc_url)
            msvc_name = m.group(2)
            set_vars[msvc_var] = m.group(1) + get_app_name( service_origin, msvc_name, pr_num, microservice_prefix ) + microservice_suffix + m.group(3)
            print ("Referencing microservice: " + msvc_var + '=' + set_vars[msvc_var])
    set_vars['HEROKU_APP_NAME'] = app_name

    if service_name == service_origin:
        # This is the originating app - deploy it like a reviewapp.
        print ("Creating reviewapp...")
        payload = {
            'branch': branch,
            'pipeline': pipeline['id'],
            'source_blob': {
                'url': source_code_tgz,
                'version': commit_sha,
            },
            'environment': set_vars
        }
        print(json.dumps(payload, sort_keys=True, indent=4))
        try:
            r = requests.post(api_url_heroku+'/review-apps', headers=headers_heroku, data=json.dumps(payload))
            response = json.loads(r.text)
            print ("Created ReviewApp:")
            print(json.dumps(response, sort_keys=True, indent=4))
            reviewapp_id = response['id']
            print ("Status is currently " + response['status'])
        except:
            sys.exit("Couldn't create ReviewApp.")

        # look up the app ID, wait for it to show up
        for i in range(0, timeout):
            print ("Checking for reviewapp spawn...")
            reviewapp = get_review_app_by_id( pipeline['id'], reviewapp_id )
            if reviewapp is not None:
                app_id = reviewapp['app']['id']
                break
            time.sleep(1)
            if i == timeout:
                sys.exit("timed out waiting for app to instantiate.")
            else:
                print ("waiting...")
        print ("Result:")
        print(json.dumps(reviewapp, sort_keys=True, indent=4))

        # rename the reviewapp (which should just be an app now)
        if rename_app( app_id, app_name ):
            print ("Renamed the app to "+app_name)
        else:
            sys.exit("Failed to rename the app!")

    else:
        # this is a related microservice, deploy it as a development app
        print ("Creating development phase app...")

        # get the config vars from review apps beta config vars in the pipeline
        # we have a feature request in to Heroku for a list of default config
        # vars for development phase apps
        print ("Pulling Config Vars from pipeline "+pipeline['name'])
        config_vars = get_review_app_config_vars_for_pipeline( pipeline['id'], 'review' )
        if not config_vars:
            sys.exit("Pulled no config vars from pipeline: "+pipeline['name'])
        else:
            print ("Found %s Config Vars to set." % len(config_vars.keys()))
        for k,v in set_vars.items():
            config_vars[k] = v

        # an app-setup is just like a reviewapp like above. It is almost like
        # and environment setup in that it creates the app, reads app.json and
        # performs the necessary spin-ups and attachments.
        app_setup = create_app_setup( app_name, args['HEROKU_TEAM_NAME'], source_code_tgz, commit_sha, config_vars )

        # look up the app ID, wait for it to show up
        for i in range(0, timeout):
            print ("Checking for app spawn...")
            app_setup = get_app_setup_by_id( app_setup['id'] )
            if app_setup is not None:
                app_id = app_setup['app']['id']
                break
            time.sleep(1)
            if i == timeout:
                sys.exit("timed out waiting for app to instantiate.")
            else:
                print ("waiting...")
        print ("Result:")
        print(json.dumps(app_setup, sort_keys=True, indent=4))
        app = app_setup['app']

        # attach to pipeline as development app
        print ("Attaching to pipeline...")
        if not add_to_pipeline( pipeline['id'], app['id'], 'development' ):
            sys.exit("Couldn't attach app %s to pipeline %s" % (app['id'],pipeline['id']))

comment = get_pr_comment( repo_origin, pr_num, origin_commit_sha )
message = 'Deployed microservice <a href="https://%s.herokuapp.com">%s</a> - [ <a href="https://dashboard.heroku.com/apps/%s">app: %s</a> | <a href="https://dashboard.heroku.com/apps/%s/logs">logs</a> ]<br>' % (app_name, service_name, app_name, app_name, app_name)
if comment is None:
    comment = add_pr_comment( repo_origin, pr_num, 'Review Environment for commit sha: '+origin_commit_sha+'<br>'+message)
else:
    comment = edit_pr_comment( repo_origin, pr_num, comment['id'], comment['body']+message)
print(comment['body'])

print ("Done.")
