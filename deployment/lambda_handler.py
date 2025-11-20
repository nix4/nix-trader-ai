"""AWS Lambda handler for Gold sentiment analysis agent."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from nix_trader_ai.agents.gold_sentiment_agent import run_gold_sentiment_analysis
from nix_trader_ai.models.analysis import SentimentAnalysis


def lambda_handler(event, context):
    """AWS Lambda handler function.

    Args:
        event: Lambda event object
        context: Lambda context object

    Returns:
        Response with status code and body
    """
    try:
        # Run the async analysis
        result = asyncio.run(run_gold_sentiment_analysis())

        # Convert result to dict for JSON serialization
        response_body = {
            "status": "success",
            "analysis": {
                "overall_sentiment": result.overall_sentiment,
                "sentiment_components": result.sentiment_components,
                "themes": result.themes,
                "summary": result.summary,
                "timestamp": result.timestamp.isoformat() if hasattr(result, 'timestamp') else None,
            },
            "message": "Gold sentiment analysis completed successfully"
        }

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(response_body)
        }

    except Exception as e:
        error_message = f"Error running Gold sentiment analysis: {str(e)}"
        print(error_message)  # CloudWatch logs

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "status": "error",
                "message": error_message
            })
        }


# For local testing
if __name__ == "__main__":
    # Simulate Lambda event and context
    test_event = {}
    test_context = type('Context', (), {
        'function_name': 'gold-sentiment-analysis',
        'memory_limit_in_mb': 512,
        'invoked_function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:gold-sentiment-analysis',
        'aws_request_id': 'test-request-id'
    })()

    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
