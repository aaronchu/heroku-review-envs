#!/usr/bin/env python3

import json
import os
import requests
import sys

# heroku
HEROKU_TOKEN = os.environ['HEROKU_API_TOKEN']
API_URL_HEROKU = 'https://api.heroku.com'

# basic headers for communicating with the Heroku API
HEADERS_HEROKU = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
    'Authorization': 'Bearer %s' % HEROKU_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }

# functions
def get_app_name( svc_origin, svc_target, pr_num, prefix ):
    if svc_origin == svc_target:
        app_name = "%s-%s-pr-%s" % ( prefix, svc_origin, pr_num )
    else:
        app_name = "%s-%s-pr-%s-%s" % ( prefix, svc_origin, pr_num, svc_target )

    # truncate to 30 chars for Heroku
    return app_name[:30]

def set_config_vars( app_name, config_vars ):
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_name+'/config-vars', headers=HEADERS_HEROKU, data=json.dumps(config_vars))
    if r.status_code != 200:
        sys.exit("There was an error setting config vars for %s - %s" % ( app_name, r.status_code ))

# arguments

args = {}
for arg in sys.argv:
    pair = arg.split('=')
    if len(pair) > 1:
        args[pair[0]] = '='.join(pair[1:])
    else:
        args[arg] = arg

# print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

config_vars = {}
if 'CONFIG_VARS' in args:
    for pair in args['CONFIG_VARS'].split('|'):
        (key, value) = pair.split('%')
        config_vars[key] = value

# print("Config Vars: %s" % ( config_vars ))

app_prefix = args['APP_PREFIX']
app_origin = args['APP_ORIGIN']
app_target = args['APP_TARGET']
# pr_num = args['PR_NUM']

if 'GITHUB_EVENT_PATH' in os.environ:
    EVENT_FILE = os.environ['GITHUB_EVENT_PATH']
    with open(EVENT_FILE, 'r', encoding="utf-8") as eventfile:
        GH_EVENT = json.load(eventfile)

pr = GH_EVENT['pull_request']
pr_num = pr['number']

# local variables

app_name = get_app_name(app_origin, app_target, pr_num, app_prefix)

# main script

print("Start - Setting Config Vars on %s" % ( app_name ))
set_config_vars( app_name, config_vars )
print("Done  - Setting Config Vars on %s\n" % ( app_name ))
