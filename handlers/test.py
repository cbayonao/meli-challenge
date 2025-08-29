import json
import os
import boto3
from datetime import datetime

def handler(event, context):
    """
    Simple test handler for Meli Challenge infrastructure
    """
    try:
        # Get environment variables
        table_name = os.environ.get('DYNAMODB_TABLE_NAME')
        zyte_key = os.environ.get('ZYTE_API_KEY')
        openai_key = os.environ.get('OPENAI_API_KEY')
        
        # Test DynamoDB connection
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(table_name)
        
        # Get table info
        table_info = table.table_status
        
        # Test SQS connection
        sqs = boto3.client('sqs')
        
        # Create test message
        test_message = {
            'message': 'Hello from Meli Challenge!',
            'timestamp': datetime.now().isoformat(),
            'table_status': table_info,
            'environment': os.environ.get('STAGE', 'dev')
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'data': test_message,
                'environment': {
                    'table_name': table_name,
                    'zyte_key_configured': bool(zyte_key),
                    'openai_key_configured': bool(openai_key)
                }
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        }
