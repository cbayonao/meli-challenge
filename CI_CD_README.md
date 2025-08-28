# 🚀 CI/CD Pipeline & Deployment Guide

This document explains the complete CI/CD pipeline setup for your Meli Challenge Scrapy project, including automated testing, building, and deployment to AWS ECS.

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
- **Docker Image Building**: Multi-platform image builds with caching
- **Infrastructure as Code**: Terraform-managed AWS resources
- **Multi-Environment Deployment**: Staging and production environments
- **Auto-scaling**: ECS service auto-scaling based on CPU/memory
- **Health Monitoring**: Automated health checks and rollbacks
- **Security**: Secrets management and vulnerability scanning

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│  GitHub Actions  │───▶│   AWS ECS      │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │   Code      │ │    │ │   Test       │ │    │ │   Cluster   │ │
│ │   Changes   │ │    │ │   Build      │ │    │ │   Service   │ │
│ └─────────────┘ │    │ │   Deploy     │ │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Container      │    │   AWS Services  │
                       │   Registry       │    │                 │
                       │   (GHCR)        │    │ ┌─────────────┐ │
                       └──────────────────┘    │ │ DynamoDB    │ │
                                               │ │ SQS         │ │
                                               │ │ CloudWatch  │ │
                                               │ │ Secrets     │ │
                                               │ └─────────────┘ │
                                               └─────────────────┘
```

## 🔧 Prerequisites

### **Required Tools**
- Docker & Docker Compose
- AWS CLI (configured with appropriate credentials)
- Terraform (for infrastructure deployment)
- Python 3.11+

### **AWS Setup**
- AWS Account with appropriate permissions
- IAM roles for ECS execution and task
- S3 bucket for Terraform state
- Secrets Manager for sensitive data

### **GitHub Setup**
- GitHub repository with Actions enabled
- GitHub Container Registry access
- Repository secrets configured

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
        default: 'staging'
        type: choice
        options:
        - staging
        - production
```

### **Pipeline Stages**

#### **1. Test & Lint**
- Python 3.11 setup
- Dependency installation with `uv`
- Code linting (flake8, black, isort)
- Unit tests with pytest
- Coverage reporting

#### **2. Security Scan**
- Trivy vulnerability scanning
- SARIF report upload to GitHub Security tab
- Dependency vulnerability checks

#### **3. Build**
- Docker Buildx setup
- Multi-platform builds (linux/amd64, linux/arm64)
- GitHub Container Registry push
- Build caching for performance

#### **4. Deploy Staging**
- Automatic deployment on `develop` branch
- AWS ECS service update
- Service stability verification

#### **5. Deploy Production**
- Automatic deployment on `main` branch
- Release-triggered deployments
- Production environment protection

#### **6. Post-Deployment Tests**
- Health check verification
- Service status monitoring
- Deployment success notification

## 🏗️ AWS Infrastructure

### **Terraform Modules**

#### **VPC Module**
- Custom VPC with public/private subnets
- NAT gateways for private subnet internet access
- Route tables and security groups

#### **ECS Module**
- Fargate cluster with auto-scaling
- Service definitions with health checks
- CloudWatch logging and monitoring

#### **DynamoDB Module**
- DynamoDB table with auto-scaling
- Backup and encryption enabled
- Point-in-time recovery

#### **SQS Module**
- Standard SQS queue
- Dead letter queue for failed messages
- CloudWatch alarms for monitoring

#### **IAM Module**
- ECS execution role
- ECS task role
- Least privilege permissions

#### **Secrets Module**
- AWS credentials storage
- Application secrets management
- Automatic rotation support

### **Infrastructure Configuration**

#### **Staging Environment**
```hcl
environment = "staging"
cpu         = 512
memory      = 1024
desired_count = 1
max_count   = 2
```

#### **Production Environment**
```hcl
environment = "production"
cpu         = 1024
memory      = 2048
desired_count = 2
max_count   = 5
```

## 🚀 Deployment Process

### **Automated Deployment**

#### **Staging (develop branch)**
1. Code push to `develop` branch
2. GitHub Actions workflow triggers
3. Tests run and pass
4. Docker image built and pushed
5. ECS service updated automatically
6. Health checks verify deployment

#### **Production (main branch)**
1. Code merged to `main` branch
2. GitHub Actions workflow triggers
3. All tests must pass
4. Docker image built and pushed
5. ECS service updated automatically
6. Health checks verify deployment
7. Success notification sent

### **Manual Deployment**

#### **Using GitHub Actions**
1. Go to Actions tab in repository
2. Select "CI/CD Pipeline" workflow
3. Click "Run workflow"
4. Choose environment (staging/production)
5. Click "Run workflow"

