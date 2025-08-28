#!/usr/bin/env python3
"""
Test utilities and mock data for Meli Challenge tests
Provides common test fixtures, mock data, and utility functions
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import json
import hashlib
import base64
from datetime import datetime
from scrapy.http import Request, Response, HtmlResponse
from scrapy.utils.test import get_crawler


class MockSpider:
    """Mock spider class for testing"""
    
    def __init__(self, name='test-spider'):
        self.name = name
        self.logger = Mock()
        self.crawler = get_crawler()


class MockResponse:
    """Mock response class for testing"""
    
    def __init__(self, url='https://example.com', status=200, body='<html></html>'):
        self.url = url
        self.status = status
        self.body = body
        self.text = body
        self.meta = {}
        self.raw_api_response = {
            'product': {
                'currency': 'USD',
                'availability': 'InStock',
                'features': ['Feature 1', 'Feature 2'],
                'mainImage': {'url': 'https://example.com/main.jpg'},
                'images': [
                    {'url': 'https://example.com/img1.jpg'},
                    {'url': 'https://example.com/img2.jpg'}
                ],
                'description': 'Product description'
            }
        }


class TestDataFactory:
    """Factory class for creating test data"""
    
    @staticmethod
    def create_valid_item():
        """Create a valid item for testing"""
        return {
            'title': 'Test Product',
            'pub_url': 'https://mercadolibre.com.uy/product/123',
            'seller': 'Por Test Seller',
            'price': '1.234,56',
            'original_price': '1.500,00',
            'currency': 'UYU',
            'reviews_count': '25',
            'rating': '4.5',
            'availability': 'In Stock',
            'features': ['Feature 1', 'Feature 2'],
            'images': ['https://example.com/img1.jpg', 'https://example.com/img2.jpg']
        }
    
    @staticmethod
    def create_invalid_item():
        """Create an invalid item for testing"""
        return {
            'title': '',  # Empty title
            'pub_url': 'https://mercadolibre.com.uy/product/123'
        }
    
    @staticmethod
    def create_partial_item():
        """Create a partial item for testing"""
        return {
            'title': 'Test Product',
            'pub_url': 'https://mercadolibre.com.uy/product/123'
            # Missing other fields
        }
    
    @staticmethod
    def create_collect_item():
        """Create a collect spider item for testing"""
        return {
            'product': {
                'currency': 'USD',
                'availability': 'InStock',
                'features': ['Feature 1', 'Feature 2'],
                'mainImage': {'url': 'https://example.com/main.jpg'},
                'images': [
                    {'url': 'https://example.com/img1.jpg'},
                    {'url': 'https://example.com/img2.jpg'}
                ],
                'description': 'Product description'
            },
            'message_body': {
                'seller_id': 'base64_encoded_seller_id',
                'url_id': 'sha256_hash_url_id'
            }
        }
    
    @staticmethod
    def create_sqs_message():
        """Create a mock SQS message for testing"""
        return {
            'MessageId': 'test-message-id',
            'ReceiptHandle': 'test-receipt-handle',
            'Body': json.dumps({
                'seller_id': 'base64_encoded_seller_id',
                'url_id': 'sha256_hash_url_id',
                'inserted_at': datetime.now().isoformat()
            })
        }
    
    @staticmethod
    def create_dynamodb_item():
        """Create a mock DynamoDB item for testing"""
        return {
            'seller_id': {'S': 'base64_encoded_seller_id'},
            'url_id': {'S': 'sha256_hash_url_id'},
            'title': {'S': 'Test Product'},
            'price': {'N': '1234.56'},
            'currency': {'S': 'UYU'}
        }


class MockAWSServices:
    """Mock AWS services for testing"""
    
    @staticmethod
    def mock_sqs_client():
        """Create a mock SQS client"""
        mock_sqs = Mock()
        mock_sqs.receive_message.return_value = {
            'Messages': [TestDataFactory.create_sqs_message()]
        }
        mock_sqs.delete_message.return_value = {}
        mock_sqs.send_message.return_value = {
            'MessageId': 'test-message-id'
        }
        return mock_sqs
    
    @staticmethod
    def mock_dynamodb_client():
        """Create a mock DynamoDB client"""
        mock_dynamodb = Mock()
        mock_dynamodb.put_item.return_value = {
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 200
            }
        }
        mock_dynamodb.update_item.return_value = {
            'ResponseMetadata': {
                'RequestId': 'test-request-id',
                'HTTPStatusCode': 200
            },
            'Attributes': {
                'currency': {'S': 'USD'},
                'availability': {'S': 'InStock'}
            }
        }
        mock_dynamodb.get_item.return_value = {
            'Item': TestDataFactory.create_dynamodb_item()
        }
        return mock_dynamodb


class TestHelpers:
    """Helper functions for testing"""
    
    @staticmethod
    def assert_item_structure(item, expected_fields):
        """Assert that an item has the expected structure"""
        for field in expected_fields:
            assert field in item, f"Field '{field}' should be present in item"
    
    @staticmethod
    def assert_data_types(item, type_specs):
        """Assert that item fields have the expected data types"""
        for field, expected_type in type_specs.items():
            if field in item:
                assert isinstance(item[field], expected_type), \
                    f"Field '{field}' should be of type {expected_type.__name__}, got {type(item[field]).__name__}"
    
    @staticmethod
    def assert_price_format(price):
        """Assert that price is in the correct format"""
        assert isinstance(price, (int, float)), f"Price should be numeric, got {type(price)}"
        assert price >= 0, f"Price should be non-negative, got {price}"
    
    @staticmethod
    def assert_url_format(url):
        """Assert that URL is in the correct format"""
        assert isinstance(url, str), f"URL should be string, got {type(url)}"
        assert url.startswith('http'), f"URL should start with http, got {url}"
    
    @staticmethod
    def assert_seller_format(seller):
        """Assert that seller name is in the correct format"""
        assert isinstance(seller, str), f"Seller should be string, got {type(seller)}"
        assert not seller.startswith('Por '), f"Seller should not start with 'Por ', got {seller}"
        assert seller.strip() == seller, f"Seller should not have leading/trailing whitespace, got '{seller}'"
    
    @staticmethod
    def assert_id_format(seller_id, url_id):
        """Assert that IDs are in the correct format"""
        # Check seller_id is base64 encoded
        try:
            base64.b64decode(seller_id)
        except Exception:
            assert False, f"Seller ID should be base64 encoded, got {seller_id}"
        
        # Check url_id is SHA256 hash
        assert len(url_id) == 64, f"URL ID should be 64 characters (SHA256), got {len(url_id)}"
        assert all(c in '0123456789abcdef' for c in url_id), f"URL ID should be hexadecimal, got {url_id}"


class MockScrapyComponents:
    """Mock Scrapy components for testing"""
    
    @staticmethod
    def mock_request(url='https://example.com', meta=None):
        """Create a mock Scrapy request"""
        if meta is None:
            meta = {}
        
        request = Mock(spec=Request)
        request.url = url
        request.meta = meta
        return request
    
    @staticmethod
    def mock_response(url='https://example.com', body='<html></html>', meta=None):
        """Create a mock Scrapy response"""
        if meta is None:
            meta = {}
        
        response = Mock(spec=Response)
        response.url = url
        response.body = body.encode('utf-8')
        response.text = body
        response.meta = meta
        response.status = 200
        return response
    
    @staticmethod
    def mock_html_response(url='https://example.com', body='<html></html>', meta=None):
        """Create a mock HTML response"""
        if meta is None:
            meta = {}
        
        response = Mock(spec=HtmlResponse)
        response.url = url
        response.body = body.encode('utf-8')
        response.text = body
        response.meta = meta
        response.status = 200
        return response


class TestEnvironment:
    """Test environment setup and teardown"""
    
    @staticmethod
    def setup_test_environment():
        """Set up test environment variables"""
        import os
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-access-key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret-key'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'
        os.environ['SQS_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/test-queue'
        os.environ['ZYTE_API_KEY'] = 'test-zyte-key'
    
    @staticmethod
    def cleanup_test_environment():
        """Clean up test environment variables"""
        import os
        test_vars = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_DEFAULT_REGION',
            'DYNAMODB_TABLE_NAME',
            'SQS_QUEUE_URL',
            'ZYTE_API_KEY'
        ]
        
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]


class PerformanceTestMixin:
    """Mixin for performance testing"""
    
    def assert_performance_threshold(self, func, max_time, *args, **kwargs):
        """Assert that a function executes within a time threshold"""
        import time
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time <= max_time, \
            f"Function execution time {execution_time:.4f}s exceeds threshold {max_time}s"
        
        return result
    
    def benchmark_function(self, func, iterations=1000, *args, **kwargs):
        """Benchmark a function's performance"""
        import time
        
        times = []
        for _ in range(iterations):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        return {
            'iterations': iterations,
            'average_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'total_time': sum(times)
        }


