#!/bin/bash

# Docker Setup Script for Meli Challenge
# This script sets up the Docker environment for the Scrapy project

set -e

echo "🐳 Setting up Docker environment for Meli Challenge..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are available"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p logs data
    
    print_success "Directories created: logs/, data/"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        if [ -f env.example ]; then
            cp env.example .env
            print_success "Created .env file from env.example"
            print_warning "Please edit .env with your actual values before running the container"
        else
            print_error "env.example file not found. Please create a .env file manually."
            exit 1
        fi
    else
        print_warning ".env file already exists. Skipping creation."
    fi
}

# Check if .env has been configured
check_env_configuration() {
    print_status "Checking environment configuration..."
    
    if [ -f .env ]; then
        # Check if .env contains placeholder values
        if grep -q "your_aws_access_key_here" .env; then
            print_warning ".env file contains placeholder values. Please configure it before running."
            echo ""
            echo "Required configuration:"
            echo "  - AWS_ACCESS_KEY_ID"
            echo "  - AWS_SECRET_ACCESS_KEY"
            echo "  - DYNAMODB_TABLE_NAME"
            echo "  - SQS_QUEUE_URL"
            echo "  - ZYTE_API_KEY"
            echo ""
        else
            print_success ".env file appears to be configured"
        fi
    fi
}

# Build Docker image
build_image() {
    print_status "Building Docker image..."
    
    if docker-compose build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    echo "🎉 Docker environment setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your actual values:"
    echo "   nano .env"
    echo ""
    echo "2. Start the container:"
    echo "   make up"
    echo "   # or"
    echo "   docker-compose up -d"
    echo ""
    echo "3. View logs:"
    echo "   make logs"
    echo "   # or"
    echo "   docker-compose logs -f meli-crawler"
    echo ""
    echo "4. Run specific spiders:"
    echo "   make run-collect"
    echo "   make run-identify"
    echo ""
    echo "5. Access container shell:"
    echo "   make shell"
    echo ""
    echo "For more commands, run: make help"
    echo ""
    echo "📚 Documentation: DOCKER_README.md"
}

# Main execution
main() {
    echo "🚀 Starting Docker setup..."
    echo ""
    
    check_docker
    create_directories
    setup_environment
    check_env_configuration
    build_image
    show_next_steps
}

# Run main function
main "$@"
