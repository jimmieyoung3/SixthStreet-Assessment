# Architecture diagram

The main `README.md` at the repository root embeds `architecture.png`,
which is exported from the Excalidraw source in this folder.

## How to produce the diagram

1. Open https://excalidraw.com.
2. Recreate the diagram described below (or open `architecture.excalidraw`
   in Excalidraw if you have saved one here).
3. Export as PNG (File > Export image > PNG) at 2x scale.
4. Save the PNG as `docs/architecture.png` (overwriting the placeholder).
5. Save the Excalidraw source as `docs/architecture.excalidraw` so future
   edits are possible.

## What the diagram should contain

Components, left to right:

1. **User / client** (a person icon or a labeled box). Represents whatever
   uploads files to S3 in real use: a CI job, a partner system, a developer
   running `aws s3 cp`, etc.
2. **Amazon S3 bucket** labeled `ProcessorBucket`. Show the security badges
   on or next to it: "Block Public Access", "SSE-S3", "Versioning",
   "Bucket Policy: Deny non-TLS".
3. **S3 event notification**. An arrow from the bucket to the Lambda
   labeled `s3:ObjectCreated:*`.
4. **AWS Lambda function** labeled `ProcessorFunction` with the runtime
   `python3.14`. Include a note that the IAM role grants `s3:GetObject`
   on the bucket only.
5. **Amazon CloudWatch Logs** group labeled
   `/aws/lambda/ProcessorFunction`, with an arrow from the Lambda.

Arrows and labels:

- User -> S3: `PutObject (HTTPS)`
- S3 -> Lambda: `s3:ObjectCreated:* event`
- Lambda -> S3: `GetObject`
- Lambda -> CloudWatch Logs: `structured JSON logs`

Optional callouts:

- A red dashed arrow from a "Non-TLS request" labeled `DENIED by bucket policy`
  that bounces off the bucket. Visually reinforces the deny-insecure-transport
  policy.
- A note near the Lambda: "Retention: 14 days" pointing at the log group.
