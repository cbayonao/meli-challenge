# 🚀 Quick Start Guide

Get your Meli Challenge project up and running in minutes! This guide covers the fastest path to a working web scraping system.

## ⚡ 5-Minute Setup

### **Prerequisites Check**
```bash
# Check if you have the required software
python --version          # Should be 3.11+
pip --version            # pip should be available
git --version            # git should be available
aws --version            # AWS CLI should be installed
```

### **1. Clone and Setup**
```bash
# Clone the repository
git clone git@github.com:cbayonao/meli-challenge.git
cd meli-challenge

# Install Python dependencies
uv pip install -e .

# Copy environment template
cp env.example .env
```

### **2. Configure Environment**
Edit `.env` file with your credentials:
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# Service Configuration
DYNAMODB_TABLE_NAME=meli-products
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/your-queue-url
ZYTE_API_KEY=your_zyte_api_key_here

# Scrapy Configuration
SCRAPY_LOG_LEVEL=INFO
MAX_PAGES=5
MAX_ITEMS=100
```

### **3. Run Spiders**
```bash
# Run identification spider (discovers products)
scrapy crawl meli-uy-identify

# Run collection spider (extracts details)
scrapy crawl meli-uy-collect

# Check spider status
scrapy list
```

### **4. Verify Installation**
```bash
# Check if spiders are available
scrapy list

# Should show:
# meli-uy-identify
# meli-uy-collect
```



## 🕷️ Running Spiders

### **Quick Spider Test**
```bash
# Run identification spider (discovers products)
scrapy crawl meli-uy-identify

# Run collection spider (extracts details)
scrapy crawl meli-uy-collect
```

### **Spider with Limits**
```bash
# Run with custom limits (for testing)
scrapy crawl meli-uy-identify \
  -a max_pages=2 \
  -a max_items=10

# Run collection spider with retry settings
scrapy crawl meli-uy-collect \
  -a max_batches=5 \
  -a max_messages_per_batch=3
```

## 🧪 Quick Testing

### **Run All Tests**
```bash
# Run complete test suite
make test

# Run specific test categories
make test-unit          # Unit tests only
make test-spiders       # Spider tests only
make test-pipelines     # Pipeline tests only
```

### **Test with Coverage**
```bash
# Run tests with coverage report
make test-coverage

# Generate detailed test report
make test-report
```

## 📊 Monitor Your System

### **Check Logs**
```bash
# View real-time logs
make logs

# View specific service logs
tail -f logs/scrapy.log

# View development logs
make dev-logs
```

### **Check Status**
```bash
# Check service status
make status

# Check running processes
ps aux | grep scrapy

# Check resource usage
top
```

## 🔧 Quick Configuration

### **Spider Settings**
```bash
# Environment variables for spider limits
export MAX_PAGES=10
export MAX_ITEMS=500
export MAX_BATCHES=50

# Run spider with new settings
docker-compose exec meli-crawler scrapy crawl meli-uy-identify
```

### **Pipeline Configuration**
```python
# In your spider file
custom_settings = {
    'ITEM_PIPELINES': {
        'meli_crawler.pipelines.ValidationPipeline': 100,
        'meli_crawler.pipelines.PriceNormalizationPipeline': 200,
        'meli_crawler.pipelines.SellerNormalizationPipeline': 500,
        'meli_crawler.pipelines.CreateSellerIdUrlIdPipeline': 600,
        'meli_crawler.pipelines.DynamoDBPipeline': 700,
        'meli_crawler.pipelines.SQSPipeline': 800,
    }
}
```

## 🚨 Common Issues & Quick Fixes

### **Issue: Import Errors**
```bash
# Solution: Install in development mode
uv pip install -e .

# Or activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### **Issue: AWS Credentials**
```bash
# Solution: Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```



### **Issue: Port Already in Use**
```bash
# Solution: Check what's using the port
lsof -i :8000

# Kill the process or change port
```

## 📈 Performance Tuning

### **Quick Performance Settings**
```bash
# Increase concurrency
export SCRAPY_CONCURRENT_REQUESTS=32

# Reduce delays
export SCRAPY_DOWNLOAD_DELAY=0.5

# Enable caching
export SCRAPY_HTTPCACHE_ENABLED=True
```

### **Resource Limits**
```bash
# In serverless.yml
functions:
  function-name:
    memorySize: 2048
    timeout: 900
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## 🔍 Debug Mode

### **Enable Debug Logging**
```bash
# Set debug level
export SCRAPY_LOG_LEVEL=DEBUG

# Run spider with debug output
scrapy crawl meli-uy-identify -L DEBUG
```

### **Debug Specific Component**
```bash
# Test specific pipeline
python -c "
from meli_crawler.pipelines import ValidationPipeline
pipeline = ValidationPipeline()
result = pipeline.process_item({'title': 'test', 'pub_url': 'https://example.com'}, None)
print(result)
"
```

## 🚀 Next Steps

### **After Quick Start**
1. **Review Architecture**: Read `ARCHITECTURE.md` for system design
2. **Explore Tests**: Run `make test` to understand functionality
3. **Customize Settings**: Modify `.env` for your environment
4. **Scale Up**: Increase limits and concurrency settings
5. **Deploy to AWS**: Use `deploy.sh` for cloud deployment

### **Advanced Features**
- **Custom Pipelines**: Add your own data processing logic
- **New Spiders**: Create spiders for other websites
- **Monitoring**: Set up CloudWatch dashboards
- **CI/CD**: Configure GitHub Actions for automation

## 📚 Quick Reference

### **Essential Files**
```
.env                    # Environment configuration
serverless.yml          # Serverless configuration
Makefile               # Build commands
tests/                 # Test suite
meli_crawler/          # Main application
```

### **Key Commands**
```bash
make up                # Start services
make test              # Run tests
make logs              # View logs
make status            # Check status
make down              # Stop services
```

### **Environment Variables**
```bash
AWS_ACCESS_KEY_ID      # AWS access key
AWS_SECRET_ACCESS_KEY  # AWS secret key
DYNAMODB_TABLE_NAME   # DynamoDB table
SQS_QUEUE_URL         # SQS queue URL
ZYTE_API_KEY          # Zyte API key
```

---

**🎉 You're all set!** Your Meli Challenge web scraping system is now running and ready to extract data from MercadoLibre Uruguay.

For detailed information, check out:
- **`README.md`** - Complete project documentation
- **`ARCHITECTURE.md`** - System architecture details
- **`tests/README.md`** - Testing guide
