#!/usr/bin/env python3

import json
import os
import requests
import sys

# tokens
OKTA_API_TOKEN = os.environ['OKTA_API_TOKEN']
OKTA_API_URL = os.environ['OKTA_API_URL']
OKTA_API_TOKEN_NINJA = os.environ['OKTA_API_TOKEN_NINJA']
OKTA_API_URL_NINJA = os.environ['OKTA_API_URL_NINJA']
GHA_USER_TOKEN = os.environ['GHA_USER_TOKEN']

# basic headers for communicating with the GitHub API
HEADERS_GITHUB = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % GHA_USER_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
API_URL_GITHUB = 'https://api.github.com'

# Non-API-Related Functions ####################################################

def get_app_name( svc_origin, svc_target, pr_num, prefix ):
    if svc_origin == svc_target:
      name = "%s-%s-pr-%s" % ( prefix, svc_origin, pr_num )
    else:
      name = "%s-%s-pr-%s-%s" % ( prefix, svc_origin, pr_num, svc_target )
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
args_or_envs = [
    'APP_PREFIX',
    'APP_ORIGIN',
    'APP_TARGET',
    'URL_TARGET'
]
for i in args_or_envs:
    if i not in args and i in os.environ:
        args[i] = os.environ[i]

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

# GET THE INPUTS SET UP RIGHT ##################################################

app_origin = args['APP_ORIGIN']
print("Originating Service: "+app_origin)

app_target = args['APP_TARGET']
print("Target Service: "+app_target)

# set the Okta API URL and API Token
has_ninja_label = args['HAS_NINJA_LABEL']
okta_api_url = OKTA_API_URL_NINJA if has_ninja_label else OKTA_API_URL
okta_api_token = OKTA_API_TOKEN_NINJA if has_ninja_label else OKTA_API_TOKEN

# basic headers for communicating with the Okta API
headers_okta = {
    'Accept': 'application/json',
    'Authorization': 'SSWS %s' % okta_api_token,
    'Content-Type': 'application/json'
    }

# pull branch name from the GITHUB_REF
try:
    branch_origin = GH_EVENT['pull_request']['head']['ref'] # this has been more reliable
except:
    branch_origin = os.environ['GITHUB_REF'][11:] # this is sometimes wrong

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# we always need to know the originating repo:
repo_origin = os.environ['GITHUB_REPOSITORY']

# DETERMINE THE APP NAME #######################################################

try:
    # we expect that the event payload has a pull_request object at the first level
    pr = GH_EVENT['pull_request']
except Exception as ex:
    print(ex)
    sys.exit("Couldn't find a PR for this branch - " + repo_origin + '@' + branch_origin)

pr_num = pr['number']
pr_labels = [x['name'] for x in pr['labels']]
pr_status = pr['state']
print ("Found Pull Request: \"" + pr['title'] + "\" id: " + str(pr_num))

# determine the app_name
app_name = get_app_name( app_origin, app_target, pr_num, app_prefix )

print ("App Name: " + app_name)

# START UPDATING WHITELIST #####################################################

print ("Starint Okta Whitelist URL Destroy")

uri_to_remove = args['URL_TARGET'] % app_name

r = requests.get(okta_api_url, headers=headers_okta)
client = json.loads(r.text)

redirect_uris = client['redirect_uris']

if any(uri_to_remove in s for s in redirect_uris):
  print ('The URI %s is whitelisted. Removing it from the whitelist now!' % uri_to_remove)
  redirect_uris.remove(uri_to_remove)
  del client['client_secret_expires_at']
  del client['client_id_issued_at']

  r2 = requests.put(okta_api_url, headers=headers_okta, data=json.dumps(client))

  if r2.status_code == 200:
    print ('The URI %s has been removed from the whitelist!' % uri_to_remove)
  else:
    print ('There was a problem removing the URI %s from the whitelist. Please investigate.')
else:
  print ('The URI %s is NOT whitelisted' % uri_to_remove)
