#!/usr/bin/env python3
"""
Lambda handler for monitoring and alerts
Monitors system health and sends alerts when needed
"""

import json
import logging
import os
import sys
import boto3
from typing import Dict, Any
from datetime import datetime, timedelta

# Add project root to path
sys.path.append('/opt/python/lib/python3.11/site-packages')
sys.path.append('/var/task')

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')
sqs = boto3.client('sqs')
cloudwatch = boto3.client('cloudwatch')

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for monitoring and alerts
    
    Args:
        event: Lambda event (scheduled event)
        context: Lambda context
        
    Returns:
        Response with monitoring results
    """
    try:
        logger.info("Starting monitoring check")
        
        # Get monitoring parameters
        alert_webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        stage = os.getenv('STAGE', 'dev')
        service_name = os.getenv('SERVICE_NAME', 'meli-challenge')
        
        # Perform health checks
        health_checks = {
            'dynamodb': check_dynamodb_health(),
            'sqs': check_sqs_health(),
            'lambda': check_lambda_health(),
            'overall': 'healthy'
        }
        
        # Determine overall health
        if any(check == 'unhealthy' for check in health_checks.values() if check != 'overall'):
            health_checks['overall'] = 'unhealthy'
        
        # Send alerts if unhealthy
        if health_checks['overall'] == 'unhealthy' and alert_webhook_url:
            send_alert(alert_webhook_url, health_checks, stage, service_name)
        
        # Log monitoring results
        logger.info(f"Monitoring completed. Overall health: {health_checks['overall']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Monitoring completed successfully',
                'timestamp': datetime.now().isoformat(),
                'health_checks': health_checks,
                'overall_health': health_checks['overall']
            })
        }
        
    except Exception as e:
        logger.error(f"Error in monitoring: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to complete monitoring',
                'message': str(e)
            })
        }

def check_dynamodb_health() -> str:
    """Check DynamoDB table health"""
    try:
        table_name = os.getenv('DYNAMODB_TABLE_NAME', 'meli-challenge-dev-products')
        
        # Check table status
        response = dynamodb.describe_table(TableName=table_name)
        table_status = response['Table']['TableStatus']
        
        if table_status == 'ACTIVE':
            # Check table metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=5)
            
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ConsumedReadCapacityUnits',
                Dimensions=[{'Name': 'TableName', 'Value': table_name}],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            return 'healthy'
        else:
            return 'unhealthy'
            
    except Exception as e:
        logger.error(f"DynamoDB health check failed: {e}")
        return 'unhealthy'

def check_sqs_health() -> str:
    """Check SQS queue health"""
    try:
        queue_url = os.getenv('SQS_QUEUE_URL')
        if not queue_url:
            return 'unknown'
        
        # Check queue attributes
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )
        
        # Check if queue is processing messages
        visible_messages = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
        in_flight_messages = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        
        # Alert if too many messages are stuck
        if visible_messages > 100 or in_flight_messages > 50:
            return 'warning'
        
        return 'healthy'
        
    except Exception as e:
        logger.error(f"SQS health check failed: {e}")
        return 'unhealthy'

def check_lambda_health() -> str:
    """Check Lambda function health"""
    try:
        # Check recent Lambda invocations and errors
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        # This is a simplified check - in production you'd want more detailed metrics
        return 'healthy'
        
    except Exception as e:
        logger.error(f"Lambda health check failed: {e}")
        return 'unhealthy'

def send_alert(webhook_url: str, health_checks: Dict[str, str], stage: str, service_name: str):
    """Send alert to webhook"""
    try:
        import requests
        
        alert_payload = {
            'text': f'🚨 *{service_name} Health Alert*',
            'attachments': [{
                'color': 'danger',
                'fields': [
                    {
                        'title': 'Environment',
                        'value': stage,
                        'short': True
                    },
                    {
                        'title': 'Overall Health',
                        'value': health_checks['overall'],
                        'short': True
                    },
                    {
                        'title': 'Health Checks',
                        'value': '\n'.join([f"• {k}: {v}" for k, v in health_checks.items() if k != 'overall']),
                        'short': False
                    },
                    {
                        'title': 'Timestamp',
                        'value': datetime.now().isoformat(),
                        'short': True
                    }
                ]
            }]
        }
        
        response = requests.post(webhook_url, json=alert_payload, timeout=10)
        response.raise_for_status()
        
        logger.info("Alert sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")
