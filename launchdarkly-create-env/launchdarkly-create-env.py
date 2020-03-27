#!/usr/bin/env python3

import json
import os
import requests
import sys
import urllib.parse
import traceback

# some constants
LABEL_NAME = 'review-env'

# tokens
HEROKU_TOKEN = os.environ['HEROKU_API_TOKEN']
LAUNCHDARKLY_SDK_TOKEN = os.environ['LAUNCHDARKLY_SDK_TOKEN']
GHA_USER_TOKEN = os.environ['GHA_USER_TOKEN']

# invoke only when a label is added?
REQUIRE_LABEL = (os.environ['USE_LABEL'].lower() == 'true') if 'USE_LABEL' in os.environ.keys() else False

# basic headers for communicating with the Heroku API
HEADERS_HEROKU = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
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

# Launchdarkly API url
LAUNCHDARKLY_PROJECT_ID = os.environ['LAUNCHDARKLY_PROJECT_ID']
APP_NAME = os.environ['APP_NAME']

API_URL_LAUNCHDARKLY =  'https://app.launchdarkly.com/api/v2/projects/%s' % LAUNCHDARKLY_PROJECT_ID

# basic headers for communicating with the Launchdarkly API
HEADERS_LAUNCHDARKLY = {
    'Authorization': LAUNCHDARKLY_SDK_TOKEN,
    'Content-Type': 'application/json',
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
}

# GitHub Related Functions #####################################################

def get_latest_commit_for_branch( repo, branch_name ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/branches/'+urllib.parse.quote(branch_name), headers=HEADERS_GITHUB)
    branch = json.loads(r.text)
    try:
        return branch['commit']['sha']
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        return None

def get_pr_by_name( repo, branch_name, page=1 ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/pulls?state=all&page='+str(page)+'&per_page=100', headers=HEADERS_GITHUB)
    prs = json.loads(r.text)
    try:
        pr = next((x for x in prs if x['head']['ref'] == branch_name), None)
        if pr:
            return pr
        else:
            return get_pr_by_name( repo, branch_name, page=page+1)
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        return None

# Heroku Related Functions #####################################################

def set_launchdarkly_sdk_env( ld_sdk_key, app_name ):
    config_vars = { 'LAUNCHDARKLY_SDK_KEY': ld_sdk_key }
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_name+'/config-vars', headers=HEADERS_HEROKU, data=json.dumps(config_vars))
    if r.status_code != 200:
        print('Error: Could not set Launchdarkly SDK key for %s %s' % (APP_NAME, r.text))

# Launchdarkly API functions ####################################################

def get_launchdarkly_env_sdk_key(app_name):
    payload =     {
      'name': app_name,
      'key': app_name,
      'color': "bfd7ef"
    }

    r = requests.post(API_URL_LAUNCHDARKLY+'/environments', headers=HEADERS_LAUNCHDARKLY, data=json.dumps(payload))

    if r.status_code == 201:
        response = json.loads(r.text)
        return response['apiKey']
    elif r.status_code == 409:
        return find_existing_launchdarkly_api_key(app_name)
    else:
        sys.exit('Error communicating with the Launchdarkly API: %s' % r.text)

def find_existing_launchdarkly_api_key(app_name):
    r = requests.get(API_URL_LAUNCHDARKLY+'/environments/'+app_name, headers=HEADERS_LAUNCHDARKLY)

    if r.status_code == 200:
        response = json.loads(r.text)
        return response['apiKey']
    else:
        sys.exit('Error communicating with the Launchdarkly API: %s' % r.text)

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

# get the github event json
if 'GITHUB_EVENT_PATH' in os.environ:
    EVENT_FILE = os.environ['GITHUB_EVENT_PATH']
    with open(EVENT_FILE, 'r', encoding="utf-8") as eventfile:
        GH_EVENT = json.load(eventfile)

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
# APP_PREFIX=trr HEROKU_TEAM_NAME=therealreal APP_NAME=api-gateway APP_ORIGIN=api
args_or_envs = [
    'APP_PREFIX',
    'HEROKU_TEAM_NAME',
    'APP_NAME',
    'CONNECTED_APPS',
    'APP_ORIGIN'
]
for i in args_or_envs:
    if i not in args and i in os.environ:
        args[i] = os.environ[i]

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

# determine the app_short_name - short name that references the type of service
app_short_name = args['APP_NAME']
print ("Service Name: "+app_short_name)

# if this APP_ORIGIN is not specified, then we are deploying the originating
# service. Fill in the value of this var just for ease of use.
app_origin = app_short_name
if 'APP_ORIGIN' in args:
    app_origin = args['APP_ORIGIN']
print("Originating Service: "+app_origin)

# pull branch name from the GITHUB_REF
try:
    branch_origin = GH_EVENT['pull_request']['head']['ref'] # this has been more reliable
except:
    branch_origin = os.environ['GITHUB_REF'][11:] # this is sometimes wrong

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# we always need to know the originating repo:
repo_origin = os.environ['GITHUB_REPOSITORY']

repo = repo_origin
branch = branch_origin

github_org = repo.split('/')[0]
print ("GitHub Org: "+github_org)
print ("Repo: "+repo)
print ("Branch to deploy: "+branch)

# DETERMINE THE APP NAME #######################################################

try:
    # we expect that the event payload has a pull_request object at the first level
    pr = GH_EVENT['pull_request']
except:
    try:
        # look up the PR number for origin repo
        pr = get_pr_by_name( repo_origin, branch_origin )
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        sys.exit("Couldn't find a PR for this branch - %s@%s" % (repo_origin, branch_origin))

pr_num = pr['number']
pr_labels = [x['name'] for x in pr['labels']]
pr_status = pr['state']
print ("Found Pull Request: \"%s\" id: %s (%s)" % (pr['title'].encode('utf-8'), pr_num, pr_status))

# determine the app_name
app_name = get_app_name( app_origin, app_short_name, pr_num, app_prefix )

print ("App Name: "+app_name)


# if this is not a labelled PR
print ("Detected Labels: " + ', '.join(pr_labels))
if ( REQUIRE_LABEL and LABEL_NAME not in pr_labels ):
    if get_app_by_name_or_id( app_name ):
        # if app is already spun up, shut it down
        print("Spinning down app "+app_name)
        delete_app_by_name( app_name )
    elif REQUIRE_LABEL:
        # If nothing is spun up so far, but labels are required
        print("To spin up a review environment, label your open pr with "+LABEL_NAME)
    elif pr_status == 'closed':
        print("This PR is currently closed.")
    else:
        print("Quitting. Either label missing or PR is closed.")
    sys.exit(0)

# Set Lauchdarkly SDK key for review env #########################################################

print ("Start "+sys.argv[0])
def mask( k, v ):
    if 'TOKEN' in k or 'SECRET' in k:
        return '***'
    else:
        return v
print ("Environment: " + str({k: mask(k,v) for k, v in os.environ.items()}))

# Find or Create the Launchdarkly env for this review-env
ld_sdk_key = get_launchdarkly_env_sdk_key(app_name)
print (ld_sdk_key)

# attach the addon to apps
app_short_names = args['CONNECTED_APPS'].split(',')
print ("Attaching Launchdarkly environment %s to multiple apps: %s" % (app_name, ','.join(app_short_names)))

for attach_app_shortname in app_short_names:
    attach_app_name = get_app_name( app_origin, attach_app_shortname, pr_num, app_prefix )
    print ("Attaching Launchdarkly environment %s to %s..." % (app_name, attach_app_name))
    set_launchdarkly_sdk_env(ld_sdk_key, attach_app_name)

print ("Done.")
