# okta-whitelist-url-create

This GitHub action will whitelist a review environment with Okta so that it can be logged into using Okta and RBAC features can be tested.

## Terminology

"Whitelisting" means that the URI specified can be used to login with Okta. Each URI that we want people to be able to login with has to be cleared before Okta will allow it. 

## Usage

Example usage when deploying a Development App:

```
action "create-okta-whitelist" {
  uses = "TheRealReal/heroku-review-envs/okta-whitelist-url-create"
  needs = "Deploy Review Environment if Branch Modified"
  secrets = [
    "OKTA_API_TOKEN",
    "GHA_USER_TOKEN"]
  args = [
    "APP_PREFIX=myorg",
    "APP_ORIGIN=myapp",
    "APP_TARGET=myapp",
    "URL_TARGET=https://%s.herokuapp.com/my_okta_consume_route",
    "OKTA_API_URL=https://myorg.oktapreview.com/oauth2/v1/clients/my-client-id"
  ]
}
```

Example usage when deploying a Related App:

```
action "create-okta-whitelist" {
  uses = "TheRealReal/heroku-review-envs/okta-whitelist-url-create"
  needs = "Deploy Review Environment if Branch Modified"
  secrets = [
    "OKTA_API_TOKEN",
    "GHA_USER_TOKEN"]
  args = [
    "APP_PREFIX=myorg",
    "APP_ORIGIN=myrelatedapp",
    "APP_TARGET=myapp",
    "URL_TARGET=https://%s.herokuapp.com/my_okta_consume_route",
    "OKTA_API_URL=https://myorg.oktapreview.com/oauth2/v1/clients/my-client-id"
  ]
}
```

## Secrets

* `OKTA_API_TOKEN` - **Required.** Token for communication with Okta API.
* `GHA_USER_TOKEN` - **Required.** Token for communication with GitHub API.

## Arguments

In order to supply arguments to this action, use a format similar to environment variable definitions - as shown above in the examples.

* `APP_PREFIX`     - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `APP_ORIGIN`     - **Required.** The name of the Development App.
* `APP_TARGET`     - **Required.** The name of the App that will host your Okta consume endpoint.
* `URL_TARGET`     - **Required.** The URL you want whitelisted with Okta. Use a single %s to indicate where you would like the app name to appear.
* `OKTA_API_URL`   - **Required.** The URL for your Okta API, including Client ID
