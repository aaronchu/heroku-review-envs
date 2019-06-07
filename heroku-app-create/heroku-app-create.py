#!/usr/bin/env python3

import json
import os
import requests
import re
import sys
import time
import urllib.parse

# some constants
TIMEOUT = 20
APP_DOMAIN_SUFFIX = '.herokuapp.com'
LABEL_NAME = 'review-env'

# tokens
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GHA_USER_TOKEN = os.environ['GHA_USER_TOKEN']
HEROKU_TOKEN = os.environ['HEROKU_API_TOKEN']

# basic headers for communicating with the Heroku API
HEADERS_HEROKU = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
    'Authorization': 'Bearer %s' % HEROKU_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
HEADERS_HEROKU_REVIEW_PIPELINES = {
    'Accept': 'application/vnd.heroku+json; version=3.pipelines',
    'Authorization': 'Bearer %s' % HEROKU_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }

API_URL_HEROKU = 'https://api.heroku.com'

# basic headers for communicating with the GitHub API
HEADERS_GITHUB = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % GHA_USER_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
API_URL_GITHUB = 'https://api.github.com'

# Heroku Related Functions #####################################################


def get_review_app_by_branch( pipeline_id, branch_name ):
    r = requests.get(API_URL_HEROKU+'/pipelines/'+pipeline_id+'/review-apps', headers=HEADERS_HEROKU)
    reviewapps = json.loads(r.text)
    try:
        reviewapp = next((x for x in reviewapps if x['branch'] == branch_name), None)
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except:
        pass
    return None

def get_review_app_by_id( pipeline_id, id ):
    r = requests.get(API_URL_HEROKU+'/pipelines/'+pipeline_id+'/review-apps', headers=HEADERS_HEROKU)
    reviewapps = json.loads(r.text)
    try:
        reviewapp = next((x for x in reviewapps if x['id'] == id), None)
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except:
        pass
    return None

def get_app_setup_by_id( app_setup_id ):
    r = requests.get(API_URL_HEROKU+'/app-setups/'+app_setup_id, headers=HEADERS_HEROKU)
    app_setup = json.loads(r.text)
    return app_setup

def delete_app_by_name( app_name ):
    if '-pr-' not in app_name:
        sys.exit("Tried to delete app "+app_name+" - refusing for safety's sake.")
    r = requests.delete(API_URL_HEROKU+'/apps/'+app_name, headers=HEADERS_HEROKU)
    response = json.loads(r.text)
    return response

def get_app_by_name( app_name ):
    r = requests.get(API_URL_HEROKU+'/apps', headers=HEADERS_HEROKU)
    apps = json.loads(r.text)
    try:
        app = next((x for x in apps if x['name'] == app_name), None)
        if app is not None and 'id' in app:
            return app
    except:
        pass
    return None

def get_app_by_id( app_id ):
    r = requests.get(API_URL_HEROKU+'/apps', headers=HEADERS_HEROKU)
    apps = json.loads(r.text)
    try:
        app = next((x for x in apps if x['id'] == app_id), None)
        if app is not None and 'id' in app:
            return app
    except:
        pass
    return None

def rename_app( app_id, app_name ):
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_id, headers=HEADERS_HEROKU, data=json.dumps( {'name': app_name[:30]} ))
    return r.status_code is 200

def get_pipeline_by_name( pipeline_name ):
    r = requests.get(API_URL_HEROKU+'/pipelines', headers=HEADERS_HEROKU)
    pipelines = json.loads(r.text)
    try:
        pipeline = next((x for x in pipelines if x['name'] == pipeline_name), None)
        if pipeline is not None and 'id' in pipeline:
            return pipeline
    except:
        pass
    return None

def create_team_app( name, team ):
    r = requests.post(API_URL_HEROKU+'/teams/apps', headers=HEADERS_HEROKU, data=json.dumps( {'name': name, 'team': team} ))
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
    r = requests.post(API_URL_HEROKU+'/app-setups', headers=HEADERS_HEROKU, data=json.dumps(payload))
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
    r = requests.post(API_URL_HEROKU+'/pipeline-couplings', headers=HEADERS_HEROKU, data=json.dumps(payload))
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
    r = requests.post(API_URL_HEROKU+'/apps/'+app_id+'/builds', headers=HEADERS_HEROKU, data=json.dumps(payload))
    response = json.loads(r.text)
    if 'status' in response:
        return response
    else:
        return None

def get_features_for_app( app_id ):
    r = requests.get(API_URL_HEROKU+'/apps/'+app_id+'/features', headers=HEADERS_HEROKU)
    features = json.loads(r.text)
    try:
        if features[0]['id'] and features[0]['doc_url']:
            return features
    except:
        pass
    return None

def get_config_vars_for_app( app_id ):
    r = requests.get(API_URL_HEROKU+'/apps/'+app_id+'/config-vars', headers=HEADERS_HEROKU)
    config_vars = json.loads(r.text)
    return config_vars

