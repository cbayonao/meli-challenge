# 🚀 CI/CD Pipeline & Deployment Guide - Serverless

This document explains the complete CI/CD pipeline setup for your Meli Challenge Scrapy project, including automated testing, building, and deployment to AWS using Serverless Framework.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [GitHub Actions Workflow](#github-actions-workflow)
- [AWS Infrastructure](#aws-infrastructure)
- [Deployment Process](#deployment-process)
- [Monitoring & Troubleshooting](#monitoring--troubleshooting)
- [Security & Best Practices](#security--best-practices)

## 🎯 Overview

The CI/CD pipeline provides:

- **Automated Testing**: Linting, unit tests, and security scanning
- **Serverless Deployment**: AWS Lambda functions with auto-scaling
- **Infrastructure as Code**: Serverless Framework managed AWS resources
- **Multi-Environment Deployment**: Development, staging, and production environments
- **Auto-scaling**: Lambda concurrency and DynamoDB auto-scaling
- **Health Monitoring**: Automated health checks and CloudWatch alarms
- **Security**: Secrets management and vulnerability scanning

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  GitHub Actions  │───▶│   AWS Lambda    │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   Code      │ │    │ │   Test       │ │    │ │   Functions │ │
│ │   Changes   │ │    │ │   Build      │ │    │ │   API       │ │
│ └─────────────┘ │    │ │   Deploy     │ │    │ │   Gateway   │ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Serverless     │    │   AWS Services  │
                       │   Framework      │    │                 │
                       │   (Local)        │    │ ┌─────────────┐ │
                       └──────────────────┘    │ │ DynamoDB    │ │
                                               │ │ SQS         │ │
                                               │ │ CloudWatch  │ │
                                               │ │ Secrets     │ │
                                               │ └─────────────┘ │
                                               └─────────────────┘
```

## 🔧 Prerequisites

### **Required Tools**
- Node.js 18+ and npm
- AWS CLI (configured with appropriate credentials)
- Serverless Framework (for infrastructure deployment)
- Python 3.11+

### **AWS Setup**
- AWS Account with appropriate permissions
- IAM roles for Lambda execution
- DynamoDB tables and SQS queues
- Secrets Manager for sensitive data

### **GitHub Setup**
- GitHub repository with Actions enabled
- Repository secrets configured for AWS credentials
- Environment protection rules (optional)

## 🔄 GitHub Actions Workflow

### **Workflow Triggers**
```yaml
on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  release:
    types: [ published ]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'dev'
        type: choice
        options:
        - dev
        - staging
        - prod
```

### **Pipeline Stages**

#### **1. Test & Lint**
- Python 3.11 setup
- Dependency installation with pip
- Code linting (flake8, black, isort)
- Unit tests with pytest and coverage

#### **2. Security Scan**
- Trivy vulnerability scanner
- Code security analysis
- SARIF report upload to GitHub Security

#### **3. Serverless Setup**
- Node.js 18+ setup
- Serverless Framework installation
- Dependency verification

#### **4. Deployment**
- **Development**: Deploy to dev stage (develop branch)
- **Staging**: Deploy to staging stage (main branch)
- **Production**: Deploy to prod stage (main branch + releases)

#### **5. Post-Deployment**
- Health checks and validation
- Success/failure notifications
- Cleanup on deployment failure

## 🚀 AWS Infrastructure

### **Serverless Resources**

#### **Lambda Functions**
- **identification-spider**: Discovers products from MercadoLibre
- **collection-spider**: Extracts detailed product information
- **data-validator**: Validates scraped data using AI
- **monitoring**: Health checks and alerting

#### **AWS Services**
- **DynamoDB**: Product data storage with auto-scaling
- **SQS**: Message queuing for processing
- **API Gateway**: HTTP endpoints for spiders
- **CloudWatch**: Monitoring, logging, and alarms
- **Secrets Manager**: API keys and sensitive data

### **Configuration Files**
- **`serverless.yml`**: Main configuration
- **`serverless.dev.yml`**: Development stage settings
- **`serverless.prod.yml`**: Production stage settings

## 🔧 Deployment Process

### **Local Development**
```bash
# Setup Serverless Framework
make serverless-setup

# Deploy to development
make serverless-deploy

# Deploy to production
make serverless-deploy-prod

# Remove deployment
make serverless-remove
```

### **CI/CD Deployment**
```bash
# Automated deployment via GitHub Actions
# Development: develop branch → dev stage
# Staging: main branch → staging stage
# Production: main branch + release → prod stage
```

### **Environment Variables**
```bash
# Required secrets in GitHub
AWS_ACCESS_KEY_ID_DEV
AWS_SECRET_ACCESS_KEY_DEV
AWS_REGION_DEV
AWS_ACCESS_KEY_ID_STAGING
AWS_SECRET_ACCESS_KEY_STAGING
AWS_REGION_STAGING
AWS_ACCESS_KEY_ID_PROD
AWS_SECRET_ACCESS_KEY_PROD
AWS_REGION_PROD

# API Keys
ZYTE_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

## 📊 Monitoring & Troubleshooting

### **CloudWatch Monitoring**
- **Lambda Metrics**: Invocations, errors, duration, throttles
- **DynamoDB Metrics**: Read/write capacity, throttled requests
- **SQS Metrics**: Queue depth, message age, errors
- **API Gateway Metrics**: Request count, latency, errors

### **CloudWatch Alarms**
- **High Error Rate**: Lambda function errors
- **Queue Depth**: SQS message accumulation
- **DynamoDB Throttling**: Capacity issues

### **Logs and Debugging**
```bash
# View function logs
make serverless-logs

# Get deployment info
make serverless-info

# Local testing
npx serverless invoke local -f function-name
```

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

## 🔐 Security & Best Practices

### **IAM Roles and Permissions**
- **Least privilege principle**: Only necessary permissions
- **Resource-based policies**: Specific resource access
- **Cross-account access**: Secure multi-account setup

### **Secrets Management**
- **AWS Secrets Manager**: Centralized secret storage
- **Environment variables**: Secure configuration
- **API key rotation**: Regular key updates

### **Network Security**
- **VPC configuration**: Private subnets for Lambda
- **Security groups**: Restrictive access rules
- **WAF integration**: Web application firewall

### **Code Security**
- **Dependency scanning**: Regular vulnerability checks
- **Code signing**: Verify code integrity
- **Access control**: Repository permissions

## 📈 Performance Optimization

### **Lambda Optimization**
- **Memory allocation**: Right-size for performance
- **Concurrency limits**: Control resource usage
- **Cold start reduction**: Keep functions warm

### **DynamoDB Optimization**
- **Auto-scaling**: Automatic capacity management
- **Indexing strategy**: Efficient query patterns
- **Batch operations**: Reduce API calls

### **SQS Optimization**
- **Batch processing**: Process multiple messages
- **Dead letter queues**: Handle failed messages
- **Visibility timeout**: Prevent duplicate processing

## 🔄 Rollback and Recovery

### **Deployment Rollback**
```bash
# Remove current deployment
make serverless-remove

# Deploy previous version
git checkout <previous-commit>
make serverless-deploy
```

### **Data Recovery**
- **DynamoDB backups**: Point-in-time recovery
- **SQS message retention**: Configurable retention periods
- **CloudWatch logs**: Historical data access

### **Disaster Recovery**
- **Multi-region deployment**: Geographic redundancy
- **Cross-region replication**: Data synchronization
- **Backup strategies**: Regular backup schedules

## 📚 Additional Resources

- [Serverless Framework Documentation](https://www.serverless.com/framework/docs/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)

## 🤝 Support and Troubleshooting

### **Getting Help**
1. **Check logs**: `make serverless-logs`
2. **Review configuration**: Check `serverless.yml` files
3. **Verify AWS credentials**: `aws sts get-caller-identity`
4. **Check CloudWatch**: Monitor metrics and alarms
5. **Review documentation**: This README and Serverless docs

### **Common Commands**
```bash
# Development
make serverless-setup
make serverless-deploy
make serverless-info

# Production
make serverless-deploy-prod
make serverless-remove

# Troubleshooting
make serverless-logs
npx serverless info --stage prod
npx serverless logs -f function-name --tail
```
