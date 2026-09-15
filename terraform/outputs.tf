output "api_url" {
  description = "Base URL for the manufacturing support agent API."
  value       = aws_apigatewayv2_api.agent.api_endpoint
}

output "knowledge_bucket" {
  description = "Private S3 bucket containing approved support procedures."
  value       = aws_s3_bucket.knowledge.id
}

output "lambda_function_name" {
  description = "Name of the support-agent Lambda function."
  value       = aws_lambda_function.agent.function_name
}

output "bedrock_model_id" {
  description = "Configured Amazon Bedrock model ID."
  value       = var.bedrock_model_id
}
