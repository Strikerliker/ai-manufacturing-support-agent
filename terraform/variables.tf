variable "aws_region" {
  description = "AWS Region for the manufacturing support agent."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short project name used in resource naming."
  type        = string
  default     = "manufacturing-support-agent"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "portfolio"
}

variable "bedrock_model_id" {
  description = "Amazon Bedrock foundation model ID used for grounded responses."
  type        = string
  default     = "amazon.nova-lite-v1:0"
}

variable "max_question_chars" {
  description = "Maximum accepted support question length."
  type        = number
  default     = 2000
}

variable "min_retrieval_score" {
  description = "Minimum lexical retrieval score required before model invocation."
  type        = number
  default     = 0.08
}

variable "top_k" {
  description = "Maximum number of retrieved support passages provided to the model."
  type        = number
  default     = 4
}

variable "log_retention_days" {
  description = "CloudWatch log retention period."
  type        = number
  default     = 14
}

variable "throttling_burst_limit" {
  description = "API Gateway burst request limit."
  type        = number
  default     = 10
}

variable "throttling_rate_limit" {
  description = "API Gateway sustained request rate limit."
  type        = number
  default     = 5
}

variable "allowed_origins" {
  description = "CORS origins permitted to call the API from a browser."
  type        = list(string)
  default     = ["https://dumm.cloud"]
}

variable "tags" {
  description = "Additional tags for supported AWS resources."
  type        = map(string)
  default     = {}
}
