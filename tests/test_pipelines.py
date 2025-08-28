#!/usr/bin/env python3
"""
Unit tests for Scrapy pipelines
Tests data validation, normalization, and processing pipelines
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import hashlib
import base64

# Import the pipelines
from meli_crawler.pipelines import (
    ValidationPipeline,
    PriceNormalizationPipeline,
    DiscountCalculationPipeline,
    ReviewsNormalizationPipeline,
    SellerNormalizationPipeline,
    CreateSellerIdUrlIdPipeline,
    DynamoDBPipeline,
    SQSPipeline,
    CollectSpiderUpdatePipeline
)


class TestValidationPipeline(unittest.TestCase):
    """Test cases for ValidationPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = ValidationPipeline()
        self.spider = Mock()
        self.spider.name = 'test-spider'
    
    def test_required_fields_validation(self):
        """Test that required fields are properly validated"""
        # Valid item
        valid_item = {
            'title': 'Test Product',
            'pub_url': 'https://example.com/product'
        }
        result = self.pipeline.process_item(valid_item, self.spider)
        self.assertEqual(result, valid_item)
    
    def test_missing_required_fields(self):
        """Test that items with missing required fields are dropped"""
        # Missing title
        invalid_item = {
            'pub_url': 'https://example.com/product'
        }
        result = self.pipeline.process_item(invalid_item, self.spider)
        self.assertIsNone(result)
        
        # Missing pub_url
        invalid_item = {
            'title': 'Test Product'
        }
        result = self.pipeline.process_item(invalid_item, self.spider)
        self.assertIsNone(result)
    
    def test_empty_required_fields(self):
        """Test that items with empty required fields are dropped"""
        # Empty title
        invalid_item = {
            'title': '',
            'pub_url': 'https://example.com/product'
        }
        result = self.pipeline.process_item(invalid_item, self.spider)
        self.assertIsNone(result)
        
        # Empty pub_url
        invalid_item = {
            'title': 'Test Product',
            'pub_url': ''
        }
        result = self.pipeline.process_item(invalid_item, self.spider)
        self.assertIsNone(result)


class TestPriceNormalizationPipeline(unittest.TestCase):
    """Test cases for PriceNormalizationPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = PriceNormalizationPipeline()
        self.spider = Mock()
    
    def test_price_normalization(self):
        """Test price normalization logic"""
        # Test with valid price
        item = {
            'price': '1.234,56',
            'currency': 'UYU'
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['price'], 1234.56)
        self.assertEqual(result['currency'], 'UYU')
    
    def test_price_with_dots_and_commas(self):
        """Test price parsing with dots and commas"""
        item = {
            'price': '1.234.567,89',
            'currency': 'UYU'
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['price'], 1234567.89)
    
    def test_price_without_currency(self):
        """Test price processing without currency"""
        item = {
            'price': '100,50'
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['price'], 100.50)
        self.assertEqual(result['currency'], 'UYU')  # Default currency
    
    def test_invalid_price_handling(self):
        """Test handling of invalid price formats"""
        item = {
            'price': 'invalid',
            'currency': 'UYU'
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['price'], 0.0)


class TestDiscountCalculationPipeline(unittest.TestCase):
    """Test cases for DiscountCalculationPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = DiscountCalculationPipeline()
        self.spider = Mock()
    
    def test_discount_calculation(self):
        """Test discount calculation logic"""
        item = {
            'price': 100.0,
            'original_price': 150.0
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['discount_percentage'], 33.33)
        self.assertEqual(result['discount_amount'], 50.0)
    
    def test_no_discount(self):
        """Test when there's no discount"""
        item = {
            'price': 100.0,
            'original_price': 100.0
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['discount_percentage'], 0.0)
        self.assertEqual(result['discount_amount'], 0.0)
    
    def test_missing_original_price(self):
        """Test when original price is missing"""
        item = {
            'price': 100.0
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['discount_percentage'], 0.0)
        self.assertEqual(result['discount_amount'], 0.0)


class TestSellerNormalizationPipeline(unittest.TestCase):
    """Test cases for SellerNormalizationPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = SellerNormalizationPipeline()
        self.spider = Mock()
    
    def test_seller_normalization(self):
        """Test seller name normalization"""
        # Test removing "Por " prefix
        item = {
            'seller': 'Por Test Seller'
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['seller'], 'Test Seller')
    
    def test_seller_whitespace_trimming(self):
        """Test seller name whitespace trimming"""
        item = {
            'seller': '  Test Seller  '
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['seller'], 'Test Seller')
    
    def test_empty_seller_default(self):
        """Test default value for empty seller"""
        # Empty string
        item = {'seller': ''}
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['seller'], 'no seller found')
        
        # Whitespace only
        item = {'seller': '   '}
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['seller'], 'no seller found')
        
        # None value
        item = {'seller': None}
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['seller'], 'no seller found')
    
    def test_valid_seller_preserved(self):
        """Test that valid seller names are preserved"""
        item = {
            'seller': 'Valid Seller Name'
        }
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result['seller'], 'Valid Seller Name')


class TestCreateSellerIdUrlIdPipeline(unittest.TestCase):
    """Test cases for CreateSellerIdUrlIdPipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = CreateSellerIdUrlIdPipeline()
        self.spider = Mock()
    
    def test_seller_id_creation(self):
        """Test seller_id creation using base64 encoding"""
        item = {
            'seller': 'Test Seller'
        }
        result = self.pipeline.process_item(item, self.spider)
        
        # Verify seller_id is base64 encoded
        expected_seller_id = base64.b64encode('Test Seller'.encode()).decode()
        self.assertEqual(result['seller_id'], expected_seller_id)
    
    def test_url_id_creation(self):
        """Test url_id creation using SHA256 hash"""
        item = {
            'pub_url': 'https://example.com/product'
        }
        result = self.pipeline.process_item(item, self.spider)
        
        # Verify url_id is SHA256 hash
        expected_url_id = hashlib.sha256('https://example.com/product'.encode()).hexdigest()
        self.assertEqual(result['url_id'], expected_url_id)
    
    def test_both_ids_creation(self):
        """Test creation of both seller_id and url_id"""
        item = {
            'seller': 'Test Seller',
            'pub_url': 'https://example.com/product'
        }
        result = self.pipeline.process_item(item, self.spider)
        
        # Verify both IDs are created
        self.assertIn('seller_id', result)
        self.assertIn('url_id', result)
        
        # Verify they are different
        self.assertNotEqual(result['seller_id'], result['url_id'])
    
    def test_empty_values_handling(self):
        """Test handling of empty values"""
        item = {
            'seller': '',
            'pub_url': ''
        }
        result = self.pipeline.process_item(item, self.spider)
        
        # Should still create IDs for empty strings
        self.assertIn('seller_id', result)
        self.assertIn('url_id', result)