def set_config_vars_for_app( app_id, config_vars ):
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_id+'/config-vars', headers=HEADERS_HEROKU, data=json.dumps(config_vars))
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
    r = requests.put(API_URL_HEROKU+'/apps/'+app_id+'/buildpack-installations', headers=HEADERS_HEROKU, data=json.dumps(buildpack_changes))
    result = json.loads(r.text)
    if r.status_code != 200:
        return None
    return result

def get_review_app_config_vars_for_pipeline( pipeline_id, stage ):
    r = requests.get(API_URL_HEROKU+'/pipelines/'+pipeline_id+'/stage/'+stage+'/config-vars', headers=HEADERS_HEROKU_REVIEW_PIPELINES)
    config_vars = json.loads(r.text)
    return config_vars

def grant_review_app_access_to_user( app_name, email ):
    payload = {
        'user': email,
        'permissions': ['view', 'manage'],
        'silent': True
    }
    r = requests.post(API_URL_HEROKU+'/teams/apps/'+app_name+'/collaborators', headers=HEADERS_HEROKU_REVIEW_PIPELINES, data=json.dumps(payload))
    return json.loads(r.text)

def get_team_members( team_name ):
    r = requests.get(API_URL_HEROKU+'/teams/'+team_name+'/members', headers=HEADERS_HEROKU_REVIEW_PIPELINES)
    team_members = json.loads(r.text)
    return team_members

# GitHub Related Functions #####################################################

def get_download_url( repo, branch, token ):
    # pulls the 302 location out of the redirect
    download_url = API_URL_GITHUB+'/repos/'+repo+'/tarball/'+urllib.parse.quote(branch)+'?access_token='+token
    try:
        r = requests.get(download_url, allow_redirects=False)
        if r.status_code == 302:
            return r.headers['location']
    except:
        pass
    return None

