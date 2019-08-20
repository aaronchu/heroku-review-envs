#!/usr/bin/env python3

import json
import os
import requests
import sys

# some constants
TIMEOUT = 20

# tokens
OKTA_API_TOKEN = os.environ['OKTA_API_TOKEN']
OKTA_CLIENT_ID = os.environ['OKTA_CLIENT_ID']

# basic headers for communicating with the GitHub API
HEADERS_OKTA = {
    'Accept': 'application/json',
    'Authorization': 'SSWS %s' % OKTA_API_TOKEN,
    'Content-Type': 'application/json'
    }
API_URL_OKTA = 'https://therealreal.oktapreview.com/oauth2/v1/clients/%s' % OKTA_CLIENT_ID

# Placeholder const for the actual URI to add
REVIEW_ENV_URI = 'https://trr-web-pr-123456.herokuapp.com/admin/okta'

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

# START UPDATING WHITELIST #####################################################

print ("Starint Okta Whitelist URL Create")

r = requests.get(API_URL_OKTA, headers=HEADERS_OKTA)
client = json.loads(r.text)

redirect_uris = client['redirect_uris']

if not any(REVIEW_ENV_URI in s for s in redirect_uris):
  print ('The URI %s is NOT whitelisted. Adding it to the whitelist now!' % REVIEW_ENV_URI)
  redirect_uris.append(REVIEW_ENV_URI)
  del client['client_secret_expires_at']
  del client['client_id_issued_at']

  r2 = requests.put(API_URL_OKTA, headers=HEADERS_OKTA, data=json.dumps(client))

  if r2.status_code == 200:
    print ('The URI %s has been added to the whitelist!' % REVIEW_ENV_URI)
  else:
    print ('There was a problem adding the URI %s to the whitelist. Please investigate.')
else:
  print ('The URI %s is already whitelisted' % REVIEW_ENV_URI)
