#!/usr/bin/env python3
"""
Lambda handler for identification spider
Runs the meli-uy-identify spider to discover products
"""

import json
import logging
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append('/opt/python/lib/python3.11/site-packages')
sys.path.append('/var/task')

from meli_crawler.spiders.meli_uy_identify import MeliUyIdentifySpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy.signalmanager import SignalManager
from scrapy import signals

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for identification spider
    
    Args:
        event: Lambda event (can contain spider parameters)
        context: Lambda context
        
    Returns:
        Response with execution status and results
    """
    try:
        logger.info("Starting identification spider")
        
        # Get spider parameters from event or environment
        max_pages = int(event.get('max_pages', os.getenv('MAX_PAGES', 20)))
        max_items = int(event.get('max_items', os.getenv('MAX_ITEMS', 2000)))
        
        logger.info(f"Spider parameters: max_pages={max_pages}, max_items={max_items}")
        
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
            MeliUyIdentifySpider,
            max_pages=max_pages,
            max_items=max_items
        )
        
        # Run the spider
        process.start()
        
        logger.info("Identification spider completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Identification spider completed successfully',
                'parameters': {
                    'max_pages': max_pages,
                    'max_items': max_items
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error running identification spider: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to run identification spider',
                'message': str(e)
            })
        }
