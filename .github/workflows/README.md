# GitHub Actions Workflows

This directory contains automated workflows for the nix-trader-ai project.

## Gold Sentiment Analysis Workflow

**File:** `gold-sentiment-analysis.yml`

### Schedule

The Gold Sentiment Analysis runs automatically at the following times (GMT/UTC):

**Morning Session:**
- 5:00 AM GMT
- 5:30 AM GMT
- 6:00 AM GMT
- 6:30 AM GMT
- 7:00 AM GMT

**Afternoon Session:**
- 12:30 PM GMT
- 1:00 PM GMT
- 1:30 PM GMT
- 2:00 PM GMT

**Evening Session:**
- 6:00 PM GMT
- 6:30 PM GMT
- 7:00 PM GMT
- 8:00 PM GMT
- 8:30 PM GMT
- 9:00 PM GMT

**Total:** 15 scheduled runs per day

### What it does

1. Fetches real-time Gold (XAU/USD) market data with 24-hour hourly price history
2. Collects recent news articles about gold markets
3. Performs AI-powered sentiment analysis
4. Sends results to configured Slack channel
5. Uploads telemetry to Logfire

### Required Secrets

Configure these secrets in your GitHub repository settings (Settings → Secrets and variables → Actions):

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for sentiment analysis | **Yes** |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for notifications | **Yes** |
| `LOGFIRE_TOKEN` | Logfire API token for telemetry | Recommended |
| `SLACK_BOT_TOKEN` | Slack bot token (alternative to webhook) | Optional |
| `SLACK_DEFAULT_CHANNEL` | Default Slack channel for messages | Optional |
| `NEWSAPI_KEY` | NewsAPI.org API key | Optional |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | Optional |

### Manual Trigger

You can manually trigger the workflow from the GitHub Actions tab:

1. Go to **Actions** → **Gold Sentiment Analysis**
2. Click **Run workflow**
3. Select branch and click **Run workflow**

### Monitoring

- View workflow runs in the **Actions** tab
- Check Slack for analysis results
- View telemetry in Logfire dashboard
- Logs are uploaded as artifacts on failure (retained for 7 days)

### Cron Schedule Format

GitHub Actions uses standard cron syntax:
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

Example: `30 5 * * *` = 5:30 AM every day

### Notes

- GitHub Actions uses UTC timezone (same as GMT)
- Scheduled workflows may have a delay of up to 10 minutes during high load
- Free tier includes 2,000 minutes/month for private repos, unlimited for public repos
- Each run takes approximately 30-60 seconds
