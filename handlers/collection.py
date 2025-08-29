#!/usr/bin/env python3
"""
Lambda handler for collection spider
Runs the meli-uy-collect spider to extract product details
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append('/opt/python/lib/python3.11/site-packages')
sys.path.append('/var/task')

from meli_crawler.spiders.meli_uy_collect import MeliUyCollectSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for collection spider
    
    Args:
        event: Lambda event (SQS message with product data)
        context: Lambda context
        
    Returns:
        Response with execution status and results
    """
    try:
        logger.info("Starting collection spider")
        
        # Get spider parameters from event or environment
        max_batches = int(event.get('max_batches', os.getenv('MAX_BATCHES', 50)))
        max_messages_per_batch = int(event.get('max_messages_per_batch', os.getenv('MAX_MESSAGES_PER_BATCH', 10)))
        max_retries = int(event.get('max_retries', os.getenv('MAX_RETRIES', 3)))
        
        logger.info(f"Spider parameters: max_batches={max_batches}, max_messages_per_batch={max_messages_per_batch}, max_retries={max_retries}")
        
        # Configure Scrapy settings
        settings = get_project_settings()
        settings.set('LOG_LEVEL', os.getenv('SCRAPY_LOG_LEVEL', 'INFO'))
        settings.set('FEEDS', {
            'stdout': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2
            }
        })
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Add spider to process
        process.crawl(
            MeliUyCollectSpider,
            max_batches=max_batches,
            max_messages_per_batch=max_messages_per_batch,
            max_retries=max_retries
        )
        
        # Run the spider
        process.start()
        
        logger.info("Collection spider completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Collection spider completed successfully',
                'parameters': {
                    'max_batches': max_batches,
                    'max_messages_per_batch': max_messages_per_batch,
                    'max_retries': max_retries
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error running collection spider: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to run collection spider',
                'message': str(e)
            })
        }
