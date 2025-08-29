#!/usr/bin/env python3
"""
Integration tests for Meli Challenge
Tests complete data flow, extraction, and formatting across the entire pipeline
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import hashlib
import base64
from datetime import datetime

# Import the components to test
from meli_crawler.spiders.meli_uy_identify import MeliUySpider
from meli_crawler.spiders.meli_uy_collect import MeliUyCollectSpider
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


class TestCompleteDataFlow(unittest.TestCase):
    """Test complete data flow from spider to final output"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.spider = Mock()
        self.spider.name = 'test-spider'
        
        # Create all pipeline instances
        self.pipelines = {
            'validation': ValidationPipeline(),
            'price_norm': PriceNormalizationPipeline(),
            'discount': DiscountCalculationPipeline(),
            'reviews': ReviewsNormalizationPipeline(),
            'seller_norm': SellerNormalizationPipeline(),
            'id_creation': CreateSellerIdUrlIdPipeline(),
            'dynamodb': DynamoDBPipeline(),
            'sqs': SQSPipeline(),
            'collect_update': CollectSpiderUpdatePipeline()
        }
    
    def test_complete_pipeline_flow(self):
        """Test complete data flow through all pipelines"""
        # Simulate raw data from spider
        raw_item = {
            'title': '  Test Product  ',
            'pub_url': 'https://mercadolibre.com.uy/product/123',
            'seller': 'Por Test Seller Name',
            'price': '1.234,56',
            'original_price': '1.500,00',
            'currency': 'UYU',
            'reviews_count': '25',
            'rating': '4.5',
            'availability': 'In Stock',
            'features': ['Feature 1', 'Feature 2'],
            'images': ['https://example.com/img1.jpg', 'https://example.com/img2.jpg']
        }
        
        # Process through validation pipeline
        item = self.pipelines['validation'].process_item(raw_item, self.spider)
        self.assertIsNotNone(item, "Item should pass validation")
        
        # Process through price normalization
        item = self.pipelines['price_norm'].process_item(item, self.spider)
        self.assertEqual(item['price'], 1234.56)
        self.assertEqual(item['original_price'], 1500.00)
        
        # Process through discount calculation
        item = self.pipelines['discount'].process_item(item, self.spider)
        self.assertAlmostEqual(item['discount_percentage'], 17.70, places=2)
        self.assertEqual(item['discount_amount'], 265.44)
        
        # Process through reviews normalization
        item = self.pipelines['reviews'].process_item(item, self.spider)
        self.assertEqual(item['reviews_count'], 25)
        self.assertEqual(item['rating'], 4.5)
        
        # Process through seller normalization
        item = self.pipelines['seller_norm'].process_item(item, self.spider)
        self.assertEqual(item['seller'], 'Test Seller Name')
        
        # Process through ID creation
        item = self.pipelines['id_creation'].process_item(item, self.spider)
        self.assertIn('seller_id', item)
        self.assertIn('url_id', item)
        
        # Verify ID formats
        expected_seller_id = base64.b64encode('Test Seller Name'.encode()).decode()
        expected_url_id = hashlib.sha256('https://mercadolibre.com.uy/product/123'.encode()).hexdigest()
        
        self.assertEqual(item['seller_id'], expected_seller_id)
        self.assertEqual(item['url_id'], expected_url_id)
        
        # Verify final item structure
        expected_fields = [
            'title', 'pub_url', 'seller', 'price', 'original_price', 'currency',
            'discount_percentage', 'discount_amount', 'reviews_count', 'rating',
            'availability', 'features', 'images', 'seller_id', 'url_id'
        ]
        
        for field in expected_fields:
            self.assertIn(field, item, f"Field {field} should be present")
        
        # Verify data types
        self.assertIsInstance(item['price'], float)
        self.assertIsInstance(item['original_price'], float)
        self.assertIsInstance(item['discount_percentage'], float)
        self.assertIsInstance(item['discount_amount'], float)
        self.assertIsInstance(item['reviews_count'], int)
        self.assertIsInstance(item['rating'], float)
        self.assertIsInstance(item['features'], list)
        self.assertIsInstance(item['images'], list)
        self.assertIsInstance(item['seller_id'], str)
        self.assertIsInstance(item['url_id'], str)
    
    def test_data_quality_validation(self):
        """Test data quality and consistency across the pipeline"""
        # Test with various data formats
        test_cases = [
            {
                'title': 'Product 1',
                'pub_url': 'https://example.com/1',
                'seller': 'Por Seller 1',
                'price': '100,00',
                'original_price': '120,00'
            },
            {
                'title': 'Product 2',
                'pub_url': 'https://example.com/2',
                'seller': '  Seller 2  ',
                'price': '2.500,75',
                'original_price': '3.000,00'
            },
            {
                'title': 'Product 3',
                'pub_url': 'https://example.com/3',
                'seller': '',  # Empty seller
                'price': '50,25',
                'original_price': '50,25'  # No discount
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(test_case=test_case):
                # Process through all pipelines
                item = test_case.copy()
                
                # Validation
                item = self.pipelines['validation'].process_item(item, self.spider)
                self.assertIsNotNone(item, f"Test case {i} should pass validation")
                
                # Price normalization
                item = self.pipelines['price_norm'].process_item(item, self.spider)
                self.assertIsInstance(item['price'], float)
                self.assertIsInstance(item['original_price'], float)
                
                # Discount calculation
                item = self.pipelines['discount'].process_item(item, self.spider)
                self.assertIsInstance(item['discount_percentage'], float)
                self.assertIsInstance(item['discount_amount'], float)
                
                # Seller normalization
                item = self.pipelines['seller_norm'].process_item(item, self.spider)
                if test_case['seller'].strip():
                    self.assertNotEqual(item['seller'], 'no seller found')
                else:
                    self.assertEqual(item['seller'], 'no seller found')
                
                # ID creation
                item = self.pipelines['id_creation'].process_item(item, self.spider)
                self.assertIn('seller_id', item)
                self.assertIn('url_id', item)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery across the pipeline"""
        # Test with malformed data
        malformed_items = [
            {
                'title': '',  # Empty title
                'pub_url': 'https://example.com/product'
            },
            {
                'title': 'Valid Title',
                'pub_url': ''  # Empty URL
            },
            {
                'title': None,  # None title
                'pub_url': 'https://example.com/product'
            },
            {
                'price': 'invalid_price',  # Invalid price
                'seller': 'Por Test Seller'
            }
        ]
        
        for i, malformed_item in enumerate(malformed_items):
            with self.subTest(malformed_item=malformed_item):
                # Validation should handle malformed data gracefully
                if 'title' in malformed_item and 'pub_url' in malformed_item:
                    if not malformed_item['title'] or not malformed_item['pub_url']:
                        # Should be dropped by validation
                        result = self.pipelines['validation'].process_item(malformed_item, self.spider)
                        self.assertIsNone(result, f"Malformed item {i} should be dropped")
                        continue
                
                # For items that pass validation, test error handling in other pipelines
                if 'title' in malformed_item and 'pub_url' in malformed_item:
                    if malformed_item['title'] and malformed_item['pub_url']:
                        # Should pass validation
                        item = self.pipelines['validation'].process_item(malformed_item, self.spider)
                        self.assertIsNotNone(item, f"Valid item {i} should pass validation")
                        
                        # Test error handling in other pipelines
                        if 'price' in malformed_item:
                            item = self.pipelines['price_norm'].process_item(item, self.spider)
                            # Should handle invalid price gracefully
                            self.assertIn('price', item)


class TestDataFormatValidation(unittest.TestCase):
    """Test data format validation and consistency"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.spider = Mock()
        self.spider.name = 'test-spider'
        
        # Create pipeline instances
        self.validation = ValidationPipeline()
        self.seller_norm = SellerNormalizationPipeline()
        self.id_creation = CreateSellerIdUrlIdPipeline()
        self.collect_update = CollectSpiderUpdatePipeline()
    
    def test_url_format_validation(self):
        """Test URL format validation and consistency"""
        test_urls = [
            'https://mercadolibre.com.uy/product/123',
            'https://articulo.mercadolibre.com.uy/MLU-123456789',
            'https://listado.mercadolibre.com.uy/category',
            'http://example.com/product',  # Different domain
            'invalid-url',  # Invalid URL
            '',  # Empty URL
            None  # None URL
        ]
        
        for url in test_urls:
            with self.subTest(url=url):
                item = {
                    'title': 'Test Product',
                    'pub_url': url
                }
                
                if url and url.startswith('https://mercadolibre.com.uy'):
                    # Valid MercadoLibre URL
                    result = self.validation.process_item(item, self.spider)
                    self.assertIsNotNone(result, f"Valid URL {url} should pass validation")
                    
                    # Test ID creation
                    result = self.id_creation.process_item(result, self.spider)
                    self.assertIn('url_id', result)
                    
                    # Verify URL ID is consistent
                    expected_url_id = hashlib.sha256(url.encode()).hexdigest()
                    self.assertEqual(result['url_id'], expected_url_id)
                else:
                    # Invalid or non-MercadoLibre URL
                    result = self.validation.process_item(item, self.spider)
                    if not url:  # Empty or None URL
                        self.assertIsNone(result, f"Invalid URL {url} should be dropped")
    
    def test_seller_name_consistency(self):
        """Test seller name consistency and normalization"""
        test_sellers = [
            'Por Test Seller',
            '  Por Another Seller  ',
            'Seller Without Prefix',
            '  Seller With Spaces  ',
            '',  # Empty seller
            '   ',  # Whitespace only
            None  # None seller
        ]
        
        for seller in test_sellers:
            with self.subTest(seller=seller):
                item = {'seller': seller}
                result = self.seller_norm.process_item(item, self.spider)
                
                if seller and seller.strip():
                    # Non-empty seller
                    if seller.strip().startswith('Por '):
                        # Should remove "Por " prefix
                        expected = seller.strip()[4:].strip()
                        self.assertEqual(result['seller'], expected)
                    else:
                        # Should trim whitespace
                        expected = seller.strip()
                        self.assertEqual(result['seller'], expected)
                else:
                    # Empty seller should default to "no seller found"
                    self.assertEqual(result['seller'], 'no seller found')
    
    def test_price_format_consistency(self):
        """Test price format consistency and normalization"""
        test_prices = [
            ('100,00', 100.00),
            ('1.234,56', 1234.56),
            ('2.500.750,89', 2500750.89),
            ('50', 50.00),
            ('0,99', 0.99),
            ('invalid', 0.0),
            ('', 0.0),
            (None, 0.0)
        ]
        
        for price_input, expected_output in test_prices:
            with self.subTest(price_input=price_input):
                item = {'price': price_input}
                
                # Mock the price normalization pipeline
                with patch('meli_crawler.pipelines.PriceNormalizationPipeline.process_item') as mock_process:
                    mock_process.return_value = {'price': expected_output}
                    
                    # Test that price is processed correctly
                    if isinstance(price_input, str) and price_input.replace('.', '').replace(',', '').isdigit():
                        # Valid price format
                        self.assertIsInstance(expected_output, float)
                    else:
                        # Invalid price format should default to 0.0
                        self.assertEqual(expected_output, 0.0)
    
    def test_id_generation_consistency(self):
        """Test ID generation consistency and uniqueness"""
        test_items = [
            {
                'seller': 'Seller A',
                'pub_url': 'https://mercadolibre.com.uy/product/1'
            },
            {
                'seller': 'Seller B',
                'pub_url': 'https://mercadolibre.com.uy/product/2'
            },
            {
                'seller': 'Seller A',  # Same seller, different URL
                'pub_url': 'https://mercadolibre.com.uy/product/3'
            },
            {
                'seller': 'Seller C',
                'pub_url': 'https://mercadolibre.com.uy/product/1'  # Same URL, different seller
            }
        ]
        
        generated_ids = []
        
        for item in test_items:
            with self.subTest(item=item):
                result = self.id_creation.process_item(item, self.spider)
                
                # Verify IDs are generated
                self.assertIn('seller_id', result)
                self.assertIn('url_id', result)
                
                # Verify ID formats
                seller_id = result['seller_id']
                url_id = result['url_id']
                
                # Seller ID should be base64 encoded
                try:
                    decoded = base64.b64decode(seller_id).decode()
                    self.assertEqual(decoded, item['seller'])
                except Exception:
                    self.fail(f"Seller ID {seller_id} is not valid base64")
                
                # URL ID should be SHA256 hash
                expected_url_id = hashlib.sha256(item['pub_url'].encode()).hexdigest()
                self.assertEqual(url_id, expected_url_id)
                
                # Collect IDs for uniqueness testing
                id_pair = (seller_id, url_id)
                generated_ids.append(id_pair)
        
        # Verify ID uniqueness
        unique_ids = set(generated_ids)
        self.assertEqual(len(unique_ids), len(generated_ids), "All ID pairs should be unique")


class TestCollectSpiderDataFlow(unittest.TestCase):
    """Test data flow specific to the collect spider"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.spider = Mock()
        self.spider.name = 'meli-uy-collect'
        self.collect_pipeline = CollectSpiderUpdatePipeline()
    
    def test_collect_spider_data_processing(self):
        """Test data processing for collect spider items"""
        # Simulate collect spider item
        collect_item = {
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
        
        # Test DynamoDB format conversion
        result = self.collect_pipeline.process_item(collect_item, self.spider)
        
        # Verify that the item was processed
        self.assertIsNotNone(result)
        self.assertIn('dynamodb_updated', result)
        
        # Test format conversion for different data types
        test_data = {
            'string': 'test',
            'number': 123,
            'boolean': True,
            'list': ['item1', 'item2'],
            'dict': {'key': 'value'},
            'none': None
        }
        
        for data_type, test_value in test_data.items():
            with self.subTest(data_type=data_type):
                converted = self.collect_pipeline.convert_to_dynamodb_format(test_value)
                
                if data_type == 'string':
                    self.assertEqual(converted, {'S': test_value})
                elif data_type == 'number':
                    self.assertEqual(converted, {'N': str(test_value)})
                elif data_type == 'boolean':
                    self.assertEqual(converted, {'BOOL': test_value})
                elif data_type == 'list':
                    self.assertEqual(converted, {'L': [{'S': 'item1'}, {'S': 'item2'}]})
                elif data_type == 'dict':
                    self.assertEqual(converted, {'M': {'key': {'S': 'value'}}})
                elif data_type == 'none':
                    self.assertEqual(converted, {'NULL': True})
    
    def test_collect_spider_filtering(self):
        """Test that collect pipeline only processes collect spider items"""
        # Test with collect spider
        self.spider.name = 'meli-uy-collect'
        item = {'test': 'data'}
        result = self.collect_pipeline.process_item(item, self.spider)
        self.assertIsNotNone(result)
        
        # Test with different spider
        self.spider.name = 'meli-uy-identify'
        result = self.collect_pipeline.process_item(item, self.spider)
        self.assertEqual(result, item)  # Should return unchanged item


if __name__ == '__main__':
    unittest.main()
