#!/usr/bin/env python3

import json
import os
import re
import requests
import sys

# okta token
OKTA_API_TOKEN = os.environ['OKTA_API_TOKEN']
OKTA_API_TOKEN_ALT = os.environ['OKTA_API_TOKEN_ALT']

# okta url
OKTA_API_URL = os.environ['OKTA_API_URL']
OKTA_API_URL_ALT = os.environ['OKTA_API_URL_ALT']

# functions
def build_headers( target ):
    token = OKTA_API_TOKEN if target == 'main' else OKTA_API_TOKEN_ALT

    return {
        'Accept': 'application/json',
        'Authorization': 'SSWS %s' % token,
        'Content-Type': 'application/json'
        }

def build_url( target ):
    return OKTA_API_URL if target == 'main' else OKTA_API_URL_ALT

def get_okta_data( target ):
    r = requests.get(build_url(target), headers=build_headers(target))
    return json.loads(r.text)

def put_okta_data( target, data ):
    del data['client_secret_expires_at']
    del data['client_id_issued_at']

    try:
        r = requests.put(build_url(target), headers=build_headers(target), data=json.dumps(data))
        if r.status_code == 200:
            print('Successfully updated the whitelist.')
        else:
            print('There was a problem updating the whitelist. Status code: %d' % ( r.status_code ))
    except requests.exceptions.RequestException as e:
        print('An exception occured when updating the whitelist. Exception: %s' % ( str(e) ))

def get_app_name( svc_origin, svc_target, pr_num, prefix ):
    if svc_origin == svc_target:
        app_name = "%s-%s-pr-%s" % ( prefix, svc_origin, pr_num )
    else:
        app_name = "%s-%s-pr-%s-%s" % ( prefix, svc_origin, pr_num, svc_target )

    return app_name

def get_redirect_uris( target ):
    redirect_uris = get_okta_data(target)['redirect_uris']

    # filter list to redirect uris for review environments
    regex = re.compile(r"https\:\/\/trr-([a-z\-]+)-pr-([0-9]+)(-web)?\.herokuapp\.com\/admin\/okta", re.IGNORECASE)
    return list(filter(regex.search, redirect_uris))

def add_whitelist_uri( target, redirect_uri ):
    review_environment_redirect_uris = get_redirect_uris(target)

    if redirect_uri in review_environment_redirect_uris:
        print("Redirect URI %s already whitelisted, doing nothing" % ( redirect_uri ))
    else:
        print("Redirect URI %s not whitelisted, adding" % ( redirect_uri ))

        data = get_okta_data(target)
        redirect_uris = data['redirect_uris']
        redirect_uris.append(redirect_uri)

        put_okta_data(target, data)


def remove_whitelist_uri( target, redirect_uri ):
    review_environment_redirect_uris = get_redirect_uris(target)

    if redirect_uri not in review_environment_redirect_uris:
        print("Redirect URI %s not whitelisted, doing nothing" % ( redirect_uri ))
    else:
        print("Redirect URI %s whitelisted, removing" % ( redirect_uri ))

        data = get_okta_data(target)
        redirect_uris = data['redirect_uris']
        redirect_uris.remove(redirect_uri)

        put_okta_data(target, data)

# arguments

args = {}
for arg in sys.argv:
    pair = arg.split('=')
    if len(pair) > 1:
        args[pair[0]] = '='.join(pair[1:])
    else:
        args[arg] = arg

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

okta_target = args['OKTA_TARGET']
app_prefix = args['APP_PREFIX']
app_origin = args['APP_ORIGIN']
app_target = args['APP_TARGET']
url_target = args['URL_TARGET']
# pr_num = args['PR_NUM']

if 'GITHUB_EVENT_PATH' in os.environ:
    EVENT_FILE = os.environ['GITHUB_EVENT_PATH']
    with open(EVENT_FILE, 'r', encoding="utf-8") as eventfile:
        GH_EVENT = json.load(eventfile)

pr = GH_EVENT['pull_request']
pr_num = pr['number']

# validations

if okta_target not in ["main", "alt"]:
    sys.exit("Invalid okta_target arg '%s'. Must be either 'main' or 'alt'" % ( okta_target ))

# local variables

redirect_uri = url_target % get_app_name(app_origin, app_target, pr_num, app_prefix)
opposite_okta_target = "main" if okta_target == "alt" else "alt"

# main script

print("Start - Adding to %s whitelist" % ( okta_target ))
add_whitelist_uri(okta_target, redirect_uri)
print("Done  - Adding to %s whitelist\n" % ( okta_target ))

print("Start - Removing from %s whitelist" % ( opposite_okta_target ))
remove_whitelist_uri(opposite_okta_target, redirect_uri)
print("Done  - Removing from %s whitelist\n" % ( opposite_okta_target ))
