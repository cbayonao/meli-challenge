#!/usr/bin/env python3
"""
Test configuration for Meli Challenge
Contains common test settings, constants, and configuration
"""

import os
from pathlib import Path

# Test configuration
TEST_CONFIG = {
    'timeout': 30,  # seconds
    'max_retries': 3,
    'test_data_dir': 'test_data',
    'reports_dir': 'test_reports',
    'coverage_dir': 'coverage',
    'log_level': 'INFO'
}

# Test data paths
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = PROJECT_ROOT / TEST_CONFIG['test_data_dir']
TEST_REPORTS_DIR = PROJECT_ROOT / TEST_CONFIG['reports_dir']
COVERAGE_DIR = PROJECT_ROOT / TEST_CONFIG['coverage_dir']

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_REPORTS_DIR.mkdir(exist_ok=True)
COVERAGE_DIR.mkdir(exist_ok=True)

# Test environment variables
TEST_ENV_VARS = {
    'AWS_ACCESS_KEY_ID': 'test-access-key',
    'AWS_SECRET_ACCESS_KEY': 'test-secret-key',
    'AWS_DEFAULT_REGION': 'us-east-1',
    'DYNAMODB_TABLE_NAME': 'test-table',
    'SQS_QUEUE_URL': 'https://sqs.us-east-1.amazonaws.com/test-queue',
    'ZYTE_API_KEY': 'test-zyte-key',
    'SCRAPY_LOG_LEVEL': 'ERROR',  # Reduce noise during tests
    'SCRAPY_CONCURRENT_REQUESTS': '1',  # Single request during tests
    'SCRAPY_DOWNLOAD_DELAY': '0'  # No delay during tests
}

# Test categories
TEST_CATEGORIES = {
    'unit': {
        'description': 'Unit tests for individual components',
        'modules': ['test_spiders', 'test_pipelines'],
        'timeout': 10
    },
    'integration': {
        'description': 'Integration tests for data flow',
        'modules': ['test_integration'],
        'timeout': 30
    },
    'spiders': {
        'description': 'Spider-specific tests',
        'modules': ['test_spiders'],
        'timeout': 15
    },
    'pipelines': {
        'description': 'Pipeline-specific tests',
        'modules': ['test_pipelines'],
        'timeout': 15
    }
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'pipeline_processing': 0.1,  # seconds
    'id_generation': 0.01,       # seconds
    'data_validation': 0.05,     # seconds
    'format_conversion': 0.02    # seconds
}

# Test data constants
SAMPLE_DATA = {
    'valid_urls': [
        'https://mercadolibre.com.uy/product/123',
        'https://articulo.mercadolibre.com.uy/MLU-123456789',
        'https://listado.mercadolibre.com.uy/electronics'
    ],
    'invalid_urls': [
        'invalid-url',
        'http://example.com/product',
        '',
        None
    ],
    'valid_prices': [
        '100,00',
        '1.234,56',
        '2.500.750,89',
        '50',
        '0,99'
    ],
    'invalid_prices': [
        'invalid',
        'price',
        '',
        None
    ],
    'valid_sellers': [
        'Por Test Seller',
        'Por Another Seller',
        'Seller Without Prefix',
        '  Seller With Spaces  '
    ],
    'invalid_sellers': [
        '',
        '   ',
        None
    ]
}

# Mock response data
MOCK_RESPONSES = {
    'product_page': {
        'url': 'https://mercadolibre.com.uy/product/123',
        'status': 200,
        'body': '''
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1>Test Product</h1>
                <div class="price">$1.234,56</div>
                <div class="seller">Por Test Seller</div>
            </body>
        </html>
        '''
    },
    'list_page': {
        'url': 'https://listado.mercadolibre.com.uy/electronics',
        'status': 200,
        'body': '''
        <html>
            <head><title>Electronics</title></head>
            <body>
                <div class="product-card">
                    <h2>Product 1</h2>
                    <a href="/product/1">View Product</a>
                </div>
                <div class="product-card">
                    <h2>Product 2</h2>
                    <a href="/product/2">View Product</a>
                </div>
            </body>
        </html>
        '''
    },
    'error_page': {
        'url': 'https://mercadolibre.com.uy/error',
        'status': 404,
        'body': '<html><body>Page not found</body></html>'
    }
}

# Test utilities configuration
UTIL_CONFIG = {
    'mock_aws': True,
    'mock_scrapy': True,
    'generate_reports': True,
    'save_test_data': False,
    'cleanup_after_tests': True
}


def setup_test_environment():
    """Set up test environment variables"""
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value


def cleanup_test_environment():
    """Clean up test environment variables"""
    for key in TEST_ENV_VARS.keys():
        if key in os.environ:
            del os.environ[key]


def get_test_data_path(filename):
    """Get full path for test data file"""
    return TEST_DATA_DIR / filename


def get_test_report_path(filename):
    """Get full path for test report file"""
    return TEST_REPORTS_DIR / filename


def get_coverage_path(filename):
    """Get full path for coverage file"""
    return COVERAGE_DIR / filename


# Test markers and tags
TEST_MARKERS = {
    'slow': 'Tests that take longer than 1 second',
    'integration': 'Tests that require multiple components',
    'aws': 'Tests that interact with AWS services',
    'scrapy': 'Tests that use Scrapy framework',
    'pipeline': 'Tests for pipeline components',
    'spider': 'Tests for spider components',
    'data': 'Tests for data processing and validation'
}

# Test execution order (if needed)
TEST_EXECUTION_ORDER = [
    'test_spiders',      # Test spiders first
    'test_pipelines',    # Then test pipelines
    'test_integration'   # Finally test integration
]
