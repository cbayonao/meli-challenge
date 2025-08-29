#!/usr/bin/env python3
"""
Lambda handler for data validation
Runs AI-powered validation on scraped data
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append('/opt/python/lib/python3.11/site-packages')
sys.path.append('/var/task')

from validation.ai_validator import AIValidator

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for data validation
    
    Args:
        event: Lambda event (SQS message with data to validate)
        context: Lambda context
        
    Returns:
        Response with validation results
    """
    try:
        logger.info("Starting data validation")
        
        # Get validation parameters from event or environment
        enable_ai = event.get('enable_ai', os.getenv('VALIDATION_ENABLE_AI', 'true').lower() == 'true')
        ai_provider = event.get('ai_provider', os.getenv('VALIDATION_AI_PROVIDER', 'openai'))
        batch_size = int(event.get('batch_size', os.getenv('VALIDATION_BATCH_SIZE', 10)))
        
        logger.info(f"Validation parameters: enable_ai={enable_ai}, ai_provider={ai_provider}, batch_size={batch_size}")
        
        # Initialize AI validator if enabled
        validator = None
        if enable_ai:
            try:
                validator = AIValidator(
                    provider=ai_provider,
                    api_key=os.getenv(f'{ai_provider.upper()}_API_KEY'),
                    model='gpt-4' if ai_provider == 'openai' else 'claude-3-sonnet-20240229',
                    batch_size=batch_size
                )
                logger.info(f"AI validator initialized with {ai_provider} provider")
            except Exception as e:
                logger.warning(f"Failed to initialize AI validator: {e}")
                enable_ai = False
        
        # Process validation data
        validation_results = []
        
        # Extract data from SQS event
        if 'Records' in event:
            for record in event['Records']:
                try:
                    # Parse SQS message body
                    message_body = json.loads(record['body'])
                    
                    # Validate the data
                    if validator and enable_ai:
                        # Use AI validation
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            validation_report = loop.run_until_complete(
                                validator.validate_item(message_body)
                            )
                            validation_results.append({
                                'message_id': record['messageId'],
                                'validation_report': validation_report
                            })
                        finally:
                            loop.close()
                    else:
                        # Basic validation without AI
                        validation_results.append({
                            'message_id': record['messageId'],
                            'status': 'basic_validation',
                            'message': 'AI validation not available'
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing record {record.get('messageId', 'unknown')}: {e}")
                    validation_results.append({
                        'message_id': record.get('messageId', 'unknown'),
                        'error': str(e)
                    })
        
        logger.info(f"Validation completed for {len(validation_results)} items")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data validation completed successfully',
                'results_count': len(validation_results),
                'ai_enabled': enable_ai,
                'ai_provider': ai_provider if enable_ai else None,
                'results': validation_results
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data validation: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to run data validation',
                'message': str(e)
            })
        }
