# Terraform variables for Gold Sentiment Analysis deployment

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
  description = "CloudWatch Events schedule expression for periodic execution"
  type        = string
  default     = "rate(4 hours)"

  validation {
    condition = can(regex("^(rate\\(.*\\)|cron\\(.*\\))$", var.schedule_expression))
    error_message = "Schedule expression must be in format 'rate(...)' or 'cron(...)'"
  }
}

variable "openai_api_key" {
  description = "OpenAI API key for LLM analysis"
  type        = string
  sensitive   = true
}

variable "newsapi_key" {
  description = "NewsAPI.org API key for news collection"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alpha_vantage_api_key" {
  description = "Alpha Vantage API key for news and market data"
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

variable "slack_bot_token" {
  description = "Slack bot token for API-based messaging"
  type        = string
  sensitive   = true
  default     = ""
}

variable "slack_default_channel" {
  description = "Default Slack channel for notifications"
  type        = string
  default     = "#trading-alerts"
}

variable "logfire_token" {
  description = "Logfire API token for telemetry"
  type        = string
  sensitive   = true
  default     = ""
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300

  validation {
    condition     = var.lambda_timeout >= 60 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 60 and 900 seconds"
  }
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 and 10240 MB"
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7

  validation {
    condition = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Invalid log retention days value"
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "nix-trader-ai"
    Component   = "gold-sentiment-analysis"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
