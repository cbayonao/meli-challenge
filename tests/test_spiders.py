#!/usr/bin/env python3
"""
Unit tests for Scrapy spiders
Tests the MeliUySpider and MeliUyCollectSpider classes
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import scrapy
from scrapy.http import Request, Response
from scrapy.utils.test import get_crawler

# Import the spiders
from meli_crawler.spiders.meli_uy_identify import MeliUyIdentifySpider
from meli_crawler.spiders.meli_uy_collect import MeliUyCollectSpider


class TestMeliUySpider(unittest.TestCase):
    """Test cases for MeliUySpider"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.crawler = get_crawler()
        self.spider = MeliUyIdentifySpider()
    
    def test_spider_initialization(self):
        """Test spider initialization with default values"""
        self.assertEqual(self.spider.name, 'meli-uy-identify')
        self.assertEqual(self.spider.max_pages, 20)
        self.assertEqual(self.spider.max_items, 2000)
        self.assertEqual(self.spider.allowed_domains, ['mercadolibre.com.uy'])
    
    def test_spider_initialization_with_custom_values(self):
        """Test spider initialization with custom values"""
        spider = MeliUyIdentifySpider(max_pages=10, max_items=100)
        self.assertEqual(spider.max_pages, 10)
        self.assertEqual(spider.max_items, 100)
    
    def test_start_urls(self):
        """Test that start URLs are correctly set"""
        expected_urls = [
            'https://listado.mercadolibre.com.uy/',
            'https://listado.mercadolibre.com.uy/autos-motos-y-otros',
            'https://listado.mercadolibre.com.uy/inmuebles',
            'https://listado.mercadolibre.com.uy/vehiculos',
            'https://listado.mercadolibre.com.uy/servicios',
            'https://listado.mercadolibre.comuy/empleos',
            'https://listado.mercadolibre.com.uy/tecnologia',
            'https://listado.mercadolibre.com.uy/hogar-y-muebles',
            'https://listado.mercadolibre.com.uy/ropa-y-accesorios',
            'https://listado.mercadolibre.com.uy/salud-y-belleza',
            'https://listado.mercadolibre.com.uy/deportes',
            'https://listado.mercadolibre.com.uy/juguetes-y-bebes',
            'https://listado.mercadolibre.com.uy/animales-y-mascotas',
            'https://listado.mercadolibre.com.uy/agro',
            'https://listado.mercadolibre.com.uy/industrias-y-oficinas',
            'https://listado.mercadolibre.com.uy/otras-categorias'
        ]
        self.assertEqual(self.spider.start_urls, expected_urls)
    
    def test_custom_settings(self):
        """Test that custom settings are correctly configured"""
        self.assertIn('ITEM_PIPELINES', self.spider.custom_settings)
        self.assertIn('meli_crawler.pipelines.ValidationPipeline', 
                     self.spider.custom_settings['ITEM_PIPELINES'])
    
    def test_parse_method_exists(self):
        """Test that parse method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'parse'))
        self.assertTrue(callable(self.spider.parse))
    
    def test_parse_offer_page_method_exists(self):
        """Test that parse_offer_page method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'parse_offer_page'))
        self.assertTrue(callable(self.spider.parse_offer_page))


class TestMeliUyCollectSpider(unittest.TestCase):
    """Test cases for MeliUyCollectSpider"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.crawler = get_crawler()
        self.spider = MeliUyCollectSpider()
    
    def test_spider_initialization(self):
        """Test spider initialization with default values"""
        self.assertEqual(self.spider.name, 'meli-uy-collect')
        self.assertEqual(self.spider.max_batches, 100)
        self.assertEqual(self.spider.max_messages_per_batch, 10)
        self.assertEqual(self.spider.max_retries, 3)
        self.assertEqual(self.spider.allowed_domains, ['mercadolibre.com.uy'])
    
    def test_spider_initialization_with_custom_values(self):
        """Test spider initialization with custom values"""
        spider = MeliUyCollectSpider(max_batches=50, max_messages_per_batch=5)
        self.assertEqual(spider.max_batches, 50)
        self.assertEqual(spider.max_messages_per_batch, 5)
    
    def test_custom_settings(self):
        """Test that custom settings are correctly configured"""
        self.assertIn('ADDONS', self.spider.custom_settings)
        self.assertIn('scrapy_zyte_api.Addon', 
                     self.spider.custom_settings['ADDONS'])
        self.assertIn('ITEM_PIPELINES', self.spider.custom_settings)
        self.assertIn('meli_crawler.pipelines.CollectSpiderUpdatePipeline', 
                     self.spider.custom_settings['ITEM_PIPELINES'])
    
    def test_parse_method_exists(self):
        """Test that parse method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'parse'))
        self.assertTrue(callable(self.spider.parse))
    
    def test_handle_retry_error_method_exists(self):
        """Test that handle_retry_error method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'handle_retry_error'))
        self.assertTrue(callable(self.spider.handle_retry_error))
    
    def test_delete_sqs_message_method_exists(self):
        """Test that delete_sqs_message method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'delete_sqs_message'))
        self.assertTrue(callable(self.spider.delete_sqs_message))
    
    def test_extract_keys_from_message_method_exists(self):
        """Test that extract_keys_from_message method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'extract_keys_from_message'))
        self.assertTrue(callable(self.spider.extract_keys_from_message))
    
    def test_get_pub_url_from_dynamo_method_exists(self):
        """Test that get_pub_url_from_dynamo method exists and is callable"""
        self.assertTrue(hasattr(self.spider, 'get_pub_url_from_dynamo'))
        self.assertTrue(callable(self.spider.get_pub_url_from_dynamo))


class TestSpiderConfiguration(unittest.TestCase):
    """Test cases for spider configuration and settings"""
    
    def test_spider_names_are_unique(self):
        """Test that spider names are unique"""
        spider_names = [MeliUyIdentifySpider.name, MeliUyCollectSpider.name]
        self.assertEqual(len(spider_names), len(set(spider_names)))
    
    def test_allowed_domains_consistency(self):
        """Test that both spiders have consistent allowed domains"""
        meli_spider = MeliUyIdentifySpider()
        collect_spider = MeliUyCollectSpider()
        
        self.assertEqual(meli_spider.allowed_domains, collect_spider.allowed_domains)
    
    def test_custom_settings_structure(self):
        """Test that custom settings have the expected structure"""
        meli_spider = MeliUyIdentifySpider()
        collect_spider = MeliUyCollectSpider()
        
        # Check that both spiders have custom settings
        self.assertIsInstance(meli_spider.custom_settings, dict)
        self.assertIsInstance(collect_spider.custom_settings, dict)
        
        # Check that both spiders have ITEM_PIPELINES
        self.assertIn('ITEM_PIPELINES', meli_spider.custom_settings)
        self.assertIn('ITEM_PIPELINES', collect_spider.custom_settings)


if __name__ == '__main__':
    unittest.main()
