# Terraform outputs for Gold Sentiment Analysis deployment

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.gold_sentiment.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.gold_sentiment.function_name
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "schedule_expression" {
  description = "Schedule expression for the Lambda function"
  value       = var.schedule_expression
}

output "event_rule_arn" {
  description = "ARN of the CloudWatch Events rule"
  value       = aws_cloudwatch_event_rule.schedule.arn
}
