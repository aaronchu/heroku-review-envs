# okta-whitelist-url-create

This GitHub action will remove a review environment from the Okta whitelist so that it can no longer be logged into using Okta.

## Terminology

"Whitelisting" means that the URI specified can be used to login with Okta. Each URI that we want people to be able to login with has to be cleared before Okta will allow it. 

## Usage

Example usage when deploying a Development App:

```
action "Destroy okta-whitelist" {
  needs = "Delete Review Env if PR Closed"
  uses = "TheRealReal/heroku-review-envs/okta-whitelist-url-destroy"
  secrets = [
    "OKTA_API_TOKEN",
    "GHA_USER_TOKEN"
  ]
  args = [
    "APP_PREFIX=myorg",
    "APP_ORIGIN=myapp",
    "OKTA_CLIENT_ID=my-okta-client-id",
    "OKTA_BASE_URL=myorg.oktapreview.com"
  ]
}
```

Example usage when deploying a Related App:

```
action "Destroy okta-whitelist" {
  needs = "Delete Review Env if PR Closed"
  uses = "TheRealReal/heroku-review-envs/okta-whitelist-url-destroy"
  secrets = [
    "OKTA_API_TOKEN",
    "GHA_USER_TOKEN"
  ]
  args = [
    "APP_PREFIX=myorg",
    "APP_ORIGIN=myrelatedapp",
    "OKTA_CLIENT_ID=my-okta-client-id",
    "OKTA_BASE_URL=myorg.oktapreview.com"
  ]
}
```

## Secrets

* `OKTA_API_TOKEN` - **Required.** Token for communication with Okta API.
* `GHA_USER_TOKEN` - **Required.** Token for communication with GitHub API.

## Arguments

In order to supply arguments to this action, use a format similar to environment variable definitions - as shown above in the examples.

* `APP_PREFIX`     - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `APP_ORIGIN`     - **Optional.** The name of the Development App. Define if you're deploying a Related App.
* `OKTA_CLIENT_ID` - **Required.** The ID that specifies the Admin Application in our Okta sandbox.
* `OKTA_BASE_URL`  - **Required.** The Base URL for the Okta Authorization Server
