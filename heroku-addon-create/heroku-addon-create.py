#!/usr/bin/env python3

import json
import os
import requests
import re
import sys
import time

# some constants
timeout = 20
app_domain_suffix = '.herokuapp.com'
label_name = 'review-env'

# tokens
github_token = os.environ['GITHUB_TOKEN']
heroku_token = os.environ['HEROKU_API_TOKEN']

# Heroku Related Functions #####################################################

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

def get_review_app_by_id( pipeline_id, id ):
    r = requests.get(api_url_heroku+'/pipelines/'+pipeline_id+'/review-apps', headers=headers_heroku)
    reviewapps = json.loads(r.text)
    reviewapp = next((x for x in reviewapps if x['id'] == id), None)
    try:
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except:
        pass
    return None

def get_app_setup_by_id( app_setup_id ):
    r = requests.get(api_url_heroku+'/app-setups/'+app_setup_id, headers=headers_heroku)
    app_setup = json.loads(r.text)
    return app_setup

def delete_app_by_name( app_name ):
    if '-pr-' not in app_name:
        sys.exit("Tried to delete app "+app_name+" - refusing for safety's sake.")
    r = requests.delete(api_url_heroku+'/apps/'+app_name, headers=headers_heroku)
    response = json.loads(r.text)
    return response

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

def get_app_by_id( app_id ):
    r = requests.get(api_url_heroku+'/apps', headers=headers_heroku)
    apps = json.loads(r.text)
#    print(json.dumps(apps, sort_keys=True, indent=4))
    app = next((x for x in apps if x['id'] == app_id), None)
    try:
        if app is not None and 'id' in app:
            return app
    except:
        pass
    return None

def rename_app( app_id, app_name ):
    r = requests.patch(api_url_heroku+'/apps/'+app_id, headers=headers_heroku, data=json.dumps( {'name': app_name[:30]} ))
    return r.status_code is 200

def get_pipeline_by_name( pipeline_name ):
    r = requests.get(api_url_heroku+'/pipelines', headers=headers_heroku)
    pipelines = json.loads(r.text)
    pipeline = next((x for x in pipelines if x['name'] == pipeline_name), None)
    if pipeline is not None and 'id' in pipeline:
        return pipeline
    else:
        return None

def get_download_url( repo, branch, token ):
    # pulls the 302 location out of the redirect
    download_url = 'https://api.github.com/repos/'+repo+'/tarball/'+branch+'?access_token='+token
    try:
        r = requests.get(download_url, allow_redirects=False)
        if r.status_code == 302:
            return r.headers['location']
    except:
        pass
    return None

def create_team_app( name, team ):
    r = requests.post(api_url_heroku+'/teams/apps', headers=headers_heroku, data=json.dumps( {'name': name, 'team': team} ))
    app = json.loads(r.text)
    print(json.dumps(app, sort_keys=True, indent=4))
    if 'id' in app:
        return app
    else:
        return None

def create_app_setup( name, team, source_code_tgz_url, commit_sha, envs ):
    payload = {
        'source_blob': {
            'url': source_code_tgz_url,
            'version': commit_sha,
        },
        'app': {
            'name': name,
            'organization': team
        },
        'overrides': {
            'env': envs
        }
    }
    print(json.dumps(payload, sort_keys=True, indent=4))
    r = requests.post(api_url_heroku+'/app-setups', headers=headers_heroku, data=json.dumps(payload))
    app_setup = json.loads(r.text)
    print(json.dumps(app_setup, sort_keys=True, indent=4))
    if 'id' in app_setup:
        return app_setup
    else:
        return None

def add_to_pipeline( pipeline_id, app_id, stage ):
    payload = {
        'app': app_id,
        'pipeline': pipeline_id,
        'stage': stage if stage in [ 'test',' review', 'development', 'staging', 'production' ] else 'development'
    }
    r = requests.post(api_url_heroku+'/pipeline-couplings', headers=headers_heroku, data=json.dumps(payload))
    coupling = json.loads(r.text)
    print(json.dumps(coupling, sort_keys=True, indent=4))
    if 'created_at' in coupling:
        return True
    else:
        return None

