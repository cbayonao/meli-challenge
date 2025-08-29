# 🚀 **Meli Challenge - Serverless Framework Deployment**

## 📋 **Overview**

This project use **Serverless Framework** for AWS deployment. The Serverless Framework provides a more streamlined approach to deploying serverless applications with better developer experience and faster deployments.

## 🏗️ **Architecture Changes**

### **After (Serverless Framework)**
- **AWS Lambda** functions running Scrapy spiders
- **API Gateway** for HTTP endpoints
- **SQS** for message queuing and processing
- **DynamoDB** for data storage
- **CloudWatch** for monitoring and logging

## 🚀 **Quick Start**

### **1. Prerequisites**
```bash
# Install Node.js 18+
node --version

# Install npm
npm --version

# Install AWS CLI
aws --version

# Install Python 3.11+
python3 --version
```

### **2. Setup Serverless Framework**
```bash
# Install dependencies
make serverless-setup

# Or manually
npm install
```

### **3. Configure Environment**
```bash
# Copy environment template
cp env.example .env

# Edit with your credentials
nano .env
```

### **4. Deploy to Development**
```bash
# Deploy to dev stage
make serverless-deploy

# Or manually
./deploy-serverless.sh deploy
```

## 📁 **Project Structure**

```
meli-challenge/
├── 📁 handlers/                    # Lambda function handlers
│   ├── __init__.py
│   ├── identification.py           # Identification spider handler
│   ├── collection.py               # Collection spider handler
│   ├── validation.py               # Data validation handler
│   └── monitoring.py               # Health monitoring handler
├── 📁 meli_crawler/                # Scrapy project
├── 📁 validation/                  # AI validation system
├── 📁 tests/                       # Test suite
├── serverless.yml                  # Main Serverless configuration
├── serverless.dev.yml              # Development stage config
├── serverless.prod.yml             # Production stage config
├── package.json                    # Node.js dependencies
├── requirements.txt                # Python dependencies
├── deploy-serverless.sh            # Deployment script
└── Makefile                        # Build automation
```

## ⚙️ **Configuration Files**

### **Main Configuration (`serverless.yml`)**
- **Provider settings**: AWS region, runtime, memory, timeout
- **Functions**: Lambda function definitions and triggers
- **Resources**: DynamoDB tables, SQS queues, CloudWatch logs
- **IAM roles**: Permissions for AWS services
- **Plugins**: Python requirements, environment variables

### **Development Stage (`serverless.dev.yml`)**
- **Reduced resources**: Lower memory and timeout limits
- **Debug logging**: Detailed logging for development
- **Limited processing**: Smaller batch sizes and limits
- **Disabled features**: Scheduled scraping and monitoring off

### **Production Stage (`serverless.prod.yml`)**
- **Full resources**: Higher memory and timeout limits
- **Production logging**: Info level logging
- **Full processing**: Larger batch sizes and limits
- **Enabled features**: Scheduled scraping and monitoring on
- **Auto-scaling**: DynamoDB and Lambda concurrency limits
- **CloudWatch alarms**: Error rate and queue depth monitoring

## 🔧 **Deployment Commands**

### **Using Makefile**
```bash
# Setup Serverless Framework
make serverless-setup

# Deploy to development
make serverless-deploy

# Deploy to production
make serverless-deploy-prod

# Remove deployment
make serverless-remove

# Show deployment info
make serverless-info

# Show function logs
make serverless-logs
```

### **Using Script Directly**
```bash
# Deploy to development
./deploy-serverless.sh deploy

# Deploy to staging
./deploy-serverless.sh deploy staging

# Deploy to production
./deploy-serverless.sh deploy prod us-west-2

# Remove development stage
./deploy-serverless.sh remove dev

# Show deployment information
./deploy-serverless.sh info prod

# Show function logs
./deploy-serverless.sh logs dev
```

## 🕷️ **Lambda Functions**

### **1. Identification Spider (`identification-spider`)**
- **Purpose**: Discovers products from MercadoLibre
- **Triggers**: 
  - **HTTP API**: POST `/scrape/identify`
  - **Scheduled**: Every 6 hours (configurable)
- **Input**: Spider parameters (max_pages, max_items)
- **Output**: Product URLs sent to SQS queue

### **2. Collection Spider (`collection-spider`)**
- **Purpose**: Extracts detailed product information
- **Triggers**: **SQS messages** from identification spider
- **Input**: SQS messages with product URLs
- **Output**: Product data stored in DynamoDB

### **3. Data Validator (`data-validator`)**
- **Purpose**: Validates scraped data using AI
- **Triggers**: **SQS messages** with data to validate
- **Input**: SQS messages with product data
- **Output**: Validation reports and recommendations

