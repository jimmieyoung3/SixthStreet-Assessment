"""CDK assertion tests for CdkS3LambdaProcessorStack.

These tests synthesize the stack to a CloudFormation template and assert
the resulting structure. They verify:
- All expected resource types are present.
- The Lambda runtime is python3.14.
- The bucket has encryption and public-access blocking.
- The bucket policy contains the explicit deny-insecure-transport statement.
"""
import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from cdk_s3_lambda_processor.stack import CdkS3LambdaProcessorStack


@pytest.fixture(scope="module")
def template() -> Template:
    """Synthesize the stack once per test module."""
    app = cdk.App()
    stack = CdkS3LambdaProcessorStack(app, "TestStack")
    return Template.from_stack(stack)


def test_resources_present(template: Template) -> None:
    """The stack contains the expected resource types."""
    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::S3::BucketPolicy", 1)
    # One processor function plus CDK's framework Lambdas for log retention
    # and auto-delete-objects. We assert at least one Lambda, then assert the
    # specific runtime below.
    assert len(template.find_resources("AWS::Lambda::Function")) >= 1


def test_processor_lambda_runtime_is_python_3_14(template: Template) -> None:
    """The application Lambda uses the latest supported Python runtime."""
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Runtime": "python3.14"},
    )


def test_bucket_has_encryption_and_blocks_public_access(template: Template) -> None:
    """The bucket enforces SSE-S3 encryption and blocks all public access."""
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                ]
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
            "VersioningConfiguration": {"Status": "Enabled"},
        },
    )


def test_bucket_policy_denies_insecure_transport(template: Template) -> None:
    """The bucket policy contains an explicit deny for non-TLS requests."""
    template.has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": {
                "Statement": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Effect": "Deny",
                                "Action": "s3:*",
                                "Condition": {
                                    "Bool": {"aws:SecureTransport": "false"}
                                },
                            }
                        )
                    ]
                )
            }
        },
    )


def test_lambda_has_s3_notification(template: Template) -> None:
    """The bucket is wired to notify the Lambda on object creation."""
    # CDK uses a custom resource (Custom::S3BucketNotifications) to configure
    # bucket notifications. Its presence indicates the notification wiring is
    # in place.
    template.resource_count_is("Custom::S3BucketNotifications", 1)


def test_stack_outputs_present(template: Template) -> None:
    """The stack exposes the bucket name, function name, and log group."""
    template.has_output("BucketName", {})
    template.has_output("FunctionName", {})
    template.has_output("LogGroupName", {})