def deploy_to_app( app_id, source_code_tgz_url, commit_sha ):
    payload = {
        'source_blob': {
            'url': source_code_tgz_url,
            'version': commit_sha,
        },
    }
    r = requests.post(api_url_heroku+'/apps/'+app_id+'/builds', headers=headers_heroku, data=json.dumps(payload))
    response = json.loads(r.text)
    if 'status' in response:
        return response
    else:
        return None

def get_features_for_app( app_id ):
    r = requests.get(api_url_heroku+'/apps/'+app_id+'/features', headers=headers_heroku)
    features = json.loads(r.text)
    try:
        if features[0]['id'] and features[0]['doc_url']:
            return features
    except:
        pass
    return None

def get_config_vars_for_app( app_id ):
    r = requests.get(api_url_heroku+'/apps/'+app_id+'/config-vars', headers=headers_heroku)
    config_vars = json.loads(r.text)
    return config_vars

def set_config_vars_for_app( app_id, config_vars ):
    r = requests.patch(api_url_heroku+'/apps/'+app_id+'/config-vars', headers=headers_heroku, data=json.dumps(config_vars))
    result = json.loads(r.text)
    if r.status_code != 200:
        return None
    for key, value in result.items():
        if key in config_vars and result[key] != config_vars[key]:
            return None
    return config_vars

def add_buildpacks_to_app( app_id, buildpack_urls ):
    buildpack_changes = {
        'updates': [{ 'buildpack': x } for x in buildpack_urls]
    }
    buildpack_changes['updates']
    r = requests.put(api_url_heroku+'/apps/'+app_id+'/buildpack-installations', headers=headers_heroku, data=json.dumps(buildpack_changes))
    result = json.loads(r.text)
    if r.status_code != 200:
        return None
    return result

def get_review_app_config_vars_for_pipeline( pipeline_id, stage ):
    r = requests.get(api_url_heroku+'/pipelines/'+pipeline_id+'/stage/'+stage+'/config-vars', headers=headers_heroku_review_pipelines)
    config_vars = json.loads(r.text)
    return config_vars

def grant_review_app_access_to_user( app_name, email ):
    payload = {
        'user': email,
        'permissions': ['view', 'deploy', 'operate'],
        'silent': True
    }
    r = requests.post(api_url_heroku+'/teams/apps/'+app_name+'/collaborators', headers=headers_heroku_review_pipelines, data=json.dumps(payload))
    return json.loads(r.text)

def get_team_members( team_name ):
    r = requests.get(api_url_heroku+'/teams/'+team_name+'/members', headers=headers_heroku_review_pipelines)
    team_members = json.loads(r.text)
    return team_members

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

# basic headers for communicating with the GitHub API
headers_github = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % github_token,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
api_url_github = 'https://api.github.com'

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
    if get_app_by_name( app_name ):
        # if app is already spun up, shut it down
        print("Spinning down app "+app_name)
        delete_app_by_name( app_name )
    else:
        # If nothing is spun up so far
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
        print("Addon %s (%s) has already been added to %s." % (args['ADDON_NAME'], args['ADDON_PLAN'], app_name))

    else:
        # spin up a kafka addon for this app
        print ("Creating addon %s (%s) for app %s..." % ( args['ADDON_NAME'], args['ADDON_PLAN'], app_name ))
        addon = create_addon( app_name, args['ADDON_NAME'], args['ADDON_PLAN'] )
        print(json.dumps(addon, sort_keys=True, indent=4))
        if 'name' not in addon or addon['name'] != args['ADDON_NAME']:
            sys.exit("Couldn't create the addon.")

        # attach the addon to apps
        app_short_names = args['RELATED_APPS'].split(',')
        app_short_names.append(app_origin)
        print ("Attaching %s (%s) addon to multiple apps: %s" % (args['ADDON_NAME'], args['ADDON_PLAN'], ','.join(app_short_names)))

        for attach_app_shortname in app_short_names:
            attach_app_name = get_app_name( app_origin, attach_app_shortname, pr_num, app_prefix ),
            print ("Attaching %s (%s) addon to %s..." % (args['ADDON_NAME'], args['ADDON_PLAN'], attach_app_name))
            attachment = attach_addon( attach_app_name, args['ADDON_NAME'], kafka_addon['name'] )
            if 'name' not in attachment:
                sys.exit("Couldn't attach addon %s (%s) to app %s" % (args['ADDON_NAME'], args['ADDON_PLAN'], app_name ))

else:
    sys.exit("Found no existing app: %s." % app_name)


print ("Done.")
