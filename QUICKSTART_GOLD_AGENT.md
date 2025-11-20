# Gold Sentiment Agent - Quick Start Guide

## 🚀 5-Minute Setup

### 1. Test Locally (No API Keys Required)

```bash
# The agent includes mock data for testing
python3 test_gold_sentiment.py
```

**Expected Output:**
```
✅ ALL TESTS COMPLETED
✓ Gold sentiment analysis successful!
✓ Analyzed 5 news articles
✓ Generated sentiment score: 0.00
```

### 2. Add API Keys for Real Data

Edit `.env`:
```bash
# Required for AI analysis
OPENAI_API_KEY=sk-...

# Optional - for real news (at least one recommended)
NEWSAPI_KEY=your_newsapi_key          # Get from https://newsapi.org
ALPHA_VANTAGE_API_KEY=your_av_key     # Already have: 8IKN1611HYML3IJJ

# Optional - for Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 3. Test with Real News

```bash
# With API keys configured
python3 test_gold_sentiment.py
```

### 4. Deploy to AWS Lambda

```bash
cd deployment
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Edit terraform.tfvars with your API keys
# Then deploy:
./deploy.sh terraform
```

## 📝 Quick Commands

### Local Testing
```bash
# Full test
python3 test_gold_sentiment.py

# Just news collection
python3 -c "from test_gold_sentiment import test_news_collection; import asyncio; asyncio.run(test_news_collection())"
```

### Deployment
```bash
# Create package only
cd deployment && ./deploy.sh package

# Deploy with Terraform
cd deployment && ./deploy.sh terraform

# Update existing function
cd deployment && ./deploy.sh aws-cli
```

### Monitoring (After Deployment)
```bash
# Watch logs
aws logs tail /aws/lambda/gold-sentiment-analysis --follow

# Test manually
aws lambda invoke --function-name gold-sentiment-analysis response.json
cat response.json
```

## 🔑 Where to Get API Keys

### OpenAI (Required)
- Website: https://platform.openai.com/api-keys
- Cost: ~$0.10 per analysis with GPT-4
- Free tier: $5 credit for new accounts

### NewsAPI (Recommended)
- Website: https://newsapi.org/register
- Free tier: 500 requests/day
- Perfect for 6x daily analyses

### Alpha Vantage (Already Have!)
- You have: `8IKN1611HYML3IJJ`
- Already in your `.env` file
- Free tier: 500 requests/day

### Slack Webhook (For Notifications)
**Option 1: Webhook (Easier)**
1. Go to https://api.slack.com/messaging/webhooks
2. Create new webhook for your workspace
3. Copy webhook URL to `.env`

**Option 2: Bot Token (More Features)**
1. Create app at https://api.slack.com/apps
2. Add `chat:write` scope
3. Install to workspace
4. Copy bot token to `.env`

## 📊 What You Get

### Every 4 Hours (Configurable)
- Collects latest Gold news
- AI-powered sentiment analysis
- Slack notification with:
  - Sentiment score and direction
  - Key market themes
  - Price outlook prediction
  - Risk factors to watch

### Example Slack Message
```
🟢 Gold Market Sentiment Report

Sentiment Score: 0.75 (Bullish)
Confidence: 85%
Articles Analyzed: 23

Key Themes:
• Fed rate cut expectations rising
• Dollar weakness supporting prices
• Central bank buying continues
```

## 💰 Cost Estimate

| Service | Usage | Cost |
|---------|-------|------|
| AWS Lambda | 6 runs/day × 30s | ~$0.50/mo |
| CloudWatch Logs | 7 days retention | ~$0.10/mo |
| OpenAI API | 6 calls/day | ~$5-10/mo |
| NewsAPI | Free tier | $0 |
| **Total** | | **~$6-11/mo** |

## 🎯 Customization

### Change Schedule
Edit `deployment/terraform/terraform.tfvars`:
```hcl
# Every 6 hours
schedule_expression = "rate(6 hours)"

# Twice daily (9 AM and 9 PM UTC)
schedule_expression = "cron(0 9,21 * * ? *)"

# Only during market hours
schedule_expression = "cron(0 9,13,17 * * MON-FRI *)"
```

### Change News Keywords
Edit `src/nix_trader_ai/agents/gold_sentiment_agent.py`:
```python
keywords = [
    "gold price",
    "XAU",
    "precious metals",
    "your keywords here"
]
```

### Change Slack Channel
Edit `.env`:
```bash
SLACK_DEFAULT_CHANNEL=#your-channel-name
```

## ⚡ Troubleshooting

### "No news API keys configured"
- Set `NEWSAPI_KEY` or `ALPHA_VANTAGE_API_KEY` in `.env`
- Agent uses mock data when no keys are present

### "Slack notification skipped"
- Set `SLACK_WEBHOOK_URL` or `SLACK_BOT_TOKEN` in `.env`
- Agent works without Slack, just logs messages

### "OpenAI API error"
- Check `OPENAI_API_KEY` is valid
- Verify you have credits: https://platform.openai.com/usage

### Lambda timeout
- Increase timeout in `terraform/variables.tf`:
  ```hcl
  lambda_timeout = 600  # 10 minutes
  ```

## 📚 Documentation

- Full implementation: [GOLD_SENTIMENT_AGENT.md](GOLD_SENTIMENT_AGENT.md)
- Deployment guide: [deployment/README.md](deployment/README.md)
- Agent code: [src/nix_trader_ai/agents/gold_sentiment_agent.py](src/nix_trader_ai/agents/gold_sentiment_agent.py)

## 🆘 Getting Help

1. Check logs:
   ```bash
   # Local
   tail -f logs/*.log

   # AWS
   aws logs tail /aws/lambda/gold-sentiment-analysis --follow
   ```

2. Test components individually:
   ```bash
   python3 test_gold_sentiment.py
   ```

3. Verify API keys:
   ```bash
   python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OpenAI:', os.getenv('OPENAI_API_KEY')[:10])"
   ```

---

**Ready to deploy?** Run `python3 test_gold_sentiment.py` to verify everything works!
