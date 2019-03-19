# heroku-kafka-create

This GitHub action creates and/or deploys to a Heroku Kafka App with a Kafka addon, and attach that addon to multiple Apps in the Review Environment.

This is suited to use when you are developing changes in a multi-app environment. In your GitHub Actions worksflow, you'll want to spin up your Apps first, then have this run and attach to those Apps.

## Terminology

You're working on a pull request in an repo that corresponds to a Heroku app in a pipeline. Let's call that the `Development App`. It works with other apps either by calling them or being called by them. Those other apps are called `Related Apps`.

This GitHub Action deploys both of those types of apps into your Heroku account.

## Usage

Example usage:

```
action "create-kafka" {
  needs = [
    "create-trr-website",
    "create-trr-web",
    "create-trr-api",
    "create-trr-api-gateway"
    ]
  uses = "TheRealReal/heroku-review-envs/heroku-kafka-create"
  secrets = [
    "HEROKU_API_TOKEN",
    "GITHUB_TOKEN"
    ]
  args = [
    "APP_PREFIX=myorg",
    "HEROKU_TEAM_NAME=myorganization",
    "APP_NAME=kafka",
    "APP_ORIGIN=myapp",
    "RELATED_APPS=relatedapp,relatedapp2",
    "HEROKU_PIPELINE_NAME=myorg-kafka",
    ]
}
```

## Secrets

* `HEROKU_API_TOKEN` - **Required.** Token for communication with Heroku API.
  * This should be bound to a service or role user on your Heroku Team.
  * This user must have view access to an existing app in each pipeline used here.

## Arguments

In order to supply arguments to this action, use a format similar to environment variable definitions - as shown above in the examples.

* `APP_PREFIX` - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `HEROKU_TEAM_NAME` - **Required.** The team name for your Heroku Team.
* `APP_NAME` - **Required.** The name of this App being deployed.
* `APP_ORIGIN` - **Optional.** The name of the Development App. Define if you're deploying a Related App.
* `HEROKU_PIPELINE_NAME` - **Required.** The name of the Heroku Pipeline that contains apps for this App.
* `RELATED_APPS` - **Required.** Other Apps in the Review Environment to attach this Kafka to.

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
