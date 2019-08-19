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

print ("Starint Okta Whitelist URL Create")

r = requests.get(API_URL_OKTA, headers=HEADERS_OKTA)
client = json.loads(r.text)

redirect_uris = client['redirect_uris']

if not any(REVIEW_ENV_URI in s for s in redirect_uris):
  print ('The URI %s is NOT whitelisted. Adding it to the whitelist now!' % REVIEW_ENV_URI)
  redirect_uris.append(REVIEW_ENV_URI)
  del client['client_secret_expires_at']
  del client['client_id_issued_at']

  r2 = requests.put(API_URL_OKTA, headers=HEADERS_OKTA, data=json.dumps(client))

  if r2.status_code == 200:
    print ('The URI %s has been added to the whitelist!' % REVIEW_ENV_URI)
  else:
    print ('There was a problem adding the URI %s to the whitelist. Please investigate.')
else:
  print ('The URI %s is already whitelisted' % REVIEW_ENV_URI)
