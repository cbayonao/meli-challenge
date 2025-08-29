# 🚀 Meli Challenge - Scrapy Web Scraping Project

A comprehensive web scraping solution for MercadoLibre Uruguay using Scrapy, AWS services, and modern DevOps practices.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

Meli Challenge is a production-ready web scraping system designed to extract product information from MercadoLibre Uruguay. The project implements a two-stage scraping architecture:

1. **Identification Stage**: Discovers and catalogs product listings
2. **Collection Stage**: Extracts detailed product information using Zyte API

The system integrates with AWS services (DynamoDB, SQS) for data storage and message queuing, with comprehensive testing and **Serverless Framework deployment**.

## 🏗️ Architecture

### **System Architecture Diagram**

```mermaid
graph TB
    subgraph "Web Sources"
        ML[mercadolibre.com.uy]
        ML_ART[articulo.mercadolibre.com.uy]
        ML_LIST[listado.mercadolibre.com.uy]
    end

    subgraph "Scrapy Spiders"
        ID[Identification Spider<br/>meli-uy-identify]
        COL[Collection Spider<br/>meli-uy-collect]
    end

    subgraph "Data Processing"
        VAL[Validation Pipeline]
        PRICE[Price Normalization]
        SELLER[Seller Normalization]
        ID_GEN[ID Generation]
        COLLECT[Collect Update Pipeline]
    end

    subgraph "AWS Services"
        SQS[(SQS Queue)]
        DDB[(DynamoDB Table)]
        SEC[Secrets Manager]
    end

    subgraph "External APIs"
        ZYTE[Zyte API]
    end

    subgraph "Infrastructure"
        LAMBDA[Lambda Functions]
        VPC[VPC + Subnets]
        ALB[Application Load Balancer]
        CW[CloudWatch]
    end

    ML --> ID
    ML_ART --> COL
    ML_LIST --> ID
    
    ID --> VAL
    VAL --> PRICE
    PRICE --> SELLER
    SELLER --> ID_GEN
    ID_GEN --> DDB
    ID_GEN --> SQS
    
    SQS --> COL
    COL --> ZYTE
    ZYTE --> COL
    COL --> COLLECT
    COLLECT --> DDB
    
    SEC --> LAMBDA
    LAMBDA --> VPC
    LAMBDA --> API
    LAMBDA --> CW
```

### **Data Flow Architecture**

```mermaid
sequenceDiagram
    participant ID as Identification Spider
    participant VAL as Validation Pipeline
    participant PRICE as Price Pipeline
    participant SELLER as Seller Pipeline
    participant ID_GEN as ID Generation
    participant DDB as DynamoDB
    participant SQS as SQS Queue
    participant COL as Collection Spider
    participant ZYTE as Zyte API
    participant COLLECT as Collect Pipeline

    ID->>VAL: Raw product data
    VAL->>PRICE: Validated data
    PRICE->>SELLER: Normalized prices
    SELLER->>ID_GEN: Clean seller names
    ID_GEN->>DDB: Store with IDs
    ID_GEN->>SQS: Send message
    
    SQS->>COL: Consume message
    COL->>ZYTE: Request product details
    ZYTE->>COL: Return detailed data
    COL->>COLLECT: Process product data
    COLLECT->>DDB: Update existing record
```

### **Pipeline Architecture**

```mermaid
graph LR
    subgraph "Input"
        RAW[Raw Item]
    end

    subgraph "Processing Pipelines"
        VAL[Validation<br/>Priority: 100]
        PRICE[Price Normalization<br/>Priority: 200]
        DISCOUNT[Discount Calculation<br/>Priority: 300]
        REVIEWS[Reviews Normalization<br/>Priority: 400]
        SELLER[Seller Normalization<br/>Priority: 500]
        ID_GEN[ID Generation<br/>Priority: 600]
        DDB[DynamoDB Storage<br/>Priority: 700]
        SQS[SQS Messaging<br/>Priority: 800]
        COLLECT[Collect Update<br/>Priority: 950]
    end

    subgraph "Output"
        FINAL[Final Item]
    end

    RAW --> VAL
    VAL --> PRICE
    PRICE --> DISCOUNT
    DISCOUNT --> REVIEWS
    REVIEWS --> SELLER
    SELLER --> ID_GEN
    ID_GEN --> DDB
    ID_GEN --> SQS
    SQS --> COLLECT
    COLLECT --> FINAL
```

