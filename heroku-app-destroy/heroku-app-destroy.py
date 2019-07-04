#!/usr/bin/env python3

import json
import os
import requests
import re
import sys

# get the event payload
GITHUB_EVENT_PATH = os.environ['GITHUB_EVENT_PATH']

# tokens
HEROKU_TOKEN = os.environ['HEROKU_API_TOKEN']

# basic headers for communicating with the Heroku API
HEADERS_HEROKU = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
    'Authorization': 'Bearer %s' % HEROKU_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
API_URL_HEROKU = 'https://api.heroku.com'

# Heroku Related Functions #####################################################

def delete_app_by_name( app_name ):
    if '-pr-' not in app_name:
        sys.exit("Tried to delete app "+app_name+" - refusing for safety's sake.")
    r = requests.delete(API_URL_HEROKU+'/apps/'+app_name, headers=HEADERS_HEROKU)
    response = json.loads(r.text)
    return response

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
    'HEROKU_TEAM_NAME',
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

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# DETERMINE THE APP NAME #######################################################

# look up the PR number for origin repo
payload = None
print( GITHUB_EVENT_PATH )
if os.path.exists( GITHUB_EVENT_PATH ):
    print( "%s exists." % GITHUB_EVENT_PATH)
with open( GITHUB_EVENT_PATH, 'r', encoding="utf-8" ) as payload_file:
    payload_data = payload_file.read()
    print(''.join( [c for c in payload_data if 0 < ord(c) < 127] )
    payload = json.loads(payload_data)
if payload is None:
    sys.exit("Couldn't get the PR number for this PR.")
pr_num = payload['number']

# determine the app_name
app_name = get_app_name( app_origin, app_short_name, pr_num, app_prefix )

print ("App Name: "+app_name)

result = delete_app_by_name( app_name )

print(json.dumps(result, sort_keys=True, indent=4))

print ("Done.")
