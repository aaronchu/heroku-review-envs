#!/usr/bin/env python3

import json
import os
import requests

# some constants
TIMEOUT = 20

# tokens
OKTA_API_TOKEN = os.environ['OKTA_API_TOKEN']
OKTA_CLIENT_ID = os.environ['OKTA_CLIENT_ID']

# basic headers for communicating with the GitHub API
HEADERS_OKTA = {
    'Accept': 'application/json',
    'Authorization': 'SSWS %s' % OKTA_API_TOKEN,
    'Content-Type': 'application/json'
    }
API_URL_OKTA = 'https://therealreal.oktapreview.com/oauth2/v1/clients/%s' % OKTA_CLIENT_ID

# Placeholder const for the actual URI to add
REVIEW_ENV_URI = 'https://trr-web-pr-12345.herokuapp.com/admin/okta'

print ("Starint Okta Whitelist URL Destroy")

r = requests.get(API_URL_OKTA, headers=HEADERS_OKTA)
client = json.loads(r.text)

redirect_uris = client['redirect_uris']

if any(REVIEW_ENV_URI in s for s in redirect_uris):
  print ('The URI %s is whitelisted. Removing it from the whitelist now!' % REVIEW_ENV_URI)
  redirect_uris.remove(REVIEW_ENV_URI)
  del client['client_secret_expires_at']
  del client['client_id_issued_at']

  r2 = requests.put(API_URL_OKTA, headers=HEADERS_OKTA, data=json.dumps(client))

  if r2.status_code == 200:
    print ('The URI %s has been removed from the whitelist!' % REVIEW_ENV_URI)
  else:
    print ('There was a problem removing the URI %s from the whitelist. Please investigate.')
else:
  print ('The URI %s is NOT whitelisted' % REVIEW_ENV_URI)
