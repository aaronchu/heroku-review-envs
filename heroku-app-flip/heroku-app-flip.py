#!/usr/bin/env python3

import json
import os
import re
import requests
import sys

# okta token
OKTA_API_TOKEN = os.environ['OKTA_API_TOKEN']
OKTA_API_TOKEN_NINJA = os.environ['OKTA_API_TOKEN_NINJA']

# okta url
OKTA_API_URL = os.environ['OKTA_API_URL']
OKTA_API_URL_NINJA = os.environ['OKTA_API_URL_NINJA']

# okta client variables
OKTA_CLIENT_ID = "0oa18r3unfqJuF9Y4357"
OKTA_CLIENT_ID_NINJA = "0oalprgcvn7yBQMUU0h7"
OKTA_CLIENT_SECRET = "U-ackKnkWn5EzP7q-3jB0Dx38uVPW8h1IqsT902h"
OKTA_CLIENT_SECRET_NINJA = "6ajCVmbL-gvQtFdkv5knN3ATFJ6mwBnGxkZa-I5o"

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

# support arguments passed in via the github actions workflow via the syntax
# args = ["HEROKU_PIPELINE_NAME=github-actions-test"]
args = {}
for arg in sys.argv:
    pair = arg.split('=')
    if len(pair) > 1:
        args[pair[0]] = '='.join(pair[1:])
    else:
        args[arg] = arg

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

domain = args['OKTA_DOMAIN']
svc = args['APP_ORIGIN']
# pr_num = args['PR_NUM']

if 'GITHUB_EVENT_PATH' in os.environ:
    EVENT_FILE = os.environ['GITHUB_EVENT_PATH']
    with open(EVENT_FILE, 'r', encoding="utf-8") as eventfile:
        GH_EVENT = json.load(eventfile)

pr = GH_EVENT['pull_request']
pr_num = pr['number']

# functions
def build_headers( domain ):
    token = OKTA_API_TOKEN if domain == "com" else OKTA_API_TOKEN_NINJA

    return {
        'Accept': 'application/json',
        'Authorization': 'SSWS %s' % token,
        'Content-Type': 'application/json'
        }

def build_url( domain ):
    return OKTA_API_URL if domain == "com" else OKTA_API_URL_NINJA

def get_okta_data( domain ):
    r = requests.get(build_url(domain), headers=build_headers(domain))
    return json.loads(r.text)

def put_okta_data( domain, data ):
    del data['client_secret_expires_at']
    del data['client_id_issued_at']

    try:
        r = requests.put(build_url(domain), headers=build_headers(domain), data=json.dumps(data))
        if r.status_code == 200:
            print('Successfully updated the .%s whitelist.' % ( domain ))
        else:
            print('There was a problem updating the .%s whitelist. Status code: %d' % ( domain, r.status_code ))
    except requests.exceptions.RequestException as e:
        print('An exception occured when updating the %s whitelist. Exception: %s' % ( domain, str(e) ))

def get_app_name( svc_origin, svc_target, pr_num ):
    if svc_origin == svc_target:
        app_name = "trr-%s-pr-%s" % ( svc_origin, pr_num )
    else:
        app_name = "trr-%s-pr-%s-%s" % ( svc_origin, pr_num, svc_target )

    return app_name

def get_redirect_uris( domain ):
    redirect_uris = get_okta_data(domain)['redirect_uris']

    # filter list to redirect uris for review environments
    regex = re.compile(r"https\:\/\/trr-([a-z\-]+)-pr-([0-9]+)(-web)?\.herokuapp\.com\/admin\/okta", re.IGNORECASE)
    return list(filter(regex.search, redirect_uris))

def add_whitelist_uri( domain, redirect_uri ):
    review_environment_redirect_uris = get_redirect_uris(domain)

    if redirect_uri in review_environment_redirect_uris:
        print("Redirect URI %s already whitelisted for .%s, doing nothing" % ( redirect_uri, domain ))
    else:
        print("Redirect URI %s not whitelisted for .%s, adding" % ( redirect_uri, domain ))

        data = get_okta_data(domain)
        redirect_uris = data['redirect_uris']
        redirect_uris.append(redirect_uri)

        put_okta_data(domain, data)


def remove_whitelist_uri( domain, redirect_uri ):
    review_environment_redirect_uris = get_redirect_uris(domain)

    if redirect_uri not in review_environment_redirect_uris:
        print("Redirect URI %s not whitelisted for .%s, doing nothing" % ( redirect_uri, domain ))
    else:
        print("Redirect URI %s whitelisted for .%s, removing" % ( redirect_uri, domain ))

        data = get_okta_data(domain)
        redirect_uris = data['redirect_uris']
        redirect_uris.remove(redirect_uri)

        put_okta_data(domain, data)

def set_config_vars( app_name, config_vars ):
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_name+'/config-vars', headers=HEADERS_HEROKU, data=json.dumps(config_vars))
    if r.status_code != 200:
        sys.exit("There was an error setting config vars for %s - %s" % ( app_name, r.status_code ))

# validations

if domain not in ["com", "ninja"]:
    sys.exit("Invalid domain arg '%s'. Must be either 'com' or 'ninja'" % ( domain ))

if svc not in ["web", "api", "api-gateway", "website", "inventory"]:
    sys.exit("Invalid svc arg '%s'. Must be either 'web', 'api', 'api-gateway', 'website', or 'inventory" % ( svc ))

if not pr_num.isdigit():
    sys.exit("Invalid pr_num arg '%s'. Must be a positive number" % ( pr_num ))

# local variables

redirect_uri = "https://%s.herokuapp.com/admin/okta" % get_app_name(svc, "web", pr_num)
opposite_domain = "com" if domain == "ninja" else "ninja"
auth_server_base_url = "https://login.therealreal." + domain + "/oauth2/default/"
client_id = OKTA_CLIENT_ID if domain == "com" else OKTA_CLIENT_ID_NINJA
client_secret = OKTA_CLIENT_SECRET if domain == "com" else OKTA_CLIENT_SECRET_NINJA
web_app_name = get_app_name(svc, "web", pr_num)
api_app_name = get_app_name(svc, "api", pr_num)
web_config_vars = {
    "OKTA_AUTH_SERVER_BASE_URL": auth_server_base_url,
    "OKTA_CLIENT_ID": client_id,
    "OKTA_CLIENT_SECRET": client_secret
}
api_config_vars = {
    "AUTHORIZATION_OKTA_BASE_URL": auth_server_base_url + "v1/",
    "AUTHORIZATION_OKTA_CLIENT_ID": client_id,
    "AUTHORIZATION_OKTA_CLIENT_SECRET": client_secret
}

# main script

print("\nFlipping %s PR #%s to %s\n" % ( svc, pr_num, domain ))

print("Start - Adding to .%s whitelist" % ( domain ))
add_whitelist_uri(domain, redirect_uri)
print("Done  - Adding to .%s whitelist\n" % ( domain ))

print("Start - Removing from .%s whitelist" % ( opposite_domain ))
remove_whitelist_uri(opposite_domain, redirect_uri)
print("Done  - Removing from .%s whitelist\n" % ( opposite_domain ))

print("Start - Setting 'web' Config Vars")
set_config_vars( web_app_name, web_config_vars )
print("Done  - Setting 'web' Config Vars\n")

print("Start - Setting 'api' Config Vars")
set_config_vars( api_app_name, api_config_vars )
print("Done  - Setting 'api' Config Vars\n")