class TestCollectSpiderUpdatePipeline(unittest.TestCase):
    """Test cases for CollectSpiderUpdatePipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = CollectSpiderUpdatePipeline()
        self.spider = Mock()
        self.spider.name = 'meli-uy-collect'
    
    def test_convert_to_dynamodb_format(self):
        """Test DynamoDB format conversion"""
        # Test string conversion
        result = self.pipeline.convert_to_dynamodb_format("test")
        self.assertEqual(result, {'S': 'test'})
        
        # Test number conversion
        result = self.pipeline.convert_to_dynamodb_format(123)
        self.assertEqual(result, {'N': '123'})
        
        # Test boolean conversion
        result = self.pipeline.convert_to_dynamodb_format(True)
        self.assertEqual(result, {'BOOL': True})
        
        # Test list conversion
        result = self.pipeline.convert_to_dynamodb_format(['item1', 'item2'])
        self.assertEqual(result, {'L': [{'S': 'item1'}, {'S': 'item2'}]})
        
        # Test dict conversion
        result = self.pipeline.convert_to_dynamodb_format({'key': 'value'})
        self.assertEqual(result, {'M': {'key': {'S': 'value'}}})
        
        # Test None conversion
        result = self.pipeline.convert_to_dynamodb_format(None)
        self.assertEqual(result, {'NULL': True})
    
    def test_spider_filtering(self):
        """Test that pipeline only processes meli-uy-collect spider"""
        # Test with correct spider
        item = {'test': 'data'}
        result = self.pipeline.process_item(item, self.spider)
        self.assertIsNotNone(result)
        
        # Test with different spider
        self.spider.name = 'other-spider'
        result = self.pipeline.process_item(item, self.spider)
        self.assertEqual(result, item)  # Should return unchanged item
    
    def test_missing_product_data(self):
        """Test handling of missing product data"""
        item = {'message_body': {'seller_id': 'test', 'url_id': 'test'}}
        result = self.pipeline.process_item(item, self.spider)
        self.assertIsNotNone(result)
        self.assertIn('dynamodb_updated', result)


class TestPipelineIntegration(unittest.TestCase):
    """Test cases for pipeline integration and data flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.spider = Mock()
        self.spider.name = 'test-spider'
        
        # Create pipeline instances
        self.validation = ValidationPipeline()
        self.seller_norm = SellerNormalizationPipeline()
        self.id_creation = CreateSellerIdUrlIdPipeline()
    
    def test_pipeline_chain_validation(self):
        """Test that pipelines can be chained together"""
        # Test data flow through multiple pipelines
        item = {
            'title': 'Test Product',
            'pub_url': 'https://example.com/product',
            'seller': 'Por Test Seller'
        }
        
        # Process through validation pipeline
        item = self.validation.process_item(item, self.spider)
        self.assertIsNotNone(item)
        
        # Process through seller normalization
        item = self.seller_norm.process_item(item, self.spider)
        self.assertEqual(item['seller'], 'Test Seller')
        
        # Process through ID creation
        item = self.id_creation.process_item(item, self.spider)
        self.assertIn('seller_id', item)
        self.assertIn('url_id', item)
    
    def test_pipeline_error_handling(self):
        """Test that pipelines handle errors gracefully"""
        # Test with invalid data
        invalid_item = {}
        
        # Validation should handle this gracefully
        result = self.validation.process_item(invalid_item, self.spider)
        self.assertIsNone(result)
    
    def test_pipeline_data_integrity(self):
        """Test that pipelines maintain data integrity"""
        original_item = {
            'title': 'Test Product',
            'pub_url': 'https://example.com/product',
            'seller': 'Por Test Seller',
            'price': '100,50',
            'currency': 'UYU'
        }
        
        # Process through all pipelines
        item = original_item.copy()
        item = self.validation.process_item(item, self.spider)
        item = self.seller_norm.process_item(item, self.spider)
        item = self.id_creation.process_item(item, self.spider)
        
        # Verify original data is preserved
        self.assertEqual(item['title'], original_item['title'])
        self.assertEqual(item['pub_url'], original_item['pub_url'])
        
        # Verify transformations were applied
        self.assertEqual(item['seller'], 'Test Seller')  # Normalized
        self.assertIn('seller_id', item)  # Added
        self.assertIn('url_id', item)     # Added


if __name__ == '__main__':
    unittest.main()