## ✨ Features

### **Core Functionality**
- 🔍 **Dual-Stage Scraping**: Identification + Collection phases
- 📊 **Data Validation**: Comprehensive field validation and cleaning
- 💰 **Price Normalization**: Uruguayan price format handling
- 👤 **Seller Normalization**: Clean seller name processing
- 🆔 **ID Generation**: Base64 seller IDs + SHA256 URL hashes
- 🔄 **Retry Logic**: Automatic retry for failed requests
- 📝 **Logging**: Comprehensive logging and monitoring

### **AWS Integration**
- 🗄️ **DynamoDB**: Primary data storage with optimized schemas
- 📨 **SQS**: Message queuing for asynchronous processing
- 🔐 **Secrets Manager**: Secure credential management
- ☁️ **AWS Lambda**: Serverless function execution
- 📊 **CloudWatch**: Monitoring and alerting

### **Advanced Features**
- 🌐 **Zyte API Integration**: Browser emulation and JavaScript rendering
- 🚀 **Serverless Framework**: Modern deployment and infrastructure management
- 🧪 **Comprehensive Testing**: Unit, integration, and performance tests
- 🚀 **CI/CD Pipeline**: Automated testing and deployment
- 📈 **Auto-scaling**: Lambda concurrency and DynamoDB auto-scaling
- 🔒 **Security**: IAM roles, VPC isolation, HTTPS endpoints

## 📋 Prerequisites

### **Required Software**
- **Python 3.11+**
- **Python & Scrapy**
- **AWS CLI** (for deployment)
- **Serverless Framework** (for infrastructure)
- **uv** (Python package manager)

### **Required AWS Services**
- **AWS Account** with appropriate permissions
- **DynamoDB Table** for data storage
- **SQS Queue** for message processing
- **Lambda Functions** for serverless execution
- **Secrets Manager** for credentials

### **Required API Keys**
- **Zyte API Key** for web scraping
- **AWS Access Keys** for service integration

## 🚀 Quick Start

### **1. Clone and Setup**

```bash
# Clone the repository
git clone git@github.com:cbayonao/meli-challenge.git
cd meli-challenge

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.example .env
# Edit .env with your credentials
```

### **2. Run Spiders Locally**

```bash
# Run identification spider
scrapy crawl meli-uy-identify

# Run collection spider
scrapy crawl meli-uy-collect

# Run with custom settings
scrapy crawl meli-uy-identify -s LOG_LEVEL=INFO
scrapy crawl meli-uy-collect -s MAX_BATCHES=5
```

### **3. Deploy to AWS (Serverless)**

```bash
# Setup Serverless Framework
make serverless-setup

# Deploy to development
make serverless-deploy

# Deploy to production
make serverless-deploy-prod
```

### **3. Run Locally**

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run identification spider
scrapy crawl meli-uy-identify

# Run collection spider
scrapy crawl meli-uy-collect
```

## 📁 Project Structure

```
meli-challenge/
├── 📁 meli_crawler/              # Main Scrapy project
│   ├── 📁 spiders/               # Spider definitions
│   │   ├── meli_uy_identify.py  # Product identification spider
│   │   └── meli_uy_collect.py   # Product collection spider
│   ├── 📁 pipelines/             # Data processing pipelines
│   ├── 📁 middlewares/           # Request/response middleware
│   ├── 📁 utils/                 # Utility functions
│   └── settings.py               # Scrapy configuration
├── 📁 tests/                     # Comprehensive test suite
│   ├── test_spiders.py           # Spider unit tests
│   ├── test_pipelines.py         # Pipeline unit tests
│   ├── test_integration.py       # Integration tests
│   └── test_utils.py             # Test utilities
├── 📁 handlers/                  # Lambda function handlers
│   ├── identification.py         # Identification spider handler
│   ├── collection.py             # Collection spider handler
│   ├── validation.py             # Data validation handler
│   └── monitoring.py             # Health monitoring handler

