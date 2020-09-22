#!/usr/bin/env python3

import json
import os
import requests
import re
import sys
import time
import traceback
import urllib.parse
import base64

# some constants
TIMEOUT = 20
APP_DOMAIN_SUFFIX = '.herokuapp.com'
LABEL_NAME = 'review-env'
PAGE_SIZE = 200

# tokens
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
GHA_USER_TOKEN = os.environ['GHA_USER_TOKEN']
HEROKU_TOKEN = os.environ['HEROKU_API_TOKEN']

# invoke only when a label is added?
REQUIRE_LABEL = (os.environ['USE_LABEL'].lower() == 'true') if 'USE_LABEL' in os.environ.keys() else False

# basic headers for communicating with the Heroku API
HEADERS_HEROKU = {
    'Accept': 'application/vnd.heroku+json; version=3.review-apps',
    'Authorization': 'Bearer %s' % HEROKU_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json',
    'Range': 'id ..; max=%d;' % PAGE_SIZE
    }
HEADERS_HEROKU_REVIEW_PIPELINES = {
    'Accept': 'application/vnd.heroku+json; version=3.pipelines',
    'Authorization': 'Bearer %s' % HEROKU_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json',
    'Range': 'id ..; max=%d;' % PAGE_SIZE
    }

API_URL_HEROKU = 'https://api.heroku.com'

# basic headers for communicating with the GitHub API
HEADERS_GITHUB = {
    'Accept': 'application/vnd.github.v3+json',
    'Authorization': 'token %s' % GHA_USER_TOKEN,
    'User-Agent': 'Heroku GitHub Actions Provider by TheRealReal',
    'Content-Type': 'application/json'
    }
API_URL_GITHUB = 'https://api.github.com'

# Heroku Related Functions #####################################################


def get_review_app_by_branch( pipeline_id, branch_name ):
    reviewapps = heroku_paginated_get_json_array( API_URL_HEROKU+'/pipelines/'+pipeline_id+'/review-apps', headers=HEADERS_HEROKU )
    reviewapp = next((x for x in reviewapps if x['branch'] == branch_name), None)
    print("get_review_app_by_branch:")
    print(json.dumps(reviewapp, sort_keys=True, indent=4))
    try:
        reviewapp = next((x for x in reviewapps if x['branch'] == branch_name), None)
        if reviewapp is not None and 'app' in reviewapp and reviewapp['app'] is not None and 'id' in reviewapp['app']:
            return reviewapp
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        sys.exit("Couldn't find a Review App for this pipeline @ branch - " + pipeline_id + '@' + branch_name)
    return None

def get_review_app_by_id( pipeline_id, id ):
    reviewapps = heroku_paginated_get_json_array( API_URL_HEROKU+'/pipelines/'+pipeline_id+'/review-apps', headers=HEADERS_HEROKU )
    reviewapp = next((x for x in reviewapps if x['id'] == id), None)
    try:
        reviewapp = next((x for x in reviewapps if x['id'] == id), None)
        if reviewapp is not None and 'app' in reviewapp and 'id' in reviewapp['app']:
            return reviewapp
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return None

def get_app_setup_by_id( app_setup_id ):
    r = requests.get(API_URL_HEROKU+'/app-setups/'+app_setup_id, headers=HEADERS_HEROKU)
    app_setup = json.loads(r.text)
    return app_setup

def delete_app_by_name( app_name ):
    if '-pr-' not in app_name:
        sys.exit("Tried to delete app "+app_name+" - refusing for safety's sake.")
    r = requests.delete(API_URL_HEROKU+'/apps/'+app_name, headers=HEADERS_HEROKU)
    response = json.loads(r.text)
    return response

def get_app_by_name_or_id( app_name ):
    r = requests.get(API_URL_HEROKU+'/apps/'+app_name, headers=HEADERS_HEROKU)
    app = json.loads(r.text)
    print("get_app_by_name_or_id:")
    print(json.dumps(app, sort_keys=True, indent=4))
    try:
        if app is not None and 'name' in app:
            return app
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return None

