# Deployment Guide

## Prerequisites

- Terraform 1.6 or newer
- AWS credentials supplied through an approved short-lived authentication method
- Access to the configured Amazon Bedrock foundation model in the target Region
- Permission to create S3, Lambda, IAM, API Gateway, and CloudWatch resources

## Validate locally

From the repository root:

```bash
python -m unittest discover -s tests -v
cd terraform
terraform init -backend=false
terraform validate
```

## Plan and deploy

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Terraform packages the Python source, uploads the example approved support procedures to the private S3 knowledge bucket, and creates the API/Lambda stack.

## Verify

Get the API URL:

```bash
terraform output -raw api_url
```

Health check:

```bash
curl "$(terraform output -raw api_url)/health"
```

Support request:

```bash
curl -X POST "$(terraform output -raw api_url)/support" \
  -H "content-type: application/json" \
  -d '{"question":"What should I check when an ERP work order will not release?"}'
```

Confirm that the response includes `grounded`, `citations`, and `escalation_required` fields.

## Production considerations

Replace the sample procedures with organization-approved documents before production use. Add enterprise authentication, Bedrock Guardrails, formal source approval/version metadata, centralized audit logging, alarms, data-classification controls, and an evaluation dataset before treating generated guidance as an operational production service.

## Destroy lab resources

```bash
terraform destroy
```

Review S3 object-retention requirements before destroying a production knowledge repository.
