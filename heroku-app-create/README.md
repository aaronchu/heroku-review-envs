# heroku-app-create

This GitHub action creates and/or deploys to a Heroku App based on changes in a
repository.

This is suited to use when you are developing changes to one microservice in a microservices environment.

## Terminology

You're working on a pull request in an repo that corresponds to a Heroku app in a pipeline. Let's call that the `Development App or Service`. It works with other microservices either by calling them or being called by them. Those other microservices are called `Related Apps or Services`.

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
    "MSVC_PREFIX=myorg",
    "HEROKU_TEAM_NAME=myorganization",
    "SERVICE_NAME=myapp",
    "HEROKU_PIPELINE_NAME=myorg-myapp",
    "REPO=myorg/myapp",
    "MSVC_REF=API_URL%https://<myapp>/graphql|API_HOST%https://<myapp>/"]
}
```

Example usage when deploying a Related App:

```
action "create-mymicrosvc" {
  uses = "TheRealReal/heroku-review-envs/heroku-app-create"
  secrets = [
    "HEROKU_API_TOKEN",
    "GITHUB_TOKEN",
    "GHA_USER_TOKEN"]
  args = [
    "MSVC_PREFIX=myorg",
    "HEROKU_TEAM_NAME=myorganization",
    "SERVICE_NAME=mymicrosvc",
    "SERVICE_ORIGIN=myapp",
    "HEROKU_PIPELINE_NAME=myorg-myapp",
    "REPO_ORIGIN=myorg/myapp",
    "REPO=myorg/mymicrosvc",
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

* `MSVC_PREFIX` - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `HEROKU_TEAM_NAME` - **Required.** The team name for your Heroku Team.
* `SERVICE_NAME` - **Required.** The name of this service being deployed.
* `SERVICE_ORIGIN` - **Optional.** The name of the Development App. Define if you're deploying a Related App.
* `HEROKU_PIPELINE_NAME` - **Required.** The name of the Heroku Pipeline that contains apps for this service.
* `REPO` - **Required.** The GitHub Repo that you're deploying this service from. Must be in `user`/`repo_name` or `org`/`repo_name` format.
* `REPO_ORIGIN` - **Optional.** The GitHub Repo for the Development App. Define if you're deploying a Related App.
* `BRANCH` - **Required.** The branch of the microservice that you need deployed.
* `MSVC_REF` - **Optional.** Define what `config_vars`/environment variables to be set in order to reference another microservice. See the below section on how to use this.
* `BUILDPACKS` - **Optional.** This will work for **Related Apps only.** This is a comma-separated list of buildpack URLs. This is necessary for the development phase apps which do not pick up their buildpacks properly from `app.json`. **This may not be needed any longer as we've started to use the `/app-setups` endpoint for spinning things up and it seems to read `app.json` just fine.**

## Referencing Microservices

Here's an example of how to set `MSVC_REF` in order to reference one microservice from another:
```
"MSVC_REF=API_URL%https://<myapp>/graphql|API_HOST%https://<myapp>/"
```
We are defining templates by which to generate the environment variables that point to another microservice.

In the value of the `MSVC_REF` variable, we define multiple `config_vars` to be created. They are delimited by the `|` character. Each of those is a pair - a name and a string template separated by the `%` character.

The string template should contain a placeholder for the Heroku Domain to be assigned to the app. This should be in the form `<myapp>` where `myapp` is the value of `SERVICE_NAME`.

The definition of a microservice reference like this:

```
API_URL%https://<myapp>/graphql
```

Results in a `config_var` named `API_URL` - and if `myapp` is the `SERVICE_NAME` then the value could be something like this:

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

Config vars are pulled from the Review Apps Beta pipelines. Configure these before launching the apps. Both the Development App and Related Apps pull their Config Vars from there before any updates from `MSVC_REF`.

## Known Issues

### Detection of Buildpacks for Elixir Apps

You must specify the buildpacks in the configuration of another app in the pipeline (we did this in a `staging` phase app), in order for the buildpacks to be picked up - even if they're specified in the `app.json` file.

### Auto-deployment of updates to Related Apps

We can't orchestrate this by API yet - the GitHub integration for Heroku Pipelines doesn't have this API properly exposed. For now, if you want automatic deploys to your Related Apps, you can do that with a few clicks on the Related App itself, within it's pipeline.

If you do this, you should understand that the Related Apps may change without warning, as PRs are merged into their master branches.