#### **Using Deployment Script**
```bash
# Deploy to staging
./deploy.sh -e staging

# Deploy to production
./deploy.sh -e production

# Deploy with custom region
./deploy.sh -e production -r eu-west-1

# Skip tests (use with caution)
./deploy.sh -e production -s

# Force deployment even if tests fail
./deploy.sh -e production -f
```

## 📊 Monitoring & Troubleshooting

### **CloudWatch Monitoring**

#### **ECS Metrics**
- CPU utilization
- Memory utilization
- Network metrics
- Task count

#### **Application Metrics**
- Custom business metrics
- Error rates
- Response times
- Throughput

#### **Alarms**
- High CPU/memory usage
- Service health issues
- Error rate thresholds
- Auto-scaling triggers

### **Logging**

#### **ECS Logs**
- Application logs in CloudWatch
- Structured logging with JSON
- Log retention policies
- Log filtering and search

#### **GitHub Actions Logs**
- Workflow execution logs
- Step-by-step debugging
- Artifact downloads
- Re-run failed jobs

### **Troubleshooting**

#### **Common Issues**

1. **Deployment Failures**
   ```bash
   # Check ECS service status
   aws ecs describe-services \
     --cluster meli-crawler-cluster-staging \
     --services meli-crawler-staging
   
   # Check task logs
   aws logs tail /ecs/meli-crawler-staging
   ```

2. **Infrastructure Issues**
   ```bash
   # Check Terraform state
   cd infrastructure
   terraform plan
   terraform state list
   
   # Check AWS resources
   aws ecs list-clusters
   aws ecs list-services --cluster meli-crawler-cluster-staging
   ```

3. **GitHub Actions Issues**
   - Check workflow logs in Actions tab
   - Verify repository secrets
   - Check branch protection rules
   - Verify GitHub token permissions

#### **Debug Commands**

```bash
# Check ECS cluster status
aws ecs describe-clusters --clusters meli-crawler-cluster-staging

# Check service events
aws ecs describe-services \
  --cluster meli-crawler-cluster-staging \
  --services meli-crawler-staging \
  --query 'services[0].events'

# Check running tasks
aws ecs list-tasks --cluster meli-crawler-cluster-staging

# Check task definition
aws ecs describe-task-definition \
  --task-definition meli-crawler-staging
```

## 🔒 Security & Best Practices

### **Security Measures**

#### **Secrets Management**
- AWS Secrets Manager for sensitive data
- No hardcoded credentials
- Automatic secret rotation
- Least privilege access

#### **Network Security**
- Private subnets for ECS tasks
- Security groups with minimal access
- VPC endpoints for AWS services
- No public internet access for tasks

#### **Container Security**
- Base image vulnerability scanning
- Runtime security monitoring
- Resource limits and constraints
- Health check verification

### **Best Practices**

#### **Code Quality**
- Automated linting and formatting
- Unit test coverage requirements
- Code review requirements
- Branch protection rules

#### **Infrastructure**
- Infrastructure as Code (Terraform)
- Environment separation
- Resource tagging
- Cost monitoring

#### **Deployment**
- Blue-green deployments
- Rollback capabilities
- Health check verification
- Gradual rollout

## 📚 Configuration Files

### **Required Files**

1. **`.github/workflows/ci-cd.yml`** - GitHub Actions workflow
2. **`.aws/task-definition-*.json`** - ECS task definitions
3. **`infrastructure/`** - Terraform configurations
4. **`deploy.sh`** - Deployment script
5. **`Dockerfile`** - Container definition
6. **`docker-compose.yml`** - Local development

### **Environment Variables**

#### **GitHub Secrets**
```bash
AWS_ACCESS_KEY_ID_STAGING
AWS_SECRET_ACCESS_KEY_STAGING
AWS_REGION_STAGING
AWS_ACCESS_KEY_ID_PROD
AWS_SECRET_ACCESS_KEY_PROD
AWS_REGION_PROD
```

#### **Application Secrets**
```bash
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
DYNAMODB_TABLE_NAME
SQS_QUEUE_URL
ZYTE_API_KEY
```

## 🎯 Next Steps

1. **Setup GitHub Secrets**: Configure AWS credentials and other secrets
2. **Configure AWS**: Set up IAM roles and permissions
3. **Test Pipeline**: Push to develop branch to test staging deployment
4. **Production Setup**: Configure production environment and secrets
5. **Monitoring**: Set up CloudWatch dashboards and alarms
6. **Documentation**: Update team documentation and runbooks

## 🤝 Support

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check this guide and related docs
- **Team**: Contact your DevOps/Infrastructure team

Your CI/CD pipeline is now ready for automated, secure, and reliable deployments! 🎉
