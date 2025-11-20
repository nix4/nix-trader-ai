# Terraform configuration for AWS Lambda deployment
# Gold Sentiment Analysis Agent

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
  default     = "gold-sentiment-analysis"
}

variable "schedule_expression" {
  description = "CloudWatch Events schedule expression"
  type        = string
  default     = "rate(4 hours)" # Run every 4 hours
  # Alternative: "cron(0 */4 * * ? *)" for cron syntax
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "newsapi_key" {
  description = "NewsAPI.org API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
  default     = ""
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function
resource "aws_lambda_function" "gold_sentiment" {
  filename         = "lambda_package.zip"
  function_name    = var.function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_handler.lambda_handler"
  source_code_hash = filebase64sha256("lambda_package.zip")
  runtime         = "python3.12"
  timeout         = 300 # 5 minutes
  memory_size     = 512

  environment {
    variables = {
      OPENAI_API_KEY          = var.openai_api_key
      NEWSAPI_KEY             = var.newsapi_key
      SLACK_WEBHOOK_URL       = var.slack_webhook_url
      LOGFIRE_TOKEN           = var.logfire_token
      ENABLE_TELEMETRY        = "true"
      LOGFIRE_ENVIRONMENT     = "production"
      LOGFIRE_SERVICE_NAME    = var.function_name
      PYTHONPATH              = "/var/task/src"
    }
  }

  # Enable CloudWatch Logs
  logging_config {
    log_format = "JSON"
    log_group  = "/aws/lambda/${var.function_name}"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 7
}

# CloudWatch Events Rule for scheduled execution
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.function_name}-schedule"
  description         = "Trigger Gold sentiment analysis periodically"
  schedule_expression = var.schedule_expression
}

# CloudWatch Events Target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "lambda"
  arn       = aws_lambda_function.gold_sentiment.arn
}

# Lambda permission for CloudWatch Events
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.gold_sentiment.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

# Outputs
output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.gold_sentiment.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.gold_sentiment.function_name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "schedule_expression" {
  description = "Schedule expression for the Lambda function"
  value       = var.schedule_expression
}
