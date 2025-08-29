# 🧠 AI Validation System for Meli Challenge

A comprehensive Generative AI-powered data validation system that ensures the quality, completeness, and consistency of scraped data from MercadoLibre Uruguay.

## 🎯 Overview

The AI Validation System provides autonomous validation of scraped product data using both rule-based validation and Generative AI models. It ensures:

- **Data Completeness**: No empty fields in essential records
- **Data Consistency**: Verification of calculated discounts and price relationships
- **Format Validation**: Valid URL and image formats
- **Outlier Detection**: Identification of inconsistent values and suspicious data
- **AI-Powered Analysis**: Intelligent validation using multiple AI providers

## 🏗️ Architecture

### **System Components**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scrapy Item  │───▶│ Validation       │───▶│ Validation      │
│                 │    │ Pipeline         │    │ Report          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   AI Validator   │
                       │                  │
                       │ • Rule-based     │
                       │ • AI-powered     │
                       │ • Batch          │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────────────┐
                       │  AI Providers            │
                       │                          │
                       │ • OpenAI gpt-3.5-turbo   │
                       └──────────────────────────┘
```

### **Validation Flow**

1. **Item Processing**: Scrapy items enter the validation pipeline
2. **Rule Validation**: Basic validation rules are applied (field presence, format, ranges)
3. **AI Validation**: Generative AI analyzes data quality and consistency
4. **Result Generation**: Comprehensive validation report with recommendations
5. **Report Storage**: Validation results saved in multiple formats (JSON, CSV, HTML)

## 🚀 Quick Start

### **1. Installation**

```bash
# Install validation system dependencies
pip install -r validation/requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key"
```

### **2. Basic Usage**

```python
from validation.ai_validator import AIValidator

# Initialize validator
validator = AIValidator(
    api_key="your_api_key",
    model="gpt-3.5-turbo"
)

# Validate a single item
item = {
    "title": "Test Product",
    "pub_url": "https://mercadolibre.com.uy/test",
    "seller": "Test Seller",
    "price": 100.0
}

# Async validation
import asyncio
report = asyncio.run(validator.validate_item(item))

# Sync validation (convenience function)
from validation.ai_validator import validate_item_sync
report = validate_item_sync(item)
```

### **3. Integration with Scrapy**

```python
# In your spider's custom_settings
custom_settings = {
    'ITEM_PIPELINES': {
        'validation.validation_pipeline.ValidationPipeline': 100,
        # ... other pipelines
    },
    'VALIDATION_ENABLE_AI': True,
    'VALIDATION_AI_MODEL': 'gpt-3.5-turbo',
    'VALIDATION_BATCH_SIZE': 10,
    'VALIDATION_SAVE_REPORTS': True
}
```

## 🔧 Configuration

### **Environment Variables**

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Validation Settings
VALIDATION_ENVIRONMENT=development
VALIDATION_ENABLE_AI=true
VALIDATION_BATCH_SIZE=10
VALIDATION_LOG_LEVEL=INFO
VALIDATION_OUTPUT_DIR=validation_reports
```

### **Configuration File**

```json
{
  "rules": {
    "required_fields": ["title", "pub_url", "seller", "price"],
    "price_ranges": {
      "min_price": 0.01,
      "max_price": 1000000.0,
      "currency_required": true
    }
  },
  "ai_providers": {
    "openai": {
      "default_model": "gpt-3.5-turbo",
      "max_tokens": 2000,
      "temperature": 0.1
    }
  },
  "pipeline": {
    "enable_ai_validation": true,
    "batch_size": 10,
    "save_reports": true
  }
}
```

## 📊 Validation Rules

### **Field Requirements**

- **Required Fields**: `title`, `pub_url`, `seller`, `price`
- **Optional Fields**: `original_price`, `currency`, `reviews_count`, `rating`, `availability`, `features`, `images`, `description`

### **Price Validation**

- **Range**: 0.01 to 1,000,000.0
- **Format**: Supports Uruguayan format (1.234,56)
- **Currency**: Defaults to UYU if missing
- **Consistency**: Verifies discount calculations

### **URL Validation**

- **Product URLs**: Must match MercadoLibre patterns
- **Image URLs**: Must be valid image formats
- **Domain Validation**: Ensures correct MercadoLibre domains

