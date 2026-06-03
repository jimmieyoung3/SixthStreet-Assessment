#!/usr/bin/env python3
"""CDK application entry point.

Synthesizes the CdkS3LambdaProcessorStack into a CloudFormation template.
The stack provisions an S3 bucket, a bucket policy that denies non-TLS
requests, and a Lambda function that processes single-line files uploaded
to the bucket.
"""
import aws_cdk as cdk

from cdk_s3_lambda_processor.stack import CdkS3LambdaProcessorStack

app = cdk.App()

CdkS3LambdaProcessorStack(
    app,
    "CdkS3LambdaProcessorStack",
    description="S3 bucket + bucket policy + Lambda for processing single-line files",
)

# Stack-level tags applied to every taggable resource
cdk.Tags.of(app).add("Project", "cdk-s3-lambda-processor")
cdk.Tags.of(app).add("ManagedBy", "AWS-CDK")

app.synth()
