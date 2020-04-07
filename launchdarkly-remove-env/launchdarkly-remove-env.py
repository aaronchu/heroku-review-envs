#!/usr/bin/env python3

import json
import os
import requests
import re
import sys

# constants
NEUTRAL_EXIT_CODE = 78

# get the event payload
GITHUB_EVENT_PATH = os.environ['GITHUB_EVENT_PATH']

LAUNCHDARKLY_SDK_TOKEN = os.environ['LAUNCHDARKLY_SDK_TOKEN']

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

# Launchdarkly API functions ####################################################

def remove_launchdarkly_env(app_name):
    r = requests.delete(API_URL_LAUNCHDARKLY+'/environments/'+app_name, headers=HEADERS_LAUNCHDARKLY)

    if r.status_code == 204:
        return "Environment Deleted."
    else:
        return "Environment not found, previously deleted."

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
    # if required transform origin repo name into app name
    if app_origin == "real-server":
        app_origin = "web"
    if app_origin == "inventory-service":
        app_origin = "inventory"
print("Originating Service: "+app_origin)

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# DETERMINE THE APP NAME #######################################################

# look up the PR number for origin repo
payload = None
with open( GITHUB_EVENT_PATH, 'r', encoding="utf-8" ) as payload_file:
    payload_data = payload_file.read()
    payload = json.loads(payload_data)
    print( "GitHub Event Payload:" )
    print(json.dumps(payload, sort_keys=True, indent=4))
if payload is None:
    print( "Could not get GitHub Event Payload" )
    # don't fail the action, as it'll cause the rest of the pipeline to be cancelled
    sys.exit( NEUTRAL_EXIT_CODE )
pr_num = payload['number']

# determine the app_name
app_name = get_app_name( app_origin, app_short_name, pr_num, app_prefix )

print ("App Name: "+app_name)

result = remove_launchdarkly_env( app_name )

print ("Result of Deletion:" )
print( result )

print ("Done.")
