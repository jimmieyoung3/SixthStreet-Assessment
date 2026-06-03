# Architecture diagrams

The main `README.md` at the repository root embeds two SVG diagrams
exported from Excalidraw source files in this folder.

## Files

| File | Description |
|---|---|
| `cdk-s3-logs.svg` | Runtime architecture (S3, Lambda, IAM, CloudWatch) |
| `cdk-s3-logs.excalidraw` | Excalidraw source for the runtime diagram |
| `github.svg` | CI/CD pipeline (GitHub Actions to CloudFormation) |
| `githubaction.excalidraw` | Excalidraw source for the CI/CD diagram |

## How to update a diagram

1. Open https://excalidraw.com.
2. Open the `.excalidraw` source file for the diagram you want to edit.
3. Make your changes.
4. Export as SVG (File > Export image > SVG).
5. Save the SVG and the updated `.excalidraw` source back to this folder.
