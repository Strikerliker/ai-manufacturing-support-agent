# Architecture and Security Design

## Objective

Provide a grounded manufacturing IT support assistant that can answer ERP/MRP, workstation, inventory, and barcode-support questions only when approved procedures support the answer.

## Request path

1. A support user calls Amazon API Gateway.
2. API Gateway invokes the support-agent Lambda.
3. Lambda validates the question before retrieval or model invocation.
4. Lambda lists and reads only approved Markdown procedures from the private S3 knowledge prefix.
5. The retrieval layer chunks the procedures, performs lexical relevance scoring, and selects the highest-scoring passages.
6. If no passage meets the minimum score, the agent returns a safe escalation response without calling a model.
7. If relevant passages exist, Lambda sends only the question and retrieved approved context to the configured Amazon Bedrock model.
8. The API returns the grounded answer, source citations, grounding status, and escalation flag.

## Trust boundaries

### User to API Gateway

API Gateway is the public service boundary. Routes are explicit, browser origins are configurable, and stage throttling limits request volume.

### Lambda to S3

The Lambda execution role can list only the project knowledge prefix and read only objects below `knowledge/`. The S3 bucket blocks public access, enables versioning, and encrypts objects at rest.

### Lambda to Amazon Bedrock

The Lambda role can invoke only the configured foundation-model ARN. The system prompt prohibits unsupported ERP transactions, permissions, safety steps, or production changes.

## Grounding controls

- Retrieval happens before model invocation.
- A minimum retrieval score must be met.
- Retrieved passages are the only support context supplied to the model.
- Source filenames and section titles are returned as citations.
- Low-confidence questions receive a non-generative fallback.
- Security, safety, privileged-access, data-loss, and production-down terms set an escalation flag.
- Direct database changes, privilege expansion, and disabling security controls are explicitly discouraged by the sample procedures.

## Production expansion path

A production implementation could add Amazon Cognito or enterprise SSO, Bedrock Guardrails, OpenSearch Serverless or Bedrock Knowledge Bases, document approval metadata, source versioning and expiration, DynamoDB case history, ticketing integrations, audit events, SIEM integration, feedback/evaluation datasets, automated red-team tests, and organization-specific data-classification controls.