def get_latest_commit_for_branch( repo, branch_name ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/branches/'+urllib.parse.quote(branch_name), headers=HEADERS_GITHUB)
    branch = json.loads(r.text)
    try:
        return branch['commit']['sha']
    except:
        return None

def get_pr_name( repo, branch_name, page=1 ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/pulls?state=all&page='+str(page)+'&per_page=100', headers=HEADERS_GITHUB)
    prs = json.loads(r.text)
    try:
        pr = next((x for x in prs if x['head']['ref'] == branch_name), None)
        if pr:
            return pr
        else:
            return get_pr_name( repo, branch_name, page=page+1)
    except:
        return None

def add_pr_comment( repo, pr_id, message):
    payload = {
        'body': message
    }
    r = requests.post(API_URL_GITHUB+'/repos/'+repo+'/issues/'+str(pr_id)+'/comments', headers=HEADERS_GITHUB, data=json.dumps(payload))
    comment = json.loads(r.text)
    return comment


# Non-API-Related Functions ####################################################

def get_app_name( svc_origin, svc_name, pr_num, prefix ):
    if svc_origin != svc_name:
        # if related app, we append the app name
        name = "%s-%s-pr-%s-%s" % ( prefix, svc_origin, pr_num, svc_name )
    else:
        # if this is the originating app, just name it like vanilla review apps
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
    'APP_REF',
    'APP_PREFIX',
    'APP_NAME',
    'APP_ORIGIN'
]
for i in args_or_envs:
    if i not in args and i in os.environ:
        args[i] = os.environ[i]

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

# GET THE INPUTS SET UP RIGHT ##################################################

# determine the app_short_name - short name that references the type of service
app_short_name = args['APP_NAME']
print ("Service Name: "+app_short_name)

# if this APP_ORIGIN is not specified, then we are deploying the originating
# service. Fill in the value of this var just for ease of use.
app_origin = app_short_name
if 'APP_ORIGIN' in args:
    app_origin = args['APP_ORIGIN']
print("Originating Service: "+app_origin)

# pipeline name that we deploy into
pipeline_name = args['HEROKU_PIPELINE_NAME']
print ("Pipeline Name: "+pipeline_name)

# pull branch name from the GITHUB_REF
branch_origin = os.environ['GITHUB_REF'][11:] # this dumps the preceding 'refs/heads/'
commit_sha = os.environ['GITHUB_SHA']
origin_commit_sha = commit_sha

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# we always need to know the originating repo:
repo_origin = os.environ['GITHUB_REPOSITORY']

# are we deploying the originating app, or a related app?
if app_origin == app_short_name:
    # originating app
    repo = repo_origin
    branch = branch_origin
else:
    # related app
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
    pr_labels = [x['name'] for x in pr['labels']]
    pr_status = pr['state']
    print ("Found Pull Request: \"" + pr['title'] + "\" id: " + str(pr_num))
except Exception as ex:
    print(ex)
    sys.exit("Couldn't find a PR for this branch - " + repo_origin + '@' + branch_origin)

# determine the app_name
app_name = get_app_name( app_origin, app_short_name, pr_num, app_prefix )

print ("App Name: "+app_name)

# find the pipeline where we want to spawn the app
try:
    pipeline = get_pipeline_by_name( pipeline_name )
    print ("Found pipeline: " + pipeline['name'] + ' - id: ' + pipeline['id'])
except:
    sys.exit("Couldn't find the pipeline named " + pipeline_name)

# if this is not a labelled PR
print ("Detected Labels: " + ', '.join(pr_labels))
if LABEL_NAME not in pr_labels or pr_status == 'closed':
    if get_app_by_name( app_name ):
        # if app is already spun up, shut it down
        print("Spinning down app "+app_name)
        delete_app_by_name( app_name )
    else:
        # If nothing is spun up so far
        print("To spin up a review environment, label your open pr with "+LABEL_NAME)
    sys.exit(0)

# START CREATING/DEPLOYING #####################################################

# see if there's a review app for this branch already
reviewapp = get_app_by_name( app_name )

# if it wasn't found, try to use an existing review app if it already exists
if reviewapp is None and app_origin == app_short_name:
    reviewapp = get_review_app_by_branch( pipeline['id'], branch)

# Heroku wants us to pull the 302 location for the actual code download by
# using this URL - the token gets modified, we don't know how, so we gotta pull
# it before submitting to Heroku.
source_code_tgz = get_download_url( repo, branch, GHA_USER_TOKEN )
if source_code_tgz is None:
    sys.exit("Couldn't get the redirect location for source code download.")

app_id = None
if reviewapp is not None:
    app_id = reviewapp['id']
    print ("Found reviewapp id: " + app_id )
    # Originating App - doesn't need to be deployed because Review Apps Beta
    #   automatically deploys on push to the PR.
    # Related App - we do not deploy here b/c we don't want to disrupt the state
    #   of the related app as that may affect testing.
    print("Already exists - no action necessary.")

else:
    print ("Found no existing app.")

    # CHECK AND SET CONFIG VARIABLES FOR APP REFERENCES ############################

    # APP_REF is a list of config vars referencing other apps. The config
    # vars are delimited by '|' and key=value pairs are separated by '%'.
    # This code will expand the value provided into:
    #   {APP_PREFIX}-{MAIN_APP}-{value}-{branch}
    #
    # for example:
    #   APP_REF=MY_API_URL%https://<app_name>/graphql|MY_HOST%https://<app_name>/
    # this will result in 2 config vars:
    #   MY_API_URL=https://myteam-someappname.herokuapp.com/graphql
    #   MY_HOST=https://myteam-someappname.herokuapp.com
    set_vars = {}
    if 'APP_REF' in args:
        for pair in args['APP_REF'].split('|'):
            (app_var, app_url) = pair.split('%')
            m = re.match(r'^(.*)<(.+)>(.*)$', app_url)
            name = m.group(2)
            set_vars[app_var] = m.group(1) + get_app_name( app_origin, name, pr_num, app_prefix ) + APP_DOMAIN_SUFFIX + m.group(3)
            print ("Referencing app: " + app_var + '=' + set_vars[app_var])
    set_vars['HEROKU_APP_NAME'] = app_name

    if app_short_name == app_origin:
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
            r = requests.post(API_URL_HEROKU+'/review-apps', headers=HEADERS_HEROKU, data=json.dumps(payload))
            response = json.loads(r.text)
            print ("Created ReviewApp:")
            print(json.dumps(response, sort_keys=True, indent=4))
            reviewapp_id = response['id']
            print ("Status is currently " + response['status'])
        except:
            sys.exit("Couldn't create ReviewApp.")

        # look up the app ID, wait for it to show up
        for i in range(0, TIMEOUT):
            print ("Checking for reviewapp spawn...")
            reviewapp = get_review_app_by_id( pipeline['id'], reviewapp_id )
            if reviewapp is not None:
                app_id = reviewapp['app']['id']
                break
            time.sleep(1)
            if i == TIMEOUT:
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
        # this is a related app, deploy it as a into the development pipeline phase
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
        for i in range(0, TIMEOUT):
            print ("Checking for app spawn...")
            app_setup = get_app_setup_by_id( app_setup['id'] )
            if app_setup is not None:
                app_id = app_setup['app']['id']
                break
            time.sleep(1)
            if i == TIMEOUT:
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

    # grant access to all users
    users = get_team_members( args['HEROKU_TEAM_NAME'] )
    for email in [ x['email'] for x in users ]:
        print(grant_review_app_access_to_user( app_name, email ))

message = 'Deployed app <a href="https://%s.herokuapp.com">%s</a> - [ <a href="https://dashboard.heroku.com/apps/%s">app: %s</a> | <a href="https://dashboard.heroku.com/apps/%s/logs">logs</a> ]<br>' % (app_name, app_short_name, app_name, app_name, app_name)
print (message)
print ("Done.")
