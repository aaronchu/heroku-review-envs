#!/usr/bin/env python3

import json
import os
import requests
import re
import sys
import time

# some constants
label_name = 'review-env'

# tokens
heroku_token = os.environ['HEROKU_API_TOKEN']
github_token = os.environ['GITHUB_TOKEN']

# basic headers for communicating with the Heroku API
headers_heroku = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
    'Authorization': 'Bearer %s' % heroku_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
headers_heroku_review_pipelines = {
    'Accept': 'application/vnd.heroku+json; version=3.pipelines',
    'Authorization': 'Bearer %s' % heroku_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }

api_url_heroku = 'https://api.heroku.com'

# basic headers for communicating with the GitHub API
headers_github = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % github_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
api_url_github = 'https://api.github.com'

# Heroku Related Functions #####################################################

def get_review_app_by_branch( pipeline_id, branch_name ):
    r = requests.get(api_url_heroku+'/pipelines/'+pipeline_id+'/review-apps', headers=headers_heroku)
    reviewapps = json.loads(r.text)
    reviewapp = next((x for x in reviewapps if x['branch'] == branch_name), None)
    try:
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except:
        pass
    return None

def get_app_by_name( app_name ):
    r = requests.get(api_url_heroku+'/apps', headers=headers_heroku)
    apps = json.loads(r.text)
#    print(json.dumps(apps, sort_keys=True, indent=4))
    app = next((x for x in apps if x['name'] == app_name), None)
    try:
        if app is not None and 'id' in app:
            return app
    except:
        pass
    return None

def create_addon( app_name, addon_name, addon_plan, addon_config=None ):
    payload = {
        'plan': addon_plan,
        'attachment': {
            'name': addon_name
        }
    }
    if addon_config:
        payload['config'] = addon_config
    r = requests.post(api_url_heroku+'/apps/'+app_name+'/addons', headers=headers_heroku_review_pipelines, data=json.dumps(payload))
    return json.loads(r.text)

def attach_addon( app_name, addon_name, addon_id ):
    payload = {
        'addon': addon_id,
        'app': app_name,
        'name': addon_name
    }
    r = requests.post(api_url_heroku+'/addon-attachments', headers=headers_heroku_review_pipelines, data=json.dumps(payload))
    return json.loads(r.text)

def get_app_addons( app_name ):
    r = requests.get(api_url_heroku+'/apps/'+app_name+'/addon-attachments', headers=headers_heroku_review_pipelines)
    addons = json.loads(r.text)
    return addons

# GitHub Related Functions #####################################################

def get_latest_commit_for_branch( repo, branch_name ):
    r = requests.get(api_url_github+'/repos/'+repo+'/branches/'+branch_name, headers=headers_github)
    branch = json.loads(r.text)
    try:
        return branch['commit']['sha']
    except:
        return None

def get_pr_name( repo, branch_name, page=1 ):
    r = requests.get(api_url_github+'/repos/'+repo+'/pulls?state=all&page='+str(page)+'&per_page=100', headers=headers_github)
    prs = json.loads(r.text)
    pr = next((x for x in prs if x['head']['ref'] == branch_name), None)
    if pr:
        return pr
    else:
        return get_pr_name( repo, branch_name, page=page+1)

def add_pr_comment( repo, pr_id, message):
    payload = {
        'body': message
    }
    r = requests.post(api_url_github+'/repos/'+repo+'/issues/'+str(pr_id)+'/comments', headers=headers_github, data=json.dumps(payload))
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
    'HEROKU_TEAM_NAME',
    'APP_PREFIX',
    'APP_NAME',
    'RELATED_APPS',
    'ADDON_PLAN',
    'ADDON_NAME'
]
for i in args_or_envs:
    if i not in args and i in os.environ:
        args[i] = os.environ[i]

print ("Found arguments: " + str( {k: v for k, v in args.items() if 'TOKEN' not in k and 'SECRET' not in k} ))

# GET THE INPUTS SET UP RIGHT ##################################################

# determine the app_short_name - short name that references the type of service
app_short_name = args['APP_NAME']
print ("Service Name: "+app_short_name)

# APP_ORIGIN is the originating app. Fill in the value of this var just for ease of use.
app_origin = app_short_name
print("Originating Service: "+app_origin)

# pull branch name from the GITHUB_REF
branch_origin = os.environ['GITHUB_REF'][11:] # this dumps the preceding 'refs/heads/'
commit_sha = os.environ['GITHUB_SHA']
origin_commit_sha = commit_sha

# set the app name prefix properly
app_prefix = args['APP_PREFIX']

# we always need to know the originating repo:
repo_origin = os.environ['GITHUB_REPOSITORY']

# we are always deploying this using information from the origin app
repo = repo_origin
branch = branch_origin

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

# if this is not a labelled PR
print ("Detected Labels: " + ', '.join(pr_labels))
if label_name not in pr_labels or pr_status == 'closed':
    print("To spin up a review environment, label your open pr with "+label_name)
    sys.exit(0)

# START CREATING/DEPLOYING #####################################################

# see if there's a review app for this branch already
app = get_app_by_name( app_name )

app_id = None
if app is not None:
    app_id = app['id']
    print ("Found originating app id: " + app_id )

    # check existing addon attachments
    addons = get_app_addons( app_name )
    matching_addon = next((x for x in addons if x['name'] == args['ADDON_NAME']), None)

    if matching_addon:
        # no action necessary
        print("Addon %s (%s) has already been added to %s as %s." % (matching_addon['name'], args['ADDON_PLAN'], app_name, args['ADDON_NAME'] ))

    else:
        # spin up the addon for this app
        print ("Creating an addon plan = %s for app %s as %s..." % ( args['ADDON_PLAN'], app_name, args['ADDON_NAME'] ))
        addon = create_addon( app_name, args['ADDON_NAME'], args['ADDON_PLAN'] )
        print(json.dumps(addon, sort_keys=True, indent=4))
        if 'name' not in addon:
            sys.exit("Couldn't create the addon.")

        # attach the addon to apps
        app_short_names = args['RELATED_APPS'].split(',')
        print ("Attaching %s (%s) addon as %s to multiple apps: %s" % (addon['name'], args['ADDON_PLAN'], args['ADDON_NAME'], ','.join(app_short_names)))

        for attach_app_shortname in app_short_names:
            attach_app_name = get_app_name( app_origin, attach_app_shortname, pr_num, app_prefix ),
            print ("Attaching addon %s (%s) to %s as %s..." % (addon['name'], args['ADDON_PLAN'], attach_app_name, args['ADDON_NAME']))
            attachment = attach_addon( attach_app_name, args['ADDON_NAME'], addon['name'] )
            if 'name' not in attachment:
                sys.exit("Couldn't attach addon %s (%s) to app %s as %s" % (addon['name'], args['ADDON_PLAN'], app_name, args['ADDON_NAME'] ))

else:
    sys.exit("Found no existing app: %s." % app_name)

print ("Done.")