├── 📁 .github/                   # GitHub Actions CI/CD
├── 📋 Makefile                   # Build automation
├── 🚀 deploy-serverless.sh        # Serverless deployment script
├── 📋 serverless.yml              # Serverless configuration
├── 📋 serverless.dev.yml          # Development configuration
├── 📋 serverless.prod.yml         # Production configuration
├── 📦 package.json                # Node.js dependencies
└── 📖 README.md                  # This file
```

## ⚙️ Configuration

### **Environment Variables**

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1

# DynamoDB Configuration
DYNAMODB_TABLE_NAME=meli-products

# SQS Configuration
SQS_QUEUE_URL=https://sqs.region.amazonaws.com/queue-url

# Zyte API Configuration
ZYTE_API_KEY=your_zyte_api_key

# Scrapy Configuration
SCRAPY_LOG_LEVEL=INFO
SCRAPY_CONCURRENT_REQUESTS=16
SCRAPY_DOWNLOAD_DELAY=1
```

### **Spider Configuration**

#### **Identification Spider (`meli-uy-identify`)**
```python
class MeliUyIdentifySpider(scrapy.Spider):
    name = 'meli-uy-identify'
    max_pages = 20          # Maximum pages to scrape
    max_items = 2000        # Maximum items to process
    allowed_domains = ['mercadolibre.com.uy']
    
    custom_settings = {
        'ITEM_PIPELINES': {
            'meli_crawler.pipelines.ValidationPipeline': 100,
            'meli_crawler.pipelines.PriceNormalizationPipeline': 200,
            # ... more pipelines
        }
    }
```

#### **Collection Spider (`meli-uy-collect`)**
```python
class MeliUyCollectSpider(scrapy.Spider):
    name = 'meli-uy-collect'
    max_batches = 100              # Maximum SQS batches
    max_messages_per_batch = 10    # Messages per batch
    max_retries = 3                # Retry attempts
    
    custom_settings = {
        'ADDONS': {
            'scrapy_zyte_api.Addon': None
        },
        'ZYTE_API_TRANSPARENT_MODE': True,
        'ZYTE_API_BROWSER_HEADERS': True
    }
```

## 💻 Usage Examples

### **Running Spiders**

#### **Basic Spider Execution**
```bash
# Run identification spider
scrapy crawl meli-uy-identify

# Run collection spider
scrapy crawl meli-uy-collect

# Run with custom settings
scrapy crawl meli-uy-identify -s MAX_PAGES=10 -s MAX_ITEMS=500
```

#### **Spider with Parameters**
```bash
# Run with custom limits
scrapy crawl meli-uy-identify \
  -a max_pages=5 \
  -a max_items=100 \
  -s LOG_LEVEL=DEBUG

# Run collection spider with retry settings
scrapy crawl meli-uy-collect \
  -a max_batches=50 \
  -a max_messages_per_batch=5 \
  -a max_retries=5
```



### **Makefile Commands**

```bash
# Development and testing
make test          # Run all tests
make test-unit     # Run unit tests only
make test-coverage # Run tests with coverage
make test-report   # Generate test report

# Validation system
make validation-setup    # Setup AI validation system
make validation-test     # Test AI provider connection
make validation-run      # Run validation on sample data
make validation-report   # Generate validation report

# Utilities
make setup-dirs    # Create necessary directories
make setup-env     # Setup environment from template
make clean         # Clean build artifacts
make deploy        # Deploy to AWS

# Testing
make test          # Run all tests
make test-unit     # Run unit tests only
make test-coverage # Run tests with coverage
make test-report   # Generate test report

# Deployment
make deploy        # Deploy to AWS
make clean         # Clean build artifacts
```

