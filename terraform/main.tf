data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"
  model_arn   = "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}::foundation-model/${var.bedrock_model_id}"

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Portfolio   = "John-D"
    },
    var.tags
  )

  knowledge_files = {
    "erp-work-order-support.md"       = "${path.module}/../knowledge/erp-work-order-support.md"
    "workstation-support.md"          = "${path.module}/../knowledge/workstation-support.md"
    "inventory-and-barcode-support.md" = "${path.module}/../knowledge/inventory-and-barcode-support.md"
  }
}

resource "aws_s3_bucket" "knowledge" {
  bucket = "${local.name_prefix}-${data.aws_caller_identity.current.account_id}"
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "knowledge" {
  bucket = aws_s3_bucket.knowledge.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "knowledge" {
  bucket = aws_s3_bucket.knowledge.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge" {
  bucket = aws_s3_bucket.knowledge.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "knowledge" {
  for_each = local.knowledge_files

  bucket       = aws_s3_bucket.knowledge.id
  key          = "knowledge/${each.key}"
  source       = each.value
  etag         = filemd5(each.value)
  content_type = "text/markdown"
}

data "archive_file" "agent" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/manufacturing-support-agent.zip"
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "agent" {
  name               = "${local.name_prefix}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_logs" {
  role       = aws_iam_role.agent.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "agent" {
  statement {
    sid       = "ListApprovedKnowledge"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.knowledge.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["knowledge/*"]
    }
  }

  statement {
    sid       = "ReadApprovedKnowledge"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.knowledge.arn}/knowledge/*"]
  }

  statement {
    sid       = "InvokeConfiguredBedrockModel"
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = [local.model_arn]
  }
}

resource "aws_iam_role_policy" "agent" {
  name   = "${local.name_prefix}-lambda-policy"
  role   = aws_iam_role.agent.id
  policy = data.aws_iam_policy_document.agent.json
}

resource "aws_cloudwatch_log_group" "agent" {
  name              = "/aws/lambda/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigateway/${local.name_prefix}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_lambda_function" "agent" {
  function_name = local.name_prefix
  description   = "Grounded manufacturing IT and ERP support agent."
  role          = aws_iam_role.agent.arn
  runtime       = "python3.12"
  handler       = "app.lambda_handler"
  timeout       = 60
  memory_size   = 512

  filename         = data.archive_file.agent.output_path
  source_code_hash = data.archive_file.agent.output_base64sha256

  environment {
    variables = {
      KNOWLEDGE_BUCKET    = aws_s3_bucket.knowledge.id
      KNOWLEDGE_PREFIX    = "knowledge/"
      MODEL_ID            = var.bedrock_model_id
      MAX_QUESTION_CHARS  = tostring(var.max_question_chars)
      MIN_RETRIEVAL_SCORE = tostring(var.min_retrieval_score)
      TOP_K               = tostring(var.top_k)
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.agent,
    aws_iam_role_policy.agent,
    aws_iam_role_policy_attachment.agent_logs
  ]

  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "agent" {
  name          = local.name_prefix
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.allowed_origins
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type"]
    max_age       = 300
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "agent" {
  api_id                 = aws_apigatewayv2_api.agent.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.agent.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.agent.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.agent.id}"
}

resource "aws_apigatewayv2_route" "support" {
  api_id    = aws_apigatewayv2_api.agent.id
  route_key = "POST /support"
  target    = "integrations/${aws_apigatewayv2_integration.agent.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.agent.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId        = "$context.requestId"
      routeKey         = "$context.routeKey"
      status           = "$context.status"
      responseLength   = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
      sourceIp         = "$context.identity.sourceIp"
    })
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "api" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.agent.execution_arn}/*/*"
}