### **Data Consistency**

- **Discount Tolerance**: 1% tolerance for calculated vs. stored discounts
- **Price Relationships**: Original price must be >= current price
- **Seller Format**: Removes common prefixes ("Por ", "Vendedor: ")

## 🤖 AI Validation

### **Supported Providers**

| Provider | Model | Features | Cost |
|----------|-------|----------|------|
| **OpenAI** | GPT-4, GPT-3.5-turbo | High accuracy, fast | Medium |


### **AI Validation Process**

1. **Data Analysis**: AI analyzes scraped data for quality issues
2. **Pattern Recognition**: Identifies inconsistencies and outliers
3. **Business Logic**: Validates business rules and relationships
4. **Recommendations**: Provides actionable improvement suggestions

### **AI Prompt Example**

```
You are a data quality expert analyzing scraped product data from MercadoLibre Uruguay.

Please analyze the following product data and identify any quality issues, inconsistencies, or potential errors:

Product Data:
{
  "title": "Test Product",
  "pub_url": "https://mercadolibre.com.uy/test",
  "seller": "Por Test Seller",
  "price": 100.0
}

Focus on:
1. Data completeness and missing fields
2. Data consistency (e.g., price calculations, seller information)
3. Data format validity (URLs, images, prices)
4. Outliers or suspicious values
5. Business logic consistency

Be specific and provide actionable feedback.
```

## 📁 File Structure

```
validation/
├── __init__.py                 # Package initialization
├── ai_validator.py            # Core AI validation engine
├── validation_pipeline.py     # Scrapy pipeline integration
├── validation_cli.py          # Command-line interface
├── validation_config.py       # Configuration management
├── requirements.txt            # Dependencies
└── README.md                  # This file
```

## 🛠️ Usage Examples

### **1. Command Line Interface**

```bash
# Test AI provider connection
python validation_cli.py test --provider openai

# Validate a single file
python validation_cli.py validate-file data.json --provider openai --save-report

# Validate multiple files in batch
python validation_cli.py validate-batch data/ --batch-size 20

# Validate individual item
python validation_cli.py validate-item '{"title": "test"}'

# Generate summary report
python validation_cli.py generate-report validation_reports/ --output summary.html
```

### **2. Python API**

```python
from validation.ai_validator import AIValidator
import asyncio

async def validate_products():
    validator = AIValidator(
        api_key="your_key",
        model="gpt-3.5-turbo"
    )
    
    # Validate single item
    item = {"title": "Product", "price": 100}
    report = await validator.validate_item(item)
    
    # Validate batch
    items = [item1, item2, item3]
    reports = await validator.validate_batch(items)
    
    # Export reports
    json_report = validator.export_report(report, "json")
    csv_report = validator.export_report(report, "csv")

# Run validation
asyncio.run(validate_products())
```

### **3. Scrapy Pipeline Integration**

```python
# In your spider
class MySpider(scrapy.Spider):
    name = 'my_spider'
    
    custom_settings = {
        'ITEM_PIPELINES': {
            'validation.validation_pipeline.ValidationPipeline': 100,
            'meli_crawler.pipelines.DynamoDBPipeline': 200,
        },
        'VALIDATION_ENABLE_AI': True,
        'VALIDATION_SAVE_REPORTS': True
    }
    
    def parse(self, response):
        # Your parsing logic
        item = {
            'title': 'Product Title',
            'price': '1.234,56',
            'seller': 'Por Seller Name'
        }
        yield item
```

## 📊 Validation Reports

### **Report Structure**

```json
{
  "item_id": "product_123",
  "timestamp": "2024-01-01T00:00:00Z",
  "total_validations": 8,
  "passed_validations": 6,
  "failed_validations": 1,
  "warning_validations": 1,
  "overall_status": "warning",
  "summary": "Validation Summary: 6/8 passed, 1 failed, 1 warnings",
  "ai_analysis": "Data quality is generally good with minor issues...",
  "recommendations": [
    "Verify seller name format",
    "Check price consistency"
  ],
  "results": [
    {
      "field_name": "title",
      "status": "passed",
      "level": "info",
      "message": "Required field 'title' is present",
      "actual_value": "Product Title"
    }
  ]
}
```

