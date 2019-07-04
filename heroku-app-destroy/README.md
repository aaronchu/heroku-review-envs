# heroku-app-destroy

This GitHub action deletes a Heroku App given a specific naming scheme.

## Usage

Example usage when deploying a Development App:

```
action "Destroy website" {
  needs = "PR Closed"
  users = "TheRealReal/heroku-review-envs/heroku-app-destroy"
  secrets = [
    "HEROKU_API_TOKEN"
  ]
  args = [
    "APP_PREFIX=myorg",
    "APP_NAME=myapp",
    "APP_ORIGIN=myapp",
  ]
}
```

Example usage when deploying a Related App:

```
action "Destroy website" {
  needs = "PR Closed"
  users = "TheRealReal/heroku-review-envs/heroku-app-destroy"
  secrets = [
    "HEROKU_API_TOKEN"
  ]
  args = [
    "APP_PREFIX=myorg",
    "APP_NAME=myrelatedapp",
    "APP_ORIGIN=myapp",
  ]
}
```

## Secrets

* `HEROKU_API_TOKEN` - **Required.** Token for communication with Heroku API.
  * This should be bound to a service or role user on your Heroku Team.
  * This user must have full access to the app being deleted.

## Arguments

In order to supply arguments to this action, use a format similar to environment variable definitions - as shown above in the examples.

* `APP_PREFIX` - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `APP_NAME` - **Required.** The name of this App being deployed.
* `APP_ORIGIN` - **Optional.** The name of the Development App. Define if you're deploying a Related App.

## How Heroku App Names Are Generated

We have to name these apps in a structured way in order to tell them apart.

If this is the Development App, it will be a `review` phase app in the Development App Pipeline named like this:

```
myorg-devapp-pr-number
```

If this is a Related App, it will be a `development` phase app in the Related App Pipeline named like this:

```
myorg-devapp-pr-number-relatedapp
```

## Known Issues
