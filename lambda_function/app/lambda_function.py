import pulumi
import requests
import os


def handler(event, context):
    email = event["primaryEmail"]
    name = email.split("@")[0]
    last_name = name[1:]
    first_name = name[0]
    
    pulumi_org = os.getenv("PULUMI_ORG")
    pulumi_project_name = os.getenv("PULUMI_PROJECT_NAME")
    git_org = os.getenv("GITHUB_ORG")
    git_repo = os.getenv("GITHUB_REPO")
    git_branch = os.getenv("GITHUB_BRANCH") or "main"
    aws_controltower_org = os.getenv("AWS_CONTROLTOWER_ORG")
    aws_controltower_org_id_on_delete = os.getenv("AWS_CONTROLTOWER_ORG_ID_ON_DELETE")
    oidc_role_arn = os.getenv("OIDC_ROLE_ARN")

    def pulumi_program():
        return

    stack = pulumi.automation.create_stack(
        f"{pulumi_project_name}/{pulumi_project_name}/{name}",
        project_name=pulumi_project_name,
        program=pulumi_program,
    )
    stack.set_config("name", pulumi.automation.ConfigValue(value=name))
    stack.set_config("email", pulumi.automation.ConfigValue(value=email))

    stack.refresh()
    access_token = os.getenv("PULUMI_ACCESS_TOKEN")

    headers = {"Authorization": f"token {access_token}"}

    r = requests.post(
        f"https://api.pulumi.com/api/stacks/{pulumi_org}/{pulumi_project_name}/{name}/deployments/settings",
        json={
            "sourceContext": {"git": {"branch": f"refs/heads/{git_branch}"}},
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

    print(f"Status Code: {r.status_code}, Response: {r.json()}")

    r = requests.post(
        f"https://api.pulumi.com/api/stacks/{pulumi_org}/{pulumi_project_name}/{name}/deployments",
        json={
            "operation": "update",
        },
        headers=headers,
    )
    print(f"Status Code: {r.status_code}, Response: {r.json()}")
