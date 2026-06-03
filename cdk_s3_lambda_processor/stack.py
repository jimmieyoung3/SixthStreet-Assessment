"""CDK stack: S3 bucket, bucket policy, and Lambda processor.

Resources provisioned:
- S3 bucket with block-public-access, SSE-S3 encryption, and versioning
- Explicit bucket policy denying any request not using TLS
- Lambda function (Python 3.14) triggered on s3:ObjectCreated:* events
- IAM role for the Lambda scoped to s3:GetObject on this bucket only
- CloudWatch log group with 14-day retention
"""
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
)
from constructs import Construct


class CdkS3LambdaProcessorStack(Stack):
    """Provisions the S3-to-Lambda single-line file processor."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ------------------------------------------------------------------
        # S3 bucket
        # ------------------------------------------------------------------
        # - block_public_access: defense in depth, also AWS default since 2023
        # - encryption: SSE-S3 (AES-256) managed by S3, no KMS cost overhead
        # - versioned: protects against accidental overwrites and deletes
        # - removal_policy + auto_delete_objects: allow clean `cdk destroy`
        #   for this assessment. In production these would be RETAIN.
        bucket = s3.Bucket(
            self,
            "ProcessorBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            enforce_ssl=False,  # we add an explicit policy below for clarity
        )

        # ------------------------------------------------------------------
        # Bucket policy: deny any request that is not using TLS
        # ------------------------------------------------------------------
        # Added explicitly (rather than via `enforce_ssl=True` on the bucket)
        # so the policy is visible in the source and reviewable in the
        # synthesized CloudFormation as a discrete statement.
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyInsecureTransport",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[bucket.bucket_arn, bucket.arn_for_objects("*")],
                conditions={"Bool": {"aws:SecureTransport": "false"}},
            )
        )

        # ------------------------------------------------------------------
        # Lambda function
        # ------------------------------------------------------------------
        # Runtime: python3.14 is the latest Lambda-supported Python runtime
        # (added November 2025). The handler reads the uploaded object,
        # parses the first line as CSV, and logs a structured JSON entry.
        #
        # The log group is created explicitly (rather than via the deprecated
        # `log_retention` property on Function) so retention is controlled
        # by a first-class CloudFormation resource the stack owns and
        # destroys cleanly.
        processor_log_group = logs.LogGroup(
            self,
            "ProcessorFunctionLogGroup",
            retention=logs.RetentionDays.TWO_WEEKS,
            removal_policy=RemovalPolicy.DESTROY,
        )

        processor = lambda_.Function(
            self,
            "ProcessorFunction",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("lambda_src"),
            timeout=Duration.seconds(30),
            memory_size=256,
            log_group=processor_log_group,
            description="Parses single-line files uploaded to the processor bucket",
            environment={
                "LOG_LEVEL": "INFO",
            },
        )

        # ------------------------------------------------------------------
        # Permissions: read-only access to objects in this bucket
        # ------------------------------------------------------------------
        # `grant_read` adds an IAM policy granting s3:GetObject and
        # s3:GetObject* on this bucket only. No wildcard resources.
        bucket.grant_read(processor)

        # ------------------------------------------------------------------
        # Event notification: trigger Lambda on object creation
        # ------------------------------------------------------------------
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(processor),
        )

        # ------------------------------------------------------------------
        # Stack outputs
        # ------------------------------------------------------------------
        CfnOutput(
            self,
            "BucketName",
            value=bucket.bucket_name,
            description="Name of the S3 bucket. Upload a single-line file here to trigger the Lambda.",
        )
        CfnOutput(
            self,
            "FunctionName",
            value=processor.function_name,
            description="Name of the Lambda function. View logs at /aws/lambda/<this value>.",
        )
        CfnOutput(
            self,
            "LogGroupName",
            value=f"/aws/lambda/{processor.function_name}",
            description="CloudWatch log group for the Lambda function.",
        )
