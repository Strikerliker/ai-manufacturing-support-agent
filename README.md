# AI Manufacturing Support Agent

A grounded AI support assistant for manufacturing IT and ERP/MRP troubleshooting. The project retrieves approved support procedures, ranks relevant passages, generates a source-grounded response with Amazon Bedrock, returns citations, and refuses to invent procedures when the knowledge base does not support an answer.

## What this project demonstrates

- Retrieval-augmented generation over approved manufacturing support procedures
- Source citations returned with every grounded answer
- Amazon Bedrock model invocation with retrieved context only
- Safe fallback when no approved source is relevant
- Escalation guidance for security, safety, production-impact, and access-control issues
- Serverless API with API Gateway and AWS Lambda
- Encrypted, versioned Amazon S3 knowledge storage
- Least-privilege IAM for S3 and Bedrock
- CloudWatch logging and API throttling
- Terraform infrastructure as code
- Unit tests, Bandit security scanning, and Terraform validation in GitHub Actions
- Portfolio dashboard with live CI status

## Architecture

```text
Support User
    |
    v
API Gateway
    |
    v
AWS Lambda
    |
    +--> S3 Approved Knowledge Base
    |       SOPs / ERP / IT procedures
    |
    +--> lexical retrieval + ranking
    |
    +--> Amazon Bedrock
    |       grounded prompt only
    |
    v
Answer + citations + escalation flag

CloudWatch receives API and Lambda operational logs.
```

## Repository contents

- `src/rag.py` — chunking, retrieval, citation formatting, and grounding helpers
- `src/app.py` — Lambda/API handler and Bedrock integration
- `knowledge/` — sample approved manufacturing support procedures
- `tests/` — unit tests for retrieval, validation, and fallback behavior
- `terraform/` — S3, Lambda, API Gateway, IAM, CloudWatch, and Bedrock permissions
- `docs/architecture.md` — trust boundaries, controls, and design decisions
- `docs/deployment.md` — deployment and verification procedure
- `dashboard.html` — project dashboard with live GitHub Actions status
- `.github/workflows/validate.yml` — CI validation

## API routes

### `GET /health`

Returns service health without invoking the model.

### `POST /support`

Example body:

```json
{
  "question": "What should I check when an ERP user cannot release a work order?"
}
```

Example response shape:

```json
{
  "answer": "...",
  "citations": [
    {"source": "erp-work-order-support.md", "section": "Work order release troubleshooting"}
  ],
  "grounded": true,
  "escalation_required": false
}
```

If retrieval does not find a sufficiently relevant approved procedure, the API returns a safe fallback instead of asking the model to improvise.

## Local test

```bash
python -m unittest discover -s tests -v
```

The core retrieval tests do not require AWS credentials.

## Deploy

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Terraform uploads the example knowledge documents to a private S3 bucket and deploys the API/Lambda stack. `terraform apply` creates AWS resources and may incur charges.

## Security model

- No AWS credentials or secrets are stored in the repository.
- The Lambda role can read only the project knowledge prefix.
- Bedrock permission is restricted to the configured foundation model.
- S3 Block Public Access, versioning, and encryption are enabled.
- The prompt explicitly limits answers to retrieved context.
- Empty or oversized questions are rejected before model invocation.
- Low-confidence retrieval returns an escalation/fallback response.
- API access logging does not include request bodies.

## Portfolio note

This repository is a reproducible reference implementation. CI validates the code and Terraform without claiming that the stack is currently running in a production AWS account. A live AWS deployment should use organization-approved SOPs, access controls, data classification rules, monitoring, and model-governance policies.