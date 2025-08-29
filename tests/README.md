# 🧪 Testing Guide for Meli Challenge

This document explains how to run tests, understand test structure, and contribute to the test suite for your Scrapy project.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Writing Tests](#writing-tests)
- [Test Utilities](#test-utilities)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The test suite provides comprehensive testing for:

- **Spider Classes**: Initialization, configuration, and basic functionality
- **Pipeline Components**: Data validation, normalization, and processing
- **Integration Flows**: Complete data flow from spider to final output
- **Data Format Validation**: URL formats, price formats, seller names
- **Error Handling**: Malformed data, missing fields, edge cases

## 🏗️ Test Structure

```
tests/
├── __init__.py              # Package initialization
├── test_spiders.py          # Spider unit tests
├── test_pipelines.py        # Pipeline unit tests
├── test_integration.py      # Integration tests
├── test_utils.py            # Test utilities and mock data
├── test_config.py           # Test configuration
├── run_tests.py             # Test runner script
├── README.md                # This file
├── test_data/               # Test data files (auto-created)
├── test_reports/            # Test reports (auto-created)
└── coverage/                # Coverage reports (auto-created)
```

## 🚀 Running Tests

### **Basic Test Commands**

```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Unit tests only
make test-spiders       # Spider tests only
make test-pipelines     # Pipeline tests only
make test-integration   # Integration tests only

# Run tests with coverage
make test-coverage

# Run tests locally
python -m pytest tests/ -v

# List all available tests
make test-list

# Generate test report
make test-report

# Clean test artifacts
make test-clean
```

### **Using the Test Runner Script**

```bash
# Run all tests
python tests/run_tests.py

# Run by category
python tests/run_tests.py --category spiders
python tests/run_tests.py --category pipelines
python tests/run_tests.py --category integration
python tests/run_tests.py --category unit

# Run specific test pattern
python tests/run_tests.py --pattern TestMeliUySpider
python tests/run_tests.py --pattern TestValidationPipeline

# Custom verbosity
python tests/run_tests.py --verbosity 0  # Minimal output
python tests/run_tests.py --verbosity 1  # Standard output
python tests/run_tests.py --verbosity 2  # Detailed output

# Stop on first failure
python tests/run_tests.py --failfast

# Generate report
python tests/run_tests.py --report my_report.txt

# List tests without running
python tests/run_tests.py --list
```

### **Using Python unittest directly**

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_spiders -v

# Run specific test class
python -m unittest tests.test_spiders.TestMeliUySpider -v

# Run specific test method
python -m unittest tests.test_spiders.TestMeliUySpider.test_spider_initialization -v
```

## 📊 Test Categories

### **1. Unit Tests (`test_spiders.py`)**

Tests individual spider components in isolation:

- **Spider Initialization**: Default values, custom parameters
- **Configuration**: Custom settings, allowed domains
- **Method Existence**: Required methods are present and callable
- **Data Validation**: Input parameter handling

**Example Test:**
```python
def test_spider_initialization(self):
    """Test spider initialization with default values"""
    self.assertEqual(self.spider.name, 'meli-uy-identify')
    self.assertEqual(self.spider.max_pages, 20)
    self.assertEqual(self.spider.max_items, 2000)
```

### **2. Pipeline Tests (`test_pipelines.py`)**

Tests data processing pipelines:

- **Validation Pipeline**: Required field validation
- **Price Normalization**: Price format conversion
- **Seller Normalization**: Seller name cleaning
- **ID Generation**: Base64 and SHA256 encoding
- **Data Type Conversion**: DynamoDB format conversion

**Example Test:**
```python
def test_seller_normalization(self):
    """Test seller name normalization"""
    item = {'seller': 'Por Test Seller'}
    result = self.pipeline.process_item(item, self.spider)
    self.assertEqual(result['seller'], 'Test Seller')
```

### **3. Integration Tests (`test_integration.py`)**

Tests complete data flow across components:

- **Complete Pipeline Flow**: End-to-end data processing
- **Data Quality Validation**: Format consistency
- **Error Handling**: Malformed data processing
- **Data Format Validation**: URL, price, seller formats
- **Collect Spider Flow**: Specialized data processing

**Example Test:**
```python
def test_complete_pipeline_flow(self):
    """Test complete data flow through all pipelines"""
    raw_item = TestDataFactory.create_valid_item()
    
    # Process through validation pipeline
    item = self.pipelines['validation'].process_item(raw_item, self.spider)
    self.assertIsNotNone(item, "Item should pass validation")
    
    # Process through price normalization
    item = self.pipelines['price_norm'].process_item(item, self.spider)
    self.assertEqual(item['price'], 1234.56)
```

## ✍️ Writing Tests

### **Test Class Structure**

```python
class TestYourComponent(unittest.TestCase):
    """Test cases for YourComponent"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.component = YourComponent()
        self.spider = MockSpider()
    
    def test_specific_functionality(self):
        """Test specific functionality"""
        # Arrange
        input_data = "test input"
        
        # Act
        result = self.component.process(input_data)
        
        # Assert
        self.assertEqual(result, "expected output")
    
    def tearDown(self):
        """Clean up after tests"""
        pass
```

### **Test Method Naming Convention**

- **Format**: `test_<what_is_tested>_<under_what_conditions>`
- **Examples**:
  - `test_spider_initialization_with_default_values`
  - `test_price_normalization_with_dots_and_commas`
  - `test_seller_normalization_removes_por_prefix`

### **Assertion Methods**

```python
# Basic assertions
self.assertEqual(actual, expected)
self.assertNotEqual(actual, expected)
self.assertTrue(condition)
self.assertFalse(condition)
self.assertIsNone(value)
self.assertIsNotNone(value)

# Collection assertions
self.assertIn(item, collection)
self.assertNotIn(item, collection)
self.assertIsInstance(obj, type)
self.assertRaises(exception_type, callable, *args)

# String assertions
self.assertIn(substring, string)
self.assertNotIn(substring, string)
self.assertRegex(string, pattern)
```

### **Using Test Utilities**

```python
from tests.test_utils import TestDataFactory, TestHelpers

class TestYourPipeline(unittest.TestCase):
    def test_data_processing(self):
        # Use factory to create test data
        item = TestDataFactory.create_valid_item()
        
        # Process the item
        result = self.pipeline.process_item(item, self.spider)
        
        # Use helpers to validate
        TestHelpers.assert_item_structure(result, ['title', 'price', 'seller'])
        TestHelpers.assert_data_types(result, {
            'price': float,
            'seller': str
        })
```

## 🛠️ Test Utilities

### **TestDataFactory**

Creates standardized test data:

```python
# Create valid test item
valid_item = TestDataFactory.create_valid_item()

# Create invalid test item
invalid_item = TestDataFactory.create_invalid_item()

# Create collect spider item
collect_item = TestDataFactory.create_collect_item()

# Create mock AWS services
mock_sqs = MockAWSServices.mock_sqs_client()
mock_dynamodb = MockAWSServices.mock_dynamodb_client()
```

### **TestHelpers**

Provides common validation functions:

```python
# Validate item structure
TestHelpers.assert_item_structure(item, ['title', 'price', 'seller'])

# Validate data types
TestHelpers.assert_data_types(item, {
    'price': float,
    'seller': str
})

# Validate specific formats
TestHelpers.assert_price_format(item['price'])
TestHelpers.assert_url_format(item['pub_url'])
TestHelpers.assert_seller_format(item['seller'])
TestHelpers.assert_id_format(item['seller_id'], item['url_id'])
```

### **Mock Components**

Provides mock Scrapy and AWS components:

```python
# Mock Scrapy components
request = MockScrapyComponents.mock_request(url='https://example.com')
response = MockScrapyComponents.mock_response(body='<html></html>')

# Mock spider
spider = MockSpider(name='test-spider')
```

## 📋 Best Practices

### **1. Test Organization**

- **One test class per component**
- **One test method per functionality**
- **Clear, descriptive test names**
- **Consistent setup and teardown**

### **2. Test Data Management**

- **Use factories for test data creation**
- **Avoid hardcoded test values**
- **Clean up test data after tests**
- **Use realistic but minimal test data**

### **3. Mocking Strategy**

- **Mock external dependencies (AWS, HTTP)**
- **Mock time-consuming operations**
- **Use realistic mock data**
- **Verify mock interactions when relevant**

### **4. Assertion Strategy**

- **Test one thing per test method**
- **Use specific assertions**
- **Provide clear error messages**
- **Test both positive and negative cases**

### **5. Performance Considerations**

- **Keep tests fast (< 1 second each)**
- **Use performance mixins for slow tests**
- **Mock expensive operations**
- **Run performance tests separately**

## 🚨 Troubleshooting

### **Common Issues**

#### **1. Import Errors**

```bash
# Error: No module named 'meli_crawler'
# Solution: Ensure you're in the project root directory
cd /path/to/meli-challenge
python -m unittest discover tests -v
```

#### **2. Missing Dependencies**

```bash
# Error: ModuleNotFoundError for scrapy, boto3, etc.
# Solution: Install test dependencies
pip install -r requirements.txt
# or
uv pip install -e .
```

#### **3. Test Discovery Issues**

```bash
# Error: No tests found
# Solution: Check test file naming
# Test files must start with 'test_'
# Test classes must start with 'Test'
# Test methods must start with 'test_'
```

#### **4. Environment Variable Issues**

```bash
# Error: Missing AWS credentials
# Solution: Tests use mock AWS services by default
# Check test_config.py for configuration
```

### **Debug Commands**

```bash
# Run single test with verbose output
python -m unittest tests.test_spiders.TestMeliUySpider.test_spider_initialization -v

# Run tests with debug output
python tests/run_tests.py --verbosity 2

# Check test discovery
python tests/run_tests.py --list

# Run tests with specific pattern
python tests/run_tests.py --pattern TestMeliUySpider
```

### **Test Configuration**

```python
# Check test configuration
from tests.test_config import TEST_CONFIG, TEST_ENV_VARS
print(TEST_CONFIG)
print(TEST_ENV_VARS)

# Setup test environment
from tests.test_config import setup_test_environment
setup_test_environment()
```

## 📚 Additional Resources

- **Python unittest documentation**: https://docs.python.org/3/library/unittest.html
- **Scrapy testing guide**: https://docs.scrapy.org/en/latest/topics/testing.html
- **Mock documentation**: https://docs.python.org/3/library/unittest.mock.html
- **Test coverage**: https://coverage.readthedocs.io/

## 🤝 Contributing to Tests

When adding new functionality:

1. **Write tests first** (TDD approach)
2. **Test both success and failure cases**
3. **Use descriptive test names**
4. **Follow existing test patterns**
5. **Update this documentation**

Your test suite is now ready to ensure code quality and reliability! 🎉
