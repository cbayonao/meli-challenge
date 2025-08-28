# 🐳 Docker Setup for Meli Challenge

This document explains how to run your Scrapy project in Docker containers.

## 📋 Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Make (optional, for using Makefile commands)

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with your actual values
nano .env
```

### 2. Create Directories

```bash
mkdir -p logs data
```

### 3. Build and Run

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# Check logs
docker-compose logs -f meli-crawler
```

## 🛠️ Using Makefile (Recommended)

The project includes a `Makefile` with common commands:

```bash
# Show all available commands
make help

# Setup environment and directories
make setup-env
make setup-dirs

# Build and run
make build
make up

# View logs
make logs

# Run specific spiders
make run-collect
make run-identify
make run-spider SPIDER=meli-uy-collect

# Development mode
make dev-up
make dev-logs
make dev-shell

# Production mode
make prod-up
make prod-logs

# Clean up
make down
make clean
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# DynamoDB Configuration
DYNAMODB_REGION=us-east-1
DYNAMODB_TABLE_NAME=your_dynamodb_table_name

# SQS Configuration
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/your-queue-name
SQS_REGION=us-east-1

# Zyte API Configuration
ZYTE_API_KEY=your_zyte_api_key_here

# Scrapy Configuration
SCRAPY_LOG_LEVEL=INFO
SCRAPY_CONCURRENT_REQUESTS=16
SCRAPY_DOWNLOAD_DELAY=1

# Spider Limits
MAX_PAGES=20
MAX_ITEMS=2000
MAX_BATCHES=100
MAX_MESSAGES_PER_BATCH=10
MAX_RETRIES=3
```

### Spider Limits

You can control spider behavior through environment variables:

- `MAX_PAGES`: Maximum pages to scrape (default: 20)
- `MAX_ITEMS`: Maximum items to collect (default: 2000)
- `MAX_BATCHES`: Maximum SQS message batches (default: 100)
- `MAX_MESSAGES_PER_BATCH`: Messages per batch (default: 10)
- `MAX_RETRIES`: Retry attempts for failed requests (default: 3)

## 🐛 Development vs Production

### Development Mode

Uses `docker-compose.override.yml` for development-specific settings:

```bash
# Development mode
make dev-up
make dev-logs
make dev-shell

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

**Development Features:**
- Source code mounted for live editing
- Debug logging enabled
- Lower concurrency limits
- Faster restart cycles

### Production Mode

Uses standard `docker-compose.yml`:

```bash
# Production mode
make prod-up
make prod-logs

# Or manually
docker-compose up -d
```

**Production Features:**
- Optimized performance settings
- Persistent logging
- Health checks
- Auto-restart policies

## 📁 Directory Structure

```
meli-challenge/
├── Dockerfile                 # Docker image definition
├── docker-compose.yml         # Production configuration
├── docker-compose.override.yml # Development overrides
├── .dockerignore             # Files to exclude from Docker build
├── env.example               # Environment variables template
├── Makefile                  # Common commands
├── logs/                     # Persistent log storage
├── data/                     # CSV export storage
└── meli_crawler/            # Scrapy project
```

## 🔍 Monitoring and Debugging

### View Logs

```bash
# Follow logs in real-time
make logs

# View specific service logs
docker-compose logs meli-crawler

# View logs with timestamps
docker-compose logs -t meli-crawler
```

### Container Shell Access

```bash
# Access running container
make shell

# Or manually
docker-compose exec meli-crawler /bin/bash
```

### Health Checks

The container includes health checks:

```bash
# Check container health
docker-compose ps

# View health status
docker inspect meli-crawler | grep Health -A 10
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
make test

# Or manually
docker-compose run --rm meli-crawler python -m pytest
```

### Test Individual Spiders

```bash
# Test collect spider
make run-collect

# Test identify spider
make run-identify

# Test with custom parameters
make run-spider SPIDER=meli-uy-collect
```

## 🚨 Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Fix file permissions
   chmod +x run_spiders.py
   ```

2. **Environment Variables Not Loaded**
   ```bash
   # Check .env file exists
   ls -la .env
   
   # Verify environment in container
   make shell
   env | grep AWS
   ```

3. **Container Won't Start**
   ```bash
   # Check logs
   make logs
   
   # Check container status
   make status
   
   # Restart container
   make restart
   ```

4. **Build Failures**
   ```bash
   # Clean and rebuild
   make clean
   make build
   ```

### Debug Commands

```bash
# Check Docker system
docker system df
docker system prune -f

# Check container resources
docker stats meli-crawler

# Inspect container
docker inspect meli-crawler

# Check container logs
docker logs meli-crawler
```

## 🔄 Updates and Maintenance

### Update Dependencies

```bash
# Rebuild with updated dependencies
make clean
make build
```

### Update Configuration

```bash
# Reload configuration
make restart
```

### Backup Data

```bash
# Backup logs and data
tar -czf backup-$(date +%Y%m%d).tar.gz logs/ data/
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Scrapy Documentation](https://docs.scrapy.org/)
- [AWS Boto3 Documentation](https://boto3.amazonaws.com/)

## 🤝 Support

If you encounter issues:

1. Check the logs: `make logs`
2. Verify environment variables: `make shell` then `env`
3. Check container health: `make status`
4. Review this documentation
5. Check the main project README: `SPIDER_USAGE.md`