### **Pipeline Usage**

#### **Custom Pipeline Configuration**
```python
# In your spider
custom_settings = {
    'ITEM_PIPELINES': {
        'meli_crawler.pipelines.ValidationPipeline': 100,
        'meli_crawler.pipelines.CustomPipeline': 150,
        'meli_crawler.pipelines.DynamoDBPipeline': 700,
    }
}
```

#### **Pipeline Data Flow**
```python
# Raw item from spider
raw_item = {
    'title': '  Test Product  ',
    'pub_url': 'https://mercadolibre.com.uy/product/123',
    'seller': 'Por Test Seller',
    'price': '1.234,56'
}

# After validation pipeline
validated_item = {
    'title': '  Test Product  ',
    'pub_url': 'https://mercadolibre.com.uy/product/123',
    'seller': 'Por Test Seller',
    'price': '1.234,56'
}

# After price normalization
price_normalized_item = {
    'title': '  Test Product  ',
    'pub_url': 'https://mercadolibre.com.uy/product/123',
    'seller': 'Por Test Seller',
    'price': 1234.56,
    'currency': 'UYU'
}

# After seller normalization
seller_normalized_item = {
    'title': '  Test Product  ',
    'pub_url': 'https://mercadolibre.com.uy/product/123',
    'seller': 'Test Seller',
    'price': 1234.56,
    'currency': 'UYU'
}

# After ID generation
final_item = {
    'title': '  Test Product  ',
    'pub_url': 'https://mercadolibre.com.uy/product/123',
    'seller': 'Test Seller',
    'price': 1234.56,
    'currency': 'UYU',
    'seller_id': 'VGVzdCBTZWxsZXI=',  # Base64 encoded
    'url_id': 'a1b2c3d4...'          # SHA256 hash
}
```

## 🧪 Testing

### **Running Tests**

```bash
# Run all tests
make test

# Run specific test categories
make test-unit          # Unit tests
make test-spiders       # Spider tests
make test-pipelines     # Pipeline tests
make test-integration   # Integration tests

# Run with coverage
make test-coverage

# Generate test report
make test-report

# List all tests
make test-list
```

### **Test Structure**

```
tests/
├── test_spiders.py      # Spider unit tests
├── test_pipelines.py    # Pipeline unit tests
├── test_integration.py  # Integration tests
├── test_utils.py        # Test utilities
├── test_config.py       # Test configuration
└── run_tests.py         # Test runner
```

### **Example Test**

```python
def test_seller_normalization(self):
    """Test seller name normalization"""
    item = {'seller': 'Por Test Seller'}
    result = self.pipeline.process_item(item, self.spider)
    self.assertEqual(result['seller'], 'Test Seller')

def test_price_normalization(self):
    """Test price format conversion"""
    item = {'price': '1.234,56'}
    result = self.pipeline.process_item(item, self.spider)
    self.assertEqual(result['price'], 1234.56)
```

## 🚀 Deployment

### **AWS Deployment**

#### **1. Infrastructure Setup**
```bash
# Setup Serverless Framework
make serverless-setup

# Deploy to development
make serverless-deploy

# Deploy to production
make serverless-deploy-prod
```

#### **2. Application Deployment**
```bash
# Deploy with Serverless Framework
./deploy-serverless.sh deploy staging

# Check deployment status
npx serverless info --stage staging
```

#### **3. CI/CD Pipeline**
The project includes GitHub Actions workflows for:
- **Automated Testing**: Unit tests, integration tests, security scans
- **Multi-Platform Builds**: Cross-platform compatibility
- **AWS Deployment**: Automatic deployment to staging/production
- **Monitoring**: Post-deployment health checks

### **Deployment Options**

#### **Production Deployment**
```yaml
version: '3.8'
services:
  meli-crawler:
    build: .
    environment:
      - SCRAPY_LOG_LEVEL=INFO
      - MAX_PAGES=50
      - MAX_ITEMS=5000
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### **Health Check**
```python
# healthcheck.py
import sys
import importlib