### **Report Formats**

- **JSON**: Detailed structured data
- **CSV**: Tabular format for analysis
- **HTML**: Human-readable web report

## 🔍 Validation Examples

### **Example 1: Valid Product**

```json
{
  "title": "iPhone 15 Pro Max 256GB",
  "pub_url": "https://articulo.mercadolibre.com.uy/MLU-123456789-iphone-15-pro-max",
  "seller": "Apple Store Uruguay",
  "price": 1299.99,
  "currency": "USD",
  "original_price": 1499.99,
  "discount_percentage": 13.33
}
```

**Validation Result**: ✅ PASSED
- All required fields present
- Valid MercadoLibre URL
- Price within reasonable range
- Discount calculation correct (13.33%)

### **Example 2: Invalid Product**

```json
{
  "title": "",
  "pub_url": "https://example.com/product",
  "seller": "Por ",
  "price": -50.0
}
```

**Validation Result**: ❌ FAILED
- Missing title (required field)
- Invalid URL domain
- Empty seller name
- Negative price (invalid)

### **Example 3: Suspicious Product**

```json
{
  "title": "Product",
  "pub_url": "https://articulo.mercadolibre.com.uy/MLU-123",
  "seller": "Seller",
  "price": 999999.99,
  "original_price": 1000000.00
}
```

**Validation Result**: ⚠️ WARNING
- Generic title (too short)
- Price at maximum threshold
- Suspicious pricing pattern

## 🧪 Testing

### **Run Tests**

```bash
# Run all validation tests
python -m pytest validation/tests/ -v

# Run specific test categories
python -m pytest validation/tests/ -k "test_ai_validation" -v
python -m pytest validation/tests/ -k "test_rule_validation" -v

# Run with coverage
python -m pytest validation/tests/ --cov=validation --cov-report=html
```

### **Test Configuration**

```python
# test_config.py
import pytest
from validation.validation_config import TESTING_CONFIG

@pytest.fixture
def test_config():
    return TESTING_CONFIG

@pytest.fixture
def mock_ai_response():
    return {
        "validations": [
            {
                "field_name": "title",
                "issue_type": "missing",
                "severity": "high",
                "description": "Title field is empty",
                "suggestion": "Ensure title is provided"
            }
        ]
    }
```

## 📈 Performance & Scaling

### **Batch Processing**

- **Default Batch Size**: 10 items
- **Production Batch Size**: 50 items
- **Concurrent Validations**: 5-10 (configurable)

### **Performance Optimization**

```python
# Optimize for high throughput
validator = AIValidator(
    provider="openai",
    batch_size=100,
    max_retries=2
)

# Use batch validation for multiple items
reports = await validator.validate_batch(items)
```

### **Caching**

- **Result Caching**: Enabled by default
- **Cache TTL**: 1 hour (configurable)
- **Cache Key**: Item hash + validation rules

## 🔒 Security & Privacy

### **API Key Management**

- **Environment Variables**: Secure storage
- **AWS Secrets Manager**: Production deployment
- **Key Rotation**: Regular updates

### **Data Privacy**

- **No Data Storage**: Validation results only
- **Local Processing**: No external data transmission
- **Audit Logging**: Validation activity tracking

## 🚨 Troubleshooting

### **Common Issues**

#### **1. API Key Errors**

```bash
# Error: No API key found
export OPENAI_API_KEY="your_key_here"

# Error: Invalid API key
# Verify key in OpenAI dashboard
```

#### **2. Rate Limiting**

```python
# Reduce batch size
validator = AIValidator(batch_size=5)

# Add delays between batches
import asyncio
await asyncio.sleep(1)  # 1 second delay
```

#### **3. Validation Failures**

```python
# Check validation rules
from validation.validation_config import get_config
config = get_config('development')
print(config.rules.required_fields)

# Enable debug logging
import logging
logging.getLogger('validation').setLevel(logging.DEBUG)
```

### **Debug Mode**

```python
# Enable verbose logging
validator = AIValidator(
    provider="openai",
    log_level="DEBUG"
)

# Test with simple item
test_item = {"title": "test", "price": 100}
report = await validator.validate_item(test_item)
print(report.ai_analysis)
```