# Common test data
SAMPLE_PRODUCTS = [
    {
        'title': 'iPhone 13 Pro',
        'pub_url': 'https://mercadolibre.com.uy/iphone-13-pro',
        'seller': 'Por Apple Store',
        'price': '1.299,99',
        'original_price': '1.499,99',
        'currency': 'USD',
        'reviews_count': '150',
        'rating': '4.8'
    },
    {
        'title': 'Samsung Galaxy S21',
        'pub_url': 'https://mercadolibre.com.uy/samsung-galaxy-s21',
        'seller': 'Por Samsung Store',
        'price': '899,99',
        'original_price': '999,99',
        'currency': 'USD',
        'reviews_count': '89',
        'rating': '4.6'
    },
    {
        'title': 'MacBook Air M1',
        'pub_url': 'https://mercadolibre.com.uy/macbook-air-m1',
        'seller': 'Por Mac Store',
        'price': '1.199,99',
        'original_price': '1.199,99',
        'currency': 'USD',
        'reviews_count': '67',
        'rating': '4.9'
    }
]

SAMPLE_SELLERS = [
    'Por Apple Store',
    'Por Samsung Store',
    'Por Mac Store',
    'Por Tech Store',
    'Por Mobile Store',
    '  Por Computer Store  ',
    'Por Gaming Store',
    'Por Accessories Store'
]

SAMPLE_PRICES = [
    '100,00',
    '1.234,56',
    '2.500.750,89',
    '50',
    '0,99',
    '999,99',
    '1.299,99',
    '899,99'
]

SAMPLE_URLS = [
    'https://mercadolibre.com.uy/product/123',
    'https://articulo.mercadolibre.com.uy/MLU-123456789',
    'https://listado.mercadolibre.com.uy/electronics',
    'https://mercadolibre.com.uy/category/phones',
    'https://mercadolibre.com.uy/search?q=laptop'
]
