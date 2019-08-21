#!/usr/bin/env python3

import json
import os
import requests
import sys

# tokens
OKTA_API_TOKEN = os.environ['OKTA_API_TOKEN']
GHA_USER_TOKEN = os.environ['GHA_USER_TOKEN']

# basic headers for communicating with the Okta API
HEADERS_OKTA = {
    'Accept': 'application/json',
    'Authorization': 'SSWS %s' % OKTA_API_TOKEN,
    'Content-Type': 'application/json'
    }
OKTA_CLIENT_ID = os.environ['OKTA_CLIENT_ID']
API_URL_OKTA = 'https://therealreal.oktapreview.com/oauth2/v1/clients/%s' % OKTA_CLIENT_ID

# basic headers for communicating with the GitHub API
HEADERS_GITHUB = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % GHA_USER_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
API_URL_GITHUB = 'https://api.github.com'

# Non-API-Related Functions ####################################################

def get_app_name( svc_origin, pr_num, prefix ):
    if svc_origin == 'web':
      name = "%s-%s-pr-%s" % ( prefix, svc_origin, pr_num )
    else:
      name = "%s-%s-pr-%s-web" % ( prefix, svc_origin, pr_num )
    # truncate to 30 chars for Heroku
    return name[:30]

# GitHub Related Functions #####################################################

def get_pr_name( repo, branch_name, page=1 ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/pulls?state=all&page='+str(page)+'&per_page=100', headers=HEADERS_GITHUB)
    prs = json.loads(r.text)
    pr = next((x for x in prs if x['head']['ref'] == branch_name), None)
    if pr:
        return pr
    else:
        return get_pr_name( repo, branch_name, page=page+1)

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
    'APP_ORIGIN'
]
for i in args_or_envs:
    if i not in args and i in os.environ:
        args[i] = os.environ[i]

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

# GET THE INPUTS SET UP RIGHT ##################################################

app_origin = args['APP_ORIGIN']
print("Originating Service: "+app_origin)

# pull branch name from the GITHUB_REF
branch_origin = os.environ['GITHUB_REF'][11:] # this dumps the preceding 'refs/heads/'

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# we always need to know the originating repo:
repo_origin = os.environ['GITHUB_REPOSITORY']

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
app_name = get_app_name( app_origin, pr_num, app_prefix )

print ("App Name: " + app_name)

# START UPDATING WHITELIST #####################################################

print ("Staring Okta Whitelist URL Create")

uri_to_add = "https://" + app_name + ".herokuapp.com/admin/okta"

r = requests.get(API_URL_OKTA, headers=HEADERS_OKTA)
client = json.loads(r.text)

redirect_uris = client['redirect_uris']

if not any(uri_to_add in s for s in redirect_uris):
  print ('The URI %s is NOT whitelisted. Adding it to the whitelist now!' % uri_to_add)
  redirect_uris.append(uri_to_add)
  del client['client_secret_expires_at']
  del client['client_id_issued_at']

  r2 = requests.put(API_URL_OKTA, headers=HEADERS_OKTA, data=json.dumps(client))

  if r2.status_code == 200:
    print ('The URI %s has been added to the whitelist!' % uri_to_add)
  else:
    print ('There was a problem adding the URI %s to the whitelist. Please investigate.')
else:
  print ('The URI %s is already whitelisted' % uri_to_add)