## 🔄 Integration Workflow

### **1. Development Setup**

```bash
# Clone repository
git clone <repo-url>
cd meli-challenge

# Install validation system
pip install -r validation/requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Test connection
python validation_cli.py test --provider openai
```

### **2. Spider Integration**

```python
# Add validation pipeline to spider
custom_settings = {
    'ITEM_PIPELINES': {
        'validation.validation_pipeline.ValidationPipeline': 100,
        'meli_crawler.pipelines.DynamoDBPipeline': 200,
    }
}

# Run spider with validation
scrapy crawl my_spider -s VALIDATION_ENABLE_AI=true
```

### **3. Production Deployment**

```bash
# Set production environment
export VALIDATION_ENVIRONMENT=production

# Use production configuration
python validation_cli.py validate-batch data/ --provider openai --batch-size 50

# Monitor validation results
python validation_cli.py generate-report validation_reports/ --output production_summary.html
```

## 📚 API Reference

### **AIValidator Class**

```python
class AIValidator:
    def __init__(self, 
                 provider: str = "openai",
                 api_key: Optional[str] = None,
                 model: str = "gpt-3.5-turbo",
                 batch_size: int = 10,
                 max_retries: int = 3)
    
    async def validate_item(self, item: Dict[str, Any]) -> ValidationReport
    async def validate_batch(self, items: List[Dict[str, Any]]) -> List[ValidationReport]
    def export_report(self, report: ValidationReport, format: str = "json") -> str
```

### **ValidationPipeline Class**

```python
class ValidationPipeline:
    def __init__(self, 
                 enable_ai_validation: bool = True,
                 ai_provider: str = "openai",
                 ai_model: str = "gpt-3.5-turbo",
                 batch_size: int = 10,
                 save_reports: bool = True)
    
    def process_item(self, item: Dict[str, Any], spider) -> Dict[str, Any]
```

### **ValidationReport Class**

```python
@dataclass
class ValidationReport:
    item_id: str
    timestamp: str
    total_validations: int
    passed_validations: int
    failed_validations: int
    warning_validations: int
    overall_status: ValidationStatus
    results: List[ValidationResult]
    summary: str
    ai_analysis: str
    recommendations: List[str]
```

## 🤝 Contributing

### **Development Setup**

```bash
# Install development dependencies
pip install -r validation/requirements.txt

# Run tests
python -m pytest validation/tests/ -v

# Code formatting
black validation/
flake8 validation/
mypy validation/
```

### **Adding New Validation Rules**

```python
# In validation_config.py
class ValidationRules:
    def __init__(self):
        self.new_validation_rule = {
            'min_value': 0,
            'max_value': 100,
            'pattern': r'^\d+$'
        }

# In ai_validator.py
def _validate_new_rule(self, item):
    # Implementation
    pass
```

### **Adding New AI Providers**

```python
# In ai_validator.py
def _init_ai_client(self):
    if self.provider == "new_provider":
        # Initialize new provider client
        self.client = NewProviderClient(api_key=self.api_key)
```

## 📞 Support

### **Getting Help**

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and feature requests in the repository
- **Discussions**: Use repository discussions for questions

### **Community**

- **Scrapy Community**: For Scrapy-related questions
- **AI Provider Docs**: For API-specific issues
- **Data Quality**: For validation methodology discussions

---

## 🎉 **Success Metrics**

The AI Validation System provides:

- **Data Quality Score**: Percentage of items passing validation
- **Issue Detection Rate**: Number of problems identified per batch
- **AI Accuracy**: Validation result confidence scores
- **Performance Metrics**: Processing time and throughput
- **Cost Analysis**: API usage and cost per validation

## 🚀 **Next Steps**

1. **Configure API Keys**: Set up your preferred AI provider
2. **Test Integration**: Validate sample data with the CLI
3. **Integrate with Spiders**: Add validation pipeline to your Scrapy spiders
4. **Monitor Results**: Review validation reports and improve data quality
5. **Scale Up**: Optimize batch sizes and concurrent processing for production

---

**Happy Validating! 🧠✨**

For questions and support, please refer to the documentation or open an issue in the repository.
