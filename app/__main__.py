import flask
import os
from pulumi import automation as auto
import requests

# references the templates and static files in the assets dir
template_dir = os.path.abspath("./assets/templates")
css_dir = os.path.abspath("./assets/static")
app = flask.Flask(
    __name__,
    template_folder=template_dir,
    static_folder=css_dir,
    instance_relative_config=True,
)
app.config.from_object("config")
app.config.from_pyfile("config.py")
app.secret_key = "super-secret-key"

# we want all our deployments to go into the same stack
project_name = app.config["PULUMI_PROJECT_NAME"]
access_token = app.config["PULUMI_ACCESS_TOKEN"]
pulumi_org = app.config["PULUMI_ORG"]
git_org = app.config["GITHUB_ORG"]
git_repo = app.config["GITHUB_REPO"]
git_branch = "main"
aws_controltower_org = app.config["ACCOUNT_OU"]
aws_controltower_org_id_on_delete = app.config["ACCOUNT_OU_ON_DELETE"]
oidc_role_arn = app.config["OIDC_ROLE_ARN"]
# set the access token
headers = {"Authorization": f"token {access_token}"}


# We're not building the program locally, so we can just return a no-op program.
def create_pulumi_program():
    return


@app.route("/ping", methods=["GET"])
def ping():
    return flask.jsonify("pong!", 200)


@app.route("/", methods=["GET"])
def list_accounts():
    deployments = []
    try:
        ws = auto.LocalWorkspace(
            project_settings=auto.ProjectSettings(name=project_name, runtime="python")
        )
        all_stacks = ws.list_stacks()
        for stack in all_stacks:
            stack = auto.select_stack(
                stack_name=stack.name,
                project_name=project_name,
                # no-op program, just to get outputs
                program=lambda: None,
            )
            deployments.append({"name": stack.name})
    except Exception as exn:
        flask.flash(str(exn), category="danger")
    return flask.render_template("index.html", deployments=deployments)


@app.route("/new", methods=["GET", "POST"])
def create_account():
    """creates new deployment"""
    if flask.request.method == "POST":
        name = flask.request.form.get("accountname")
        email = flask.request.form.get("email")
        first_name = flask.request.form.get("firstname")
        last_name = flask.request.form.get("lastname")

        def pulumi_program():
            return create_pulumi_program()

        try:
            # create a new stack, generating our pulumi program on the fly from the POST body
            stack = auto.create_stack(
                stack_name=f"{pulumi_org}/{project_name}/{name}",
                project_name=project_name,
                program=pulumi_program,
            )
            stack.set_config("name", auto.ConfigValue(value=name))
            stack.set_config("email", auto.ConfigValue(value=email))

            stack.refresh()

            # create the deployment settings
            try:
                r = requests.post(
                    f"https://api.pulumi.com/api/stacks/{pulumi_org}/{project_name}/{name}/deployments/settings",
                    json={
                        "sourceContext": {
                            "git": {"branch": f"refs/heads/{git_branch}"}
                        },
                        "gitHub": {
                            "repository": f"{git_org}/{git_repo}",
                            "deployCommits": True,
                            "previewPullRequests": True,
                        },
                        "operationContext": {
                            "preRunCommands": [
                                f"pulumi config set name {name} -s {pulumi_org}/{name}",
                                f"pulumi config set email {email} -s {pulumi_org}/{name}",
                                f"pulumi config set organizationalUnit {aws_controltower_org} -s {pulumi_org}/{name}",
                                f"pulumi config set organizationalUnitIdOnDelete {aws_controltower_org_id_on_delete} -s {pulumi_org}/{name}",
                                f"pulumi config set ssoEmail {email} -s {pulumi_org}/{name}",
                                f"pulumi config set ssoFirstName {first_name} -s {pulumi_org}/{name}",
                                f"pulumi config set ssoLastName {last_name} -s {pulumi_org}/{name}",
                            ],
                            "oidc": {
                                "aws": {
                                    "roleArn": oidc_role_arn,
                                    "sessionName": "deployment",
                                }
                            },
                            "environmentVariables": {"AWS_REGION": "us-west-2"},
                        },
                    },
                    headers=headers,
                )

                response = r.json()
                r.raise_for_status()
            except requests.exceptions.HTTPError as err:
                flask.flash(
                    f"Error creating deployment settings: {err} - response: {response}",
                    category="danger",
                )

            try:
                # create the deployment
                r = requests.post(
                    f"https://api.pulumi.com/api/stacks/{pulumi_org}/{project_name}/{name}/deployments",
                    json={
                        "operation": "update",
                    },
                    headers=headers,
                )
                response = r.json()
                r.raise_for_status()
                
            except requests.exceptions.HTTPError as err:
                flask.flash(
                    f"Error creating deployment: {err} - response: {response}",
                    category="danger",
                )

            flask.flash(
                f"Successfully dispatched account deployment '{name}': response {response}",
                category="success",
            )
        except auto.StackAlreadyExistsError:
            flask.flash(
                f"Error: Deployment with name '{name}' already exists, pick a unique name",
                category="danger",
            )

        return flask.redirect(flask.url_for("list_accounts"))

    return flask.render_template("create.html")


@app.route("/<string:id>/delete", methods=["POST"])
def delete_account(id: str):
    account_name = id
    print(account_name)
    try:
        stack = auto.select_stack(
            stack_name=account_name,
            project_name=project_name,
            # noop program for destroy
            program=lambda: None,
        )

        try:
            r = requests.post(
                f"https://api.pulumi.com/api/stacks/{pulumi_org}/{project_name}/{account_name}/deployments",
                json={
                    "operation": "delete",
                },
                headers=headers,
            )
        except requests.exceptions.HTTPError as err:
            flask.flash(
                f"Error dispatching account deletion deployment: {err}",
                category="danger",
            )

        flask.flash(
            f"Successfully dispatched '{account_name}' deletion!", category="success"
        )
    except Exception as exn:
        flask.flash(str(exn), category="danger")

    return flask.redirect(flask.url_for("list_accounts"))


if __name__ == "__main__":
    app.run(host="localhost", port=5050, debug=True)
