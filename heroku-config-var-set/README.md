# heroku-config-var-set

This GitHub action will set any number of config variables on a heroku review environment

## Usage

Example usage when setting config vars on a Development App (.yml syntax):

```
my_app:
    name: my_name
    runs-on: ubuntu-latest
    steps:
    - name: Sets Heroku config vars
      uses: TheRealReal/heroku-review-envs/heroku-config-var-set@master
      env:
        HEROKU_API_TOKEN: ${{ secrets.HEROKU_API_TOKEN }}
      with:
        args: APP_ORIGIN=my_origin APP_TARGET=my_target APP_PREFIX=trr CONFIG_VARS=API_URL%https://www.myapi.com/graphql/|API_HOST%https://www.myapi.com/
```

## Secrets

* `HEROKU_API_TOKEN` - **Required.** Token for communication with Heroku.

## Arguments

In order to supply arguments to this action, use a format similar to environment variable definitions - as shown above in the examples.

* `APP_ORIGIN` - **Required.** The name of the Development App that your PR was created on.
* `APP_TARGET` - **Required.** The name of the Related App that you want to set config vars for
* `APP_PREFIX` - **Required.** A prefix for all of your Heroku app names. You probably want this specific to your organization or team. It's best that this is kept short as Heroku has a 30-character limit on app names.
* `CONFIG_VARS` - **Required.** Define what `config_vars`/environment variables to be set in order to reference another app. See the below section on how to use this.

## CONFIG_VARS

In the value of the `CONFIG_VARS` variable, we define multiple configuration variables to be set. They are delimited by the `|` character. Each of those is a pair - a name and a string template separated by the `%` character.

The definition of two config var like this:

```
API_URL%https://www.myapi.com/graphql/|API_HOST%https://www.myapi.com/
```

Results in two config variables named `API_URL` and `API_HOST` that will have the following values:

```
API_URL=https://www.myapi.com/graphql/
API_HOST=https://www.myapi.com/
```