def get_app_by_id( app_id ):
    r = requests.get(API_URL_HEROKU+'/apps', headers=HEADERS_HEROKU)
    apps = json.loads(r.text)
    try:
        app = next((x for x in apps if x['id'] == app_id), None)
        if app is not None and 'id' in app:
            return app
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return None

def rename_app( app_id, app_name ):
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_id, headers=HEADERS_HEROKU, data=json.dumps( {'name': app_name[:30]} ))
    return r.status_code is 200

def get_pipeline_by_name( pipeline_name ):
    r = requests.get(API_URL_HEROKU+'/pipelines', headers=HEADERS_HEROKU)
    pipelines = json.loads(r.text)
    try:
        pipeline = next((x for x in pipelines if x['name'] == pipeline_name), None)
        if pipeline is not None and 'id' in pipeline:
            return pipeline
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return None

def create_team_app( name, team ):
    r = requests.post(API_URL_HEROKU+'/teams/apps', headers=HEADERS_HEROKU, data=json.dumps( {'name': name, 'team': team} ))
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
        },
        'skip_rollback': True
    }
    print(json.dumps(payload, sort_keys=True, indent=4))
    r = requests.post(API_URL_HEROKU+'/app-setups', headers=HEADERS_HEROKU, data=json.dumps(payload))
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
    r = requests.post(API_URL_HEROKU+'/pipeline-couplings', headers=HEADERS_HEROKU, data=json.dumps(payload))
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
    r = requests.post(API_URL_HEROKU+'/apps/'+app_id+'/builds', headers=HEADERS_HEROKU, data=json.dumps(payload))
    response = json.loads(r.text)
    if 'status' in response:
        return response
    else:
        return None

def get_features_for_app( app_id ):
    r = requests.get(API_URL_HEROKU+'/apps/'+app_id+'/features', headers=HEADERS_HEROKU)
    features = json.loads(r.text)
    try:
        if features[0]['id'] and features[0]['doc_url']:
            return features
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return None

def get_config_vars_for_app( app_id ):
    return heroku_paginated_get_json_array( API_URL_HEROKU+'/apps/'+app_id+'/config-vars', headers=HEADERS_HEROKU )

def set_config_vars_for_app( app_id, config_vars ):
    r = requests.patch(API_URL_HEROKU+'/apps/'+app_id+'/config-vars', headers=HEADERS_HEROKU, data=json.dumps(config_vars))
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
    r = requests.put(API_URL_HEROKU+'/apps/'+app_id+'/buildpack-installations', headers=HEADERS_HEROKU, data=json.dumps(buildpack_changes))
    result = json.loads(r.text)
    if r.status_code != 200:
        return None
    return result

def get_review_app_config_vars_for_pipeline( pipeline_id, stage ):
    return heroku_paginated_get_json_array( API_URL_HEROKU+'/pipelines/'+pipeline_id+'/stage/'+stage+'/config-vars', headers=HEADERS_HEROKU_REVIEW_PIPELINES )

def grant_review_app_access_to_user( app_name, email ):
    check_user = requests.get(API_URL_HEROKU+'/teams/apps/'+app_name+'/collaborators/'+email, headers=HEADERS_HEROKU_REVIEW_PIPELINES)
    if check_user.status_code == 200:
        payload = {
            'permissions': ['view', 'manage', 'deploy', 'operate']
        }
        r = requests.patch(API_URL_HEROKU+'/teams/apps/'+app_name+'/collaborators/'+email, headers=HEADERS_HEROKU_REVIEW_PIPELINES, data=json.dumps(payload))
    else:
        payload = {
            'user': email,
            'permissions': ['view', 'manage', 'deploy', 'operate'],
            'silent': True
        }
        r = requests.post(API_URL_HEROKU+'/teams/apps/'+app_name+'/collaborators', headers=HEADERS_HEROKU_REVIEW_PIPELINES, data=json.dumps(payload))

    if r.status_code > 299 or r.status_code < 200:
        if "team admin and cannot be joined on app" not in r.text:
            print("Error granting permissions to %s: %s" % ( email, r.text ))
    return json.loads(r.text)