def check_dependencies():
    required_modules = ['scrapy', 'boto3', 'decouple']
    for module in required_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            return False
    return True

if __name__ == '__main__':
    if check_dependencies():
        sys.exit(0)
    else:
        sys.exit(1)
```

## 📊 Monitoring

### **CloudWatch Metrics**

- **Lambda Metrics**: Invocations, errors, duration, throttles
- **Application Metrics**: Request count, error rate, latency
- **Custom Metrics**: Items processed, pipeline success rate

### **Logging**

```python
# Spider logging
self.logger.info(f"Processing URL: {url}")
self.logger.warning(f"Retry attempt {retry_count} for {url}")
self.logger.error(f"Failed to process {url}: {error}")

# Pipeline logging
self.logger.info(f"Processing item: {item.get('title', 'Unknown')}")
self.logger.debug(f"Pipeline result: {result}")
```

### **Health Checks**

```bash
# Check Lambda function health
npx serverless logs -f function-name --tail

# Check DynamoDB table status
aws dynamodb describe-table \
  --table-name meli-products

# Check SQS queue status
aws sqs get-queue-attributes \
  --queue-url $SQS_QUEUE_URL \
  --attribute-names All
```

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Import Errors**
```bash
# Error: No module named 'meli_crawler'
# Solution: Install in development mode
uv pip install -e .
```

#### **2. AWS Credentials**
```bash
# Error: Unable to locate credentials
# Solution: Configure AWS CLI
aws configure
# or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

#### **3. DynamoDB Errors**
```bash
# Error: Parameter validation failed
# Solution: Check data types in pipelines
# Ensure proper DynamoDB format conversion
```

#### **4. SQS Message Processing**
```bash
# Error: Messages not being consumed
# Solution: Check queue permissions
# Verify message format and structure
```

### **Debug Commands**

```bash
# Check spider status
scrapy list

# Run spider with debug output
scrapy crawl meli-uy-identify -L DEBUG

# Check pipeline processing
scrapy crawl meli-uy-identify -s LOG_LEVEL=DEBUG

# Test specific pipeline
python -c "
from meli_crawler.pipelines import ValidationPipeline
pipeline = ValidationPipeline()
print(pipeline.process_item({'title': 'test'}, None))
"
```

### **Performance Tuning**

```bash
# Increase concurrency
scrapy crawl meli-uy-identify -s CONCURRENT_REQUESTS=32

# Reduce download delay
scrapy crawl meli-uy-identify -s DOWNLOAD_DELAY=0.5

# Enable caching
scrapy crawl meli-uy-identify -s HTTPCACHE_ENABLED=True
```

## 🤝 Contributing

### **Development Workflow**

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** for new functionality
5. **Run tests**: `make test`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Create a Pull Request**

### **Code Standards**

- **Python**: Follow PEP 8 style guide
- **Tests**: Maintain >90% code coverage
- **Documentation**: Update README and docstrings
- **Commits**: Use conventional commit messages

### **Testing Requirements**

```bash
# All tests must pass
make test

# Code coverage must be >90%
make test-coverage

# No linting errors
flake8 meli_crawler/
black --check meli_crawler/
```

## 📚 Additional Resources

### **Documentation**
- [Scrapy Documentation](https://docs.scrapy.org/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)


### **Related Projects**
- [Scrapy-Zyte-API](https://github.com/scrapy-plugins/scrapy-zyte-api)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Python Decouple](https://github.com/henriquebastos/python-decouple)

### **Community**
- [Scrapy Community](https://scrapy.org/community/)
- [AWS Developer Community](https://aws.amazon.com/developer/)
- [Serverless Community](https://www.serverless.com/community/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Scrapy Team** for the excellent web scraping framework
- **AWS** for cloud infrastructure services
- **Zyte** for the powerful web scraping API
- **Open Source Community** for various tools and libraries

---

**Happy Scraping! 🕷️✨**

For questions and support, please open an issue in the repository or contact the development team.
