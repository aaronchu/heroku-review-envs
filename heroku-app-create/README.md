# heroku-app-create

This GitHub action creates and/or deploys to a Heroku App based on changes in a repository.

This is suited to use when you are developing changes to one app in a multi-app environment.

## Terminology

You're working on a pull request in an repo that corresponds to a Heroku app in a pipeline. Let's call that the `Development App`. It works with other apps either by calling them or being called by them. Those other apps are called `Related Apps`.

This GitHub Action deploys both of those types of apps into your Heroku account.

## Usage

Example usage when deploying a Development App:

```
action "create-myapp" {
  uses = "TheRealReal/heroku-review-envs/heroku-app-create"
  secrets = [
    "HEROKU_API_TOKEN",
    "GITHUB_TOKEN",
    "GHA_USER_TOKEN"
    ]
  args = [
    "APP_PREFIX=myorg",
    "HEROKU_TEAM_NAME=myorganization",
    "APP_NAME=myapp",
    "HEROKU_PIPELINE_NAME=myorg-myapp",
    "REPO=myorg/myapp",
    "APP_REF=API_URL%https://<myapp>/graphql|API_HOST%https://<myapp>/"]
}
```

Example usage when deploying a Related App:

```
action "create-myrelatedapp" {
  uses = "TheRealReal/heroku-review-envs/heroku-app-create"
  secrets = [
    "HEROKU_API_TOKEN",
    "GITHUB_TOKEN",
    "GHA_USER_TOKEN"]
  args = [
    "APP_PREFIX=myorg",
    "HEROKU_TEAM_NAME=myorganization",
    "APP_NAME=myrelatedapp",
    "APP_ORIGIN=myapp",
    "HEROKU_PIPELINE_NAME=myorg-myrelatedapp",
    "REPO_ORIGIN=myorg/myapp",
    "REPO=myorg/myrelatedapp",
    "BRANCH=master"]
}
```

## Secrets

* `HEROKU_API_TOKEN` - **Required.** Token for communication with Heroku API.
  * This should be bound to a service or role user on your Heroku Team.
  * This user must have view access to an existing app in each pipeline used here.
* `GHA_USER_TOKEN` - **Required.** Token for communication with GitHub API.
  * Since the `GITHUB_TOKEN` is limited in scope to the Development App repo, you need an API token scoped to your repositories in order to deploy from those other repos.

## Arguments

In order to supply arguments to this action, use a format similar to environment variable definitions - as shown above in the examples.

* `APP_PREFIX` - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `APP_REF` - **Optional.** Define what `config_vars`/environment variables to be set in order to reference another app. See the below section on how to use this.
* `APP_NAME` - **Required.** The name of this App being deployed.
* `APP_ORIGIN` - **Optional.** The name of the Development App. Define if you're deploying a Related App.
* `BRANCH` - **Required.** The branch of the app that you need deployed.
* `HEROKU_PIPELINE_NAME` - **Required.** The name of the Heroku Pipeline that contains apps for this App.
* `HEROKU_TEAM_NAME` - **Required.** The team name for your Heroku Team.
* `REPO` - **Required.** The GitHub Repo that you're deploying this App from. Must be in `user`/`repo_name` or `org`/`repo_name` format.
* `REPO_ORIGIN` - **Optional.** The GitHub Repo for the Development App. Define if you're deploying a Related App.
* `REQUIRE_LABEL` - **Optional.** Requires the PR to labelled with `review-env` before invoking any action.

## Referencing Apps

Here's an example of how to set `APP_REF` in order to reference one app from another:
```
"APP_REF=API_URL%https://<myapp>/graphql|API_HOST%https://<myapp>/"
```
We are defining templates by which to generate the environment variables that point to another app.

In the value of the `APP_REF` variable, we define multiple `config_vars` to be created. They are delimited by the `|` character. Each of those is a pair - a name and a string template separated by the `%` character.

The string template should contain a placeholder for the Heroku Domain to be assigned to the app. This should be in the form `<myapp>` where `myapp` is the value of `APP_NAME`.

The definition of an app reference like this:

```
API_URL%https://<myapp>/graphql
```

Results in a `config_var` named `API_URL` - and if `myapp` is the `APP_NAME` then the value could be something like this:

```
https://myorg-myapp-branch.herokuapp.com/graphql
```

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

## Config Vars

Config vars are pulled from the Review Apps Beta pipelines. Configure these before launching the apps. Both the Development App and Related Apps pull their Config Vars from there before any updates from `APP_REF`.

## Known Issues

### Auto-deployment of updates to Related Apps

We can't orchestrate this by API yet - the GitHub integration for Heroku Pipelines doesn't have this API properly exposed. For now, if you want automatic deploys to your Related Apps, you can do that with a few clicks on the Related App itself, within it's pipeline.

If you do this, you should understand that the Related Apps may change without warning, as PRs are merged into their master branches.
