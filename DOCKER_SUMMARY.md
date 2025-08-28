# 🐳 Docker Setup Summary

## 📁 Files Created

Your Scrapy project now has a complete Docker setup with the following files:

### **Core Docker Files**
- **`Dockerfile`** - Multi-stage Docker image definition
- **`docker-compose.yml`** - Production container configuration
- **`docker-compose.override.yml`** - Development overrides
- **`.dockerignore`** - Files to exclude from Docker build

### **Configuration Files**
- **`env.example`** - Environment variables template
- **`Makefile`** - Common Docker commands and shortcuts

### **Scripts and Tools**
- **`setup-docker.sh`** - Automated setup script
- **`healthcheck.py`** - Container health verification

### **Documentation**
- **`DOCKER_README.md`** - Comprehensive Docker usage guide

## 🚀 Quick Start Commands

```bash
# 1. Setup everything automatically
./setup-docker.sh

# 2. Or setup manually
cp env.example .env
mkdir -p logs data
nano .env  # Edit with your actual values

# 3. Build and run
make build
make up

# 4. View logs
make logs

# 5. Run spiders
make run-collect
make run-identify
```

## 🔧 Key Features

### **Multi-Environment Support**
- **Development**: Uses override file for live code editing
- **Production**: Optimized settings with health checks

### **Environment Variables**
- AWS credentials and regions
- DynamoDB table configuration
- SQS queue settings
- Zyte API key
- Spider limits and Scrapy settings

### **Volume Mounts**
- `./logs` → `/app/logs` (persistent logging)
- `./data` → `/app/data` (CSV exports)
- `./meli_crawler/config` → `/app/meli_crawler/config` (read-only config)

### **Health Monitoring**
- Automatic health checks every 30 seconds
- Python package verification
- Environment variable validation
- Project structure verification

## 📊 Makefile Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make build` | Build Docker image |
| `make up` | Start container |
| `make down` | Stop container |
| `make logs` | View logs |
| `make shell` | Access container shell |
| `make run-collect` | Run collect spider |
| `make run-identify` | Run identify spider |
| `make dev-up` | Start in development mode |
| `make prod-up` | Start in production mode |
| `make clean` | Clean up everything |

## 🌍 Environment Variables

### **Required Variables**
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
DYNAMODB_TABLE_NAME=your_table
SQS_QUEUE_URL=your_queue_url
ZYTE_API_KEY=your_zyte_key
```

### **Optional Variables (with defaults)**
```bash
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_REGION=us-east-1
SQS_REGION=us-east-1
SCRAPY_LOG_LEVEL=INFO
MAX_PAGES=20
MAX_ITEMS=2000
MAX_BATCHES=100
MAX_MESSAGES_PER_BATCH=10
MAX_RETRIES=3
```

## 🔍 Monitoring and Debugging

### **View Logs**
```bash
# Follow logs in real-time
make logs

# View specific service
docker-compose logs meli-crawler

# View with timestamps
docker-compose logs -t meli-crawler
```

### **Container Health**
```bash
# Check status
make status

# View health details
docker inspect meli-crawler | grep Health -A 10

# Run health check manually
docker-compose exec meli-crawler python healthcheck.py
```

### **Access Container**
```bash
# Open shell
make shell

# Run commands
docker-compose exec meli-crawler scrapy crawl meli-uy-collect
```

## 🧪 Testing

### **Test Individual Spiders**
```bash
# Test collect spider
make run-collect

# Test identify spider
make run-identify

# Test with custom parameters
make run-spider SPIDER=meli-uy-collect
```

### **Run Tests**
```bash
# Run all tests
make test

# Run specific test file
docker-compose run --rm meli-crawler python -m pytest tests/
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Container won't start**
   ```bash
   make logs          # Check logs
   make status        # Check status
   make restart       # Restart container
   ```

2. **Build failures**
   ```bash
   make clean         # Clean everything
   make build         # Rebuild
   ```

3. **Environment issues**
   ```bash
   make shell         # Access container
   env | grep AWS     # Check variables
   ```

4. **Permission issues**
   ```bash
   chmod +x run_spiders.py
   chmod +x setup-docker.sh
   ```

### **Debug Commands**
```bash
# Check Docker system
docker system df
docker system prune -f

# Check container resources
docker stats meli-crawler

# Inspect container
docker inspect meli-crawler
```

## 🔄 Development Workflow

### **Development Mode**
```bash
# Start with live code editing
make dev-up
make dev-logs

# Make changes to code
# Changes are immediately available in container

# Restart if needed
make dev-down
make dev-up
```

### **Production Mode**
```bash
# Start production container
make prod-up
make prod-logs

# Monitor health
make status
```

## 📚 Next Steps

1. **Configure Environment**: Edit `.env` with your actual values
2. **Test Setup**: Run `./setup-docker.sh` to verify everything works
3. **Start Container**: Use `make up` to start the container
4. **Run Spiders**: Test with `make run-collect` or `make run-identify`
5. **Monitor**: Use `make logs` to watch the process
6. **Customize**: Adjust environment variables and spider limits as needed

## 🤝 Support

- **Documentation**: `DOCKER_README.md` for detailed usage
- **Health Checks**: `healthcheck.py` for troubleshooting
- **Makefile**: `make help` for all available commands
- **Setup Script**: `./setup-docker.sh` for automated setup

Your Scrapy project is now fully containerized and ready for both development and production use! 🎉
