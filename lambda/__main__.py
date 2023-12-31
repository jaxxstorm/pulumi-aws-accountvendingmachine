"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import json


repo = awsx.ecr.Repository(
    "gsuite-watcher",
    force_delete=True,
)
image = awsx.ecr.Image(
    "gsuite-watcher",
    dockerfile="app/Dockerfile",
    path="app",
    repository_url=repo.url,
    env={"DOCKER_BUILDKIT": "1", "DOCKER_DEFAULT_PLATFORM": "linux/amd64"},
)

assume_policy_document = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            sid="AssumeRolePolicy",
            effect="Allow",
            principals=[
                aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=["lambda.amazonaws.com"],
                )
            ],
            actions=["sts:AssumeRole"],
        )
    ]
)

lambda_role = aws.iam.Role(
    "gsuite-watcher",
    assume_role_policy=assume_policy_document.json,
)

aws.iam.RolePolicyAttachment(
    "gsuite-watcher-policy-attachment-basic",
    role=lambda_role.name,
    policy_arn=aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE,
    opts=pulumi.ResourceOptions(parent=lambda_role),
)

lambda_func = aws.lambda_.Function(
    "gsuite-watcher",
    role=lambda_role.arn,
    image_uri=image.image_uri,
    package_type="Image",
    timeout=60,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "PULUMI_ACCESS_TOKEN": "changeme",
            "PULUMI_ORG": "lbrlabs",
            "PULUMI_PROJECT_NAME": "aws-accounts",
            "GITHUB_ORG": "lbrlabs",
            "GITHUB_REPO": "aws-accounts",
            "AWS_CONTROLTOWER_ORG": "Testing",
            "AWS_CONTROLTOWER_ORG_ID_ON_DELETE": "ou-p8qa-7ts76j9l",
            "OIDC_ROLE_ARN": "arn:aws:iam::609316800003:role/pulumi-deploy-ff54f5f",
            "PULUMI_HOME": "/tmp/.pulumi",
        }
    ),
)

api_gw = aws.apigatewayv2.Api(
    "gsuite-watcher",
    protocol_type="HTTP",
)

aws.lambda_.Permission(
    "gsuite-watcher",
    statement_id="AllowAPIGatewayInvoke",
    action="lambda:InvokeFunction",
    function=lambda_func,
    principal="apigateway.amazonaws.com",
    source_arn=api_gw.execution_arn.apply(lambda arn: f"{arn}/*/*"),
    opts=pulumi.ResourceOptions(depends_on=[api_gw]),
)

integration = aws.apigatewayv2.Integration(
    "lambda",
    api_id=api_gw.id,
    integration_type="AWS_PROXY",
    integration_method="POST",
    integration_uri=lambda_func.arn,
    payload_format_version="2.0",
    passthrough_behavior="WHEN_NO_MATCH",
)

route = aws.apigatewayv2.Route(
    "gsuite-watcher",
    api_id=api_gw.id,
    route_key="$default",
    target=integration.id.apply(lambda id: f"integrations/{id}"),
)

# creating a stage to expose the deployments
stage = aws.apigatewayv2.Stage(
    "gsuite-watcher",
    api_id=api_gw.id,
    auto_deploy=True,
    route_settings=[
        aws.apigatewayv2.StageRouteSettingArgs(
            route_key=route.route_key,
            throttling_rate_limit=1000,
            throttling_burst_limit=500,
        )
    ],
)

pulumi.export("api_url", stage.invoke_url)