### **4. Monitoring (`monitoring`)**
- **Purpose**: Health checks and alerting
- **Triggers**: **Scheduled** every 5 minutes
- **Input**: None (scheduled event)
- **Output**: Health status and alerts

## 🔄 **Data Flow**

```
1. Identification Spider (Lambda)
   ↓ (Discovers products)
2. SQS Queue (Product URLs)
   ↓ (Triggers collection)
3. Collection Spider (Lambda)
   ↓ (Extracts data)
4. DynamoDB (Product storage)
   ↓ (Data validation)
5. Validation Queue (SQS)
   ↓ (AI validation)
6. Data Validator (Lambda)
   ↓ (Validation reports)
7. CloudWatch (Logs & metrics)
```

## 📊 **Monitoring & Observability**

### **CloudWatch Metrics**
- **Lambda**: Invocations, errors, duration, throttles
- **DynamoDB**: Read/write capacity, throttled requests
- **SQS**: Queue depth, message age, errors
- **API Gateway**: Request count, latency, errors

### **CloudWatch Logs**
- **Function logs**: Detailed execution logs
- **Structured logging**: JSON formatted logs
- **Log retention**: 30 days (configurable)

### **CloudWatch Alarms**
- **High error rate**: Lambda function errors
- **Queue depth**: SQS message accumulation
- **DynamoDB throttling**: Capacity issues

## 🔐 **Security & IAM**

### **IAM Roles**
- **Lambda execution role**: Basic Lambda permissions
- **DynamoDB access**: Read/write to products table
- **SQS access**: Send/receive messages
- **CloudWatch access**: Logs and metrics
- **Secrets Manager**: API key access

### **Environment Variables**
- **Sensitive data**: Stored in AWS Secrets Manager
- **Configuration**: Environment-specific settings
- **API keys**: Zyte, OpenAI

## 💰 **Cost Optimization**

### **Development Stage**
- **Lambda**: 512MB memory, 2-minute timeout
- **DynamoDB**: Pay-per-request billing
- **SQS**: Standard queue (no FIFO)
- **Logs**: 7-day retention

### **Production Stage**
- **Lambda**: 2GB memory, 10-minute timeout
- **DynamoDB**: Provisioned capacity with auto-scaling
- **SQS**: Standard queue with dead-letter queue
- **Logs**: 30-day retention

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Lambda Timeout**
```bash
# Check function logs
make serverless-logs

# Increase timeout in serverless.yml
timeout: 900  # 15 minutes
```

#### **2. Memory Issues**
```bash
# Increase memory allocation
memorySize: 2048  # 2GB

# Check memory usage in CloudWatch
```

#### **3. SQS Queue Depth**
```bash
# Check queue attributes
aws sqs get-queue-attributes \
  --queue-url $QUEUE_URL \
  --attribute-names All

# Increase Lambda concurrency
reservedConcurrency: 20
```

#### **4. DynamoDB Throttling**
```bash
# Check table metrics
aws dynamodb describe-table \
  --table-name $TABLE_NAME

# Enable auto-scaling or increase capacity
```

### **Debug Commands**
```bash
# Local testing
npx serverless invoke local -f identification-spider

# Function logs
npx serverless logs -f identification-spider --tail

# Deployment info
npx serverless info --stage dev

# Package without deploy
npx serverless package
```

## 🔄 **Migration from Terraform**

### **What Changed**
1. **Infrastructure**: ECS → Lambda + API Gateway
2. **Deployment**: Terraform → Serverless Framework
3. **Containers**: Docker → Serverless functions
4. **Scaling**: Manual → Auto-scaling
5. **Monitoring**: Basic → CloudWatch + alarms

### **Benefits**
- **Faster deployments**: Minutes instead of hours
- **Better developer experience**: YAML configuration
- **Auto-scaling**: Built-in scaling policies
- **Cost optimization**: Pay-per-use pricing
- **Easier maintenance**: Less infrastructure code

### **Migration Steps**
1. **Backup Terraform state**: `terraform state pull > backup.tfstate`
2. **Deploy Serverless**: `./deploy-serverless.sh deploy`
3. **Verify functionality**: Test all endpoints and functions
4. **Migrate data**: Copy data from old to new DynamoDB
5. **Update DNS**: Point to new API Gateway endpoints
6. **Remove Terraform**: `terraform destroy`

## 📚 **Additional Resources**

- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/python-programming-model.html)
- [Serverless Python Requirements Plugin](https://github.com/UnitedIncome/serverless-python-requirements)
- [AWS DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AWS SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/)

## 🤝 **Support**

For issues or questions about the Serverless Framework deployment:

1. **Check logs**: `make serverless-logs`
2. **Review configuration**: Check `serverless.yml` files
3. **Verify AWS credentials**: `aws sts get-caller-identity`
4. **Check CloudWatch**: Monitor metrics and alarms
5. **Review documentation**: This README and Serverless docs
