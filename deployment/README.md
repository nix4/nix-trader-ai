# Gold Sentiment Analysis - Cloud Deployment Guide

This directory contains deployment configurations for the Gold Sentiment Analysis agent to run periodically on AWS Lambda.

## Overview

The Gold Sentiment Agent:
- 🔍 Collects latest news related to Gold markets every 4 hours
- 🤖 Analyzes sentiment using AI to determine market impact
- 📊 Evaluates geopolitical events, Fed policy, and other Gold-specific factors
- 📱 Sends formatted notifications to Slack with actionable insights
- ☁️ Runs automatically on AWS Lambda on a configurable schedule

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** (v1.0+) installed
3. **AWS CLI** configured with credentials
4. **Python 3.12** installed locally
5. **API Keys**:
   - OpenAI API key (required)
   - NewsAPI.org key (recommended) - Get from https://newsapi.org
   - Alpha Vantage key (optional) - Get from https://www.alphavantage.co
6. **Slack Webhook URL** or Bot Token (required for notifications)

## Quick Start

### 1. Configure API Keys

Copy the example configuration:
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and add your API keys:
```hcl
openai_api_key = "sk-..."
newsapi_key = "your-newsapi-key"
slack_webhook_url = "https://hooks.slack.com/services/..."
```

### 2. Deploy to AWS

Run the deployment script:
```bash
cd ..
./deploy.sh terraform
```

This will:
- Install dependencies for Lambda
- Package the application code
- Deploy using Terraform
- Set up CloudWatch Events for scheduled execution

### 3. Verify Deployment

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/gold-sentiment-analysis --follow
```

Test manually:
```bash
aws lambda invoke \
  --function-name gold-sentiment-analysis \
  --payload '{}' \
  response.json
```

## Deployment Options

### Option 1: Terraform (Recommended)

```bash
./deploy.sh terraform
```

Full infrastructure as code with automated scheduling.

### Option 2: AWS CLI

Update existing function:
```bash
./deploy.sh aws-cli
```

### Option 3: Manual Package

Create package only:
```bash
./deploy.sh package
```

Then upload `lambda_package.zip` via AWS Console.

## Configuration

### Schedule Configuration

Edit `terraform/terraform.tfvars`:

```hcl
# Run every 4 hours
schedule_expression = "rate(4 hours)"

# Run every 6 hours
schedule_expression = "rate(6 hours)"

# Run daily at 9 AM UTC
schedule_expression = "cron(0 9 * * ? *)"

# Run every 4 hours during market hours (9 AM, 1 PM, 5 PM, 9 PM UTC)
schedule_expression = "cron(0 9,13,17,21 * * ? *)"
```

### Lambda Configuration

Adjust compute resources in `terraform/terraform.tfvars`:

```hcl
lambda_timeout = 300      # 5 minutes
lambda_memory_size = 512  # 512 MB
```

### Slack Configuration

Two options for Slack integration:

**Option 1: Webhook URL (Simpler)**
```hcl
slack_webhook_url = "https://hooks.slack.com/services/..."
```

**Option 2: Bot Token (More features)**
```hcl
slack_bot_token = "xoxb-..."
slack_default_channel = "#trading-alerts"
```

## Slack Notification Format

The agent sends rich-formatted messages to Slack:

```
🟢 Gold Market Sentiment Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Sentiment Score: 0.65 (Bullish)
Confidence: 78%
Articles Analyzed: 23
Price Outlook: 📈 Bullish

Key Themes:
• Federal Reserve signals rate cuts
• Dollar weakness boosting Gold appeal
• Central banks increasing Gold reserves
• Safe-haven demand from geopolitical tensions

Summary:
Gold sentiment remains strongly bullish driven by Fed rate cut
expectations and persistent dollar weakness...

⚠️ Risk Factors:
• Stronger than expected employment data
• Hawkish Fed speakers
```

## Architecture

```
CloudWatch Events (Scheduler)
    ↓
AWS Lambda Function
    ↓
    ├─→ NewsAPI / Alpha Vantage (News Collection)
    ├─→ OpenAI API (Sentiment Analysis)
    └─→ Slack (Notifications)
```

## Local Testing

Test the Lambda function locally:

```bash
./deploy.sh test
```

Or test directly:
```bash
cd deployment
python3 lambda_handler.py
```

## Monitoring

### CloudWatch Logs

View logs:
```bash
aws logs tail /aws/lambda/gold-sentiment-analysis --follow
```

### CloudWatch Metrics

Monitor in AWS Console:
- Invocations
- Duration
- Errors
- Throttles

### Alerts

Set up CloudWatch Alarms for:
- Function errors
- High duration
- Throttling

## Cost Estimation

Assuming execution every 4 hours (6 times/day):

- **Lambda**: ~$0.50/month (512MB, 30s duration)
- **CloudWatch Logs**: ~$0.10/month (7 days retention)
- **OpenAI API**: ~$5-10/month (depends on usage)
- **NewsAPI**: Free tier (500 requests/day)

**Total**: ~$6-11/month

## Troubleshooting

### Package Too Large

If deployment package exceeds 50MB:

1. Use Lambda Layers for dependencies
2. Remove unnecessary packages
3. Upload to S3 instead of direct upload

### Import Errors

Ensure PYTHONPATH is set:
```python
PYTHONPATH=/var/task/src
```

### API Rate Limits

NewsAPI free tier: 500 requests/day
- Reduce frequency or upgrade plan

### Timeout Errors

Increase timeout in `terraform/variables.tf`:
```hcl
variable "lambda_timeout" {
  default = 300  # Increase if needed
}
```

## Alternative Deployment Platforms

### Google Cloud Functions

See `deployment/gcp/` (to be created)

### Azure Functions

See `deployment/azure/` (to be created)

### Docker Container

Run as a containerized cron job:

```bash
docker build -t gold-sentiment .
docker run -e OPENAI_API_KEY=... gold-sentiment
```

## Updating the Deployment

To update the function:

```bash
# Make code changes
cd deployment

# Redeploy
./deploy.sh terraform
```

## Clean Up

Remove all resources:

```bash
cd terraform
terraform destroy
```

Or clean local artifacts:
```bash
./deploy.sh clean
```

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use AWS Secrets Manager** for production keys
3. **Restrict IAM permissions** to minimum required
4. **Enable AWS CloudTrail** for audit logging
5. **Use VPC** if accessing private resources
6. **Encrypt environment variables** in Lambda

## Support

For issues or questions:
- Check CloudWatch Logs for errors
- Review Terraform plan output
- Test locally first with `./deploy.sh test`

## Next Steps

1. Set up CloudWatch Alarms for monitoring
2. Configure SNS for error notifications
3. Add DynamoDB for storing analysis history
4. Create API Gateway for on-demand analysis
5. Add more news sources for better coverage
6. Implement caching to reduce API costs