def get_team_members( team_name ):
    return heroku_paginated_get_json_array( API_URL_HEROKU+'/teams/'+team_name+'/members', headers=HEADERS_HEROKU_REVIEW_PIPELINES )

def heroku_paginated_get_json_array( url, **kwargs ):
    print( "GET %s (Range: '%s')" % (url, kwargs['headers']['Range'] if 'Range' in kwargs['headers'] else '' ) )
    r = requests.get( url, **kwargs )
    results = json.loads(r.text)

    if r.status_code == 206:
        # recurse and return merged results
        kwargs['headers']['Range'] = r.headers['Next-Range']
        return results + heroku_paginated_get_json_array( url, **kwargs )
    return results

# GitHub Related Functions #####################################################

def get_download_url( repo, branch, token ):
    # pulls the 302 location out of the redirect
    download_url = API_URL_GITHUB+'/repos/'+repo+'/tarball/'+urllib.parse.quote(branch)+'?access_token='+token
    try:
        r = requests.get(download_url, allow_redirects=False)
        if r.status_code == 302:
            return r.headers['location']
    except Exception as ex:
        print(ex)
        traceback.print_exc()
    return None

def get_latest_commit_for_branch( repo, branch_name ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/branches/'+urllib.parse.quote(branch_name), headers=HEADERS_GITHUB)
    branch = json.loads(r.text)
    try:
        return branch['commit']['sha']
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        return None

def get_pr_by_name( repo, branch_name, page=1 ):
    r = requests.get(API_URL_GITHUB+'/repos/'+repo+'/pulls?state=all&page='+str(page)+'&per_page=100', headers=HEADERS_GITHUB)
    prs = json.loads(r.text)
    try:
        pr = next((x for x in prs if x['head']['ref'] == branch_name), None)
        if pr:
            return pr
        else:
            return get_pr_by_name( repo, branch_name, page=page+1)
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        return None

def add_pr_comment( repo, pr_id, message):
    payload = {
        'body': message
    }
    r = requests.post(API_URL_GITHUB+'/repos/'+repo+'/issues/'+str(pr_id)+'/comments', headers=HEADERS_GITHUB, data=json.dumps(payload))
    comment = json.loads(r.text)
    return comment

def update_boot_timeout(app_name, timeout):
    data = json.dumps({
        "value": timeout
    })

    url = "%s/apps/%s/limits/boot_timeout" % (API_URL_HEROKU, app_name)
    return requests.put(url, headers=HEADERS_HEROKU, data=data)

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
    'BRANCH',
    'BUILDPACKS',
    'HEROKU_TEAM_NAME',
    'HEROKU_PIPELINE_NAME',
    'REPO',
    'REPO_ORIGIN',
    'APP_REF',
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

# pipeline name that we deploy into
pipeline_name = args['HEROKU_PIPELINE_NAME']
print ("Pipeline Name: "+pipeline_name)

# pull branch name from the GITHUB_REF
try:
    branch_origin = GH_EVENT['pull_request']['head']['ref'] # this has been more reliable
except:
    branch_origin = os.environ['GITHUB_REF'][11:] # this is sometimes wrong
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
    try:
        commit_sha = GH_EVENT['pull_request']['head']['sha']
    except:
        commit_sha = get_latest_commit_for_branch( args['REPO'], branch)

github_org = repo.split('/')[0]
print ("GitHub Org: "+github_org)
print ("Repo: "+repo)
print ("Branch to deploy: "+branch)

# DETERMINE THE APP NAME #######################################################

try:
    # we expect that the event payload has a pull_request object at the first level
    pr = GH_EVENT['pull_request']
except:
    try:
        # look up the PR number for origin repo
        pr = get_pr_by_name( repo_origin, branch_origin )
    except Exception as ex:
        print(ex)
        traceback.print_exc()
        sys.exit("Couldn't find a PR for this branch - %s@%s" % (repo_origin, branch_origin))

pr_num = pr['number']
pr_labels = [x['name'] for x in pr['labels']]
pr_status = pr['state']
print ("Found Pull Request: \"%s\" id: %s (%s)" % (pr['title'].encode('utf-8'), pr_num, pr_status))

# determine the app_name
app_name = get_app_name( app_origin, app_short_name, pr_num, app_prefix )

print ("App Name: "+app_name)

# find the pipeline where we want to spawn the app
try:
    pipeline = get_pipeline_by_name( pipeline_name )
    print ("Found pipeline: " + pipeline['name'] + ' - id: ' + pipeline['id'])
except:
    sys.exit("Couldn't find the pipeline named " + pipeline_name)

# if this is not a labelled PR
print ("Detected Labels: " + ', '.join(pr_labels))
if ( REQUIRE_LABEL and LABEL_NAME not in pr_labels ):
    if get_app_by_name_or_id( app_name ):
        # if app is already spun up, shut it down
        print("Spinning down app "+app_name)
        delete_app_by_name( app_name )
    elif REQUIRE_LABEL:
        # If nothing is spun up so far, but labels are required
        print("To spin up a review environment, label your open pr with "+LABEL_NAME)
    elif pr_status == 'closed':
        print("This PR is currently closed.")
    else:
        print("Quitting. Either label missing or PR is closed.")
    sys.exit(0)

# START CREATING/DEPLOYING #####################################################

# see if there's a review app for this branch already
reviewapp = get_app_by_name_or_id( app_name )

# if it wasn't found, try to use an existing review app if it already exists
if reviewapp is None and app_origin == app_short_name:
    print("Looking up the app by branch instead")
    reviewapp = get_review_app_by_branch( pipeline['id'], branch)

# Heroku wants us to pull the 302 location for the actual code download by
# using this URL - the token gets modified, we don't know how, so we gotta pull
# it before submitting to Heroku.
source_code_tgz = get_download_url( repo, branch, GHA_USER_TOKEN )
if source_code_tgz is None:
    sys.exit("Couldn't get the redirect location for source code download.")

app_id = None
if reviewapp is not None:
    app_id = reviewapp['id']
    print ("Found reviewapp id: " + app_id )
    print(json.dumps(reviewapp, sort_keys=True, indent=4))

    # Originating App - doesn't need to be deployed because Review Apps Beta
    #   automatically deploys on push to the PR.
    # Related App - we do not deploy here b/c we don't want to disrupt the state
    #   of the related app as that may affect testing.
    print("Already exists - no action necessary.")

else:
    print ("Found no existing app.")

    # CHECK AND SET CONFIG VARIABLES FOR APP REFERENCES ############################

    # APP_REF is a list of config vars referencing other apps. The config
    # vars are delimited by '|' and key=value pairs are separated by '%'.
    # This code will expand the value provided into:
    #   {APP_PREFIX}-{MAIN_APP}-{value}-{branch}
    #
    # for example:
    #   APP_REF=MY_API_URL%https://<app_name>/graphql|MY_HOST%https://<app_name>/
    # this will result in 2 config vars:
    #   MY_API_URL=https://myteam-someappname.herokuapp.com/graphql
    #   MY_HOST=https://myteam-someappname.herokuapp.com
    set_vars = {}
    if 'APP_REF' in args:
        for pair in args['APP_REF'].split('|'):
            (app_var, app_url) = pair.split('%')
            m = re.match(r'^(.*)<(.+)>(.*)$', app_url)
            name = m.group(2)
            set_vars[app_var] = m.group(1) + get_app_name( app_origin, name, pr_num, app_prefix ) + APP_DOMAIN_SUFFIX + m.group(3)
            print ("Referencing app: " + app_var + '=' + set_vars[app_var])
    set_vars['HEROKU_APP_NAME'] = app_name

    if app_short_name == app_origin:
        # This is the originating app - deploy it like a reviewapp.
        print ("Creating reviewapp...")
        payload = {
            'branch': branch,
            'pipeline': pipeline['id'],
            'source_blob': {
                'url': source_code_tgz,
                'version': commit_sha,
            },
            'environment': set_vars,
            'skip_rollback': True
        }
        print(json.dumps(payload, sort_keys=True, indent=4))
        try:
            r = requests.post(API_URL_HEROKU+'/review-apps', headers=HEADERS_HEROKU, data=json.dumps(payload))
            response = json.loads(r.text)
            print ("Created ReviewApp:")
            print(json.dumps(response, sort_keys=True, indent=4))
            reviewapp_id = response['id']
            print ("Status is currently " + response['status'])
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            sys.exit("Couldn't create ReviewApp.")

        # look up the app ID, wait for it to show up
        for i in range(0, TIMEOUT):
            print ("Checking for reviewapp spawn...")
            reviewapp = get_review_app_by_id( pipeline['id'], reviewapp_id )
            if reviewapp is not None:
                app_id = reviewapp['app']['id']
                break
            time.sleep(1)
            if i == TIMEOUT:
                sys.exit("timed out waiting for app to instantiate.")
            else:
                print ("waiting...")
        print ("Result:")
        print(json.dumps(reviewapp, sort_keys=True, indent=4))

        # rename the reviewapp (which should just be an app now)
        if rename_app( app_id, app_name ):
            print ("Renamed the app to "+app_name)
        else:
            sys.exit("Failed to rename the app!")

    else:
        # this is a related app, deploy it as a into the development pipeline phase
        print ("Creating development phase app...")

        # get the config vars from review apps beta config vars in the pipeline
        # we have a feature request in to Heroku for a list of default config
        # vars for development phase apps
        print ("Pulling Config Vars from pipeline "+pipeline['name'])
        config_vars = get_review_app_config_vars_for_pipeline( pipeline['id'], 'review' )
        if not config_vars:
            sys.exit("Pulled no config vars from pipeline: "+pipeline['name'])
        else:
            print ("Found %s Config Vars to set." % len(config_vars.keys()))
        for k,v in set_vars.items():
            config_vars[k] = v

        # an app-setup is just like a reviewapp like above. It is almost like
        # and environment setup in that it creates the app, reads app.json and
        # performs the necessary spin-ups and attachments.
        app_setup = create_app_setup( app_name, args['HEROKU_TEAM_NAME'], source_code_tgz, commit_sha, config_vars )

        # look up the app ID, wait for it to show up
        for i in range(0, TIMEOUT):
            print ("Checking for app spawn...")
            app_setup = get_app_setup_by_id( app_setup['id'] )
            if app_setup is not None:
                app_id = app_setup['app']['id']
                break
            time.sleep(1)
            if i == TIMEOUT:
                sys.exit("timed out waiting for app to instantiate.")
            else:
                print ("waiting...")
        print ("Result:")
        print(json.dumps(app_setup, sort_keys=True, indent=4))
        app = app_setup['app']

        # attach to pipeline as development app
        print ("Attaching to pipeline...")
        if not add_to_pipeline( pipeline['id'], app['id'], 'development' ):
            sys.exit("Couldn't attach app %s to pipeline %s" % (app['id'],pipeline['id']))

    # # Update boot timeout
    print("Updating boot timeout...")
    res = update_boot_timeout(app_name, 180)
    if res.ok:
        print(res.json())
    else:
        print("Error updating boot timeout!")
        print(res.text)

    # grant access to all users
    users = get_team_members( args['HEROKU_TEAM_NAME'] )
    print( "Found %s team members to grant access to." % len(users) )
    for email in [ x['email'] for x in users if x['email'] != "devops-noreply+review-envs@therealreal.com" ]:
        grant_review_app_access_to_user( app_name, email )

message = 'Deployed app <a href="https://%s.herokuapp.com">%s</a> - [ <a href="https://dashboard.heroku.com/apps/%s">app: %s</a> | <a href="https://dashboard.heroku.com/apps/%s/logs">logs</a> ]<br>' % (app_name, app_short_name, app_name, app_name, app_name)
print (message)
print ("Done.")
