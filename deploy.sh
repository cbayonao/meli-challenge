#!/bin/bash

# Deployment Script for Meli Challenge
# This script manages deployments to staging and production environments

set -e

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

# Default values
ENVIRONMENT="staging"
REGION="us-east-1"
SKIP_TESTS=false
SKIP_BUILD=false
FORCE_DEPLOY=false

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Environment to deploy to (staging|production) [default: staging]"
    echo "  -r, --region REGION      AWS region [default: us-east-1]"
    echo "  -s, --skip-tests         Skip running tests before deployment"
    echo "  -b, --skip-build         Skip building Docker image"
    echo "  -f, --force              Force deployment even if tests fail"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy to staging"
    echo "  $0 -e production            # Deploy to production"
    echo "  $0 -e staging -s            # Deploy to staging, skip tests"
    echo "  $0 -e production -r eu-west-1  # Deploy to production in EU"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -b|--skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -f|--force)
            FORCE_DEPLOY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
    exit 1
fi

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_warning "Terraform is not installed. Infrastructure deployment will be skipped."
    fi
    
    print_success "Prerequisites check passed"
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        print_warning "Skipping tests"
        return 0
    fi
    
    print_status "Running tests..."
    
    if docker-compose run --rm meli-crawler python -m pytest; then
        print_success "Tests passed"
    else
        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            print_warning "Tests failed, but continuing due to --force flag"
        else
            print_error "Tests failed. Use --force to deploy anyway."
            exit 1
        fi
    fi
}

# Build Docker image
build_image() {
    if [[ "$SKIP_BUILD" == "true" ]]; then
        print_warning "Skipping Docker build"
        return 0
    fi
    
    print_status "Building Docker image..."
    
    if docker-compose build; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    if ! command -v terraform &> /dev/null; then
        print_warning "Terraform not available, skipping infrastructure deployment"
        return 0
    fi
    
    print_status "Deploying infrastructure for $ENVIRONMENT environment..."
    
    cd infrastructure
    
    # Initialize Terraform
    if ! terraform init; then
        print_error "Failed to initialize Terraform"
        exit 1
    fi
    
    # Plan deployment
    if ! terraform plan -var="environment=$ENVIRONMENT" -var="aws_region=$REGION" -out=tfplan; then
        print_error "Failed to create Terraform plan"
        exit 1
    fi
    
    # Apply changes
    if ! terraform apply tfplan; then
        print_error "Failed to apply Terraform changes"
        exit 1
    fi
    
    # Clean up plan file
    rm -f tfplan
    
    cd ..
    
    print_success "Infrastructure deployed successfully"
}

# Deploy application
deploy_application() {
    print_status "Deploying application to $ENVIRONMENT environment..."
    
    # Get the latest image tag
    IMAGE_TAG=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "meli-challenge" | head -1)
    
    if [[ -z "$IMAGE_TAG" ]]; then
        print_error "No Docker image found. Please build the image first."
        exit 1
    fi
    
    print_status "Using image: $IMAGE_TAG"
    
    # Update ECS service
    if aws ecs update-service \
        --cluster "meli-crawler-cluster-$ENVIRONMENT" \
        --service "meli-crawler-$ENVIRONMENT" \
        --force-new-deployment \
        --region "$REGION"; then
        
        print_success "ECS service updated successfully"
    else
        print_error "Failed to update ECS service"
        exit 1
    fi
    
    # Wait for service to stabilize
    print_status "Waiting for service to stabilize..."
    if aws ecs wait services-stable \
        --cluster "meli-crawler-cluster-$ENVIRONMENT" \
        --services "meli-crawler-$ENVIRONMENT" \
        --region "$REGION"; then
        
        print_success "Service is stable"
    else
        print_error "Service failed to stabilize"
        exit 1
    fi
}

# Run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Get service ARN
    SERVICE_ARN=$(aws ecs describe-services \
        --cluster "meli-crawler-cluster-$ENVIRONMENT" \
        --services "meli-crawler-$ENVIRONMENT" \
        --region "$REGION" \
        --query 'services[0].serviceArn' \
        --output text)
    
    if [[ "$SERVICE_ARN" == "None" ]]; then
        print_error "Failed to get service ARN"
        exit 1
    fi
    
    # Check service status
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster "meli-crawler-cluster-$ENVIRONMENT" \
        --services "meli-crawler-$ENVIRONMENT" \
        --region "$REGION" \
        --query 'services[0].status' \
        --output text)
    
    if [[ "$SERVICE_STATUS" == "ACTIVE" ]]; then
        print_success "Service is active and healthy"
    else
        print_error "Service is not healthy. Status: $SERVICE_STATUS"
        exit 1
    fi
    
    # Check running tasks
    RUNNING_TASKS=$(aws ecs describe-services \
        --cluster "meli-crawler-cluster-$ENVIRONMENT" \
        --services "meli-crawler-$ENVIRONMENT" \
        --region "$REGION" \
        --query 'services[0].runningCount' \
        --output text)
    
    print_success "Running tasks: $RUNNING_TASKS"
}

# Main deployment function
main() {
    print_status "Starting deployment to $ENVIRONMENT environment in $REGION region..."
    
    # Check prerequisites
    check_prerequisites
    
    # Run tests
    run_tests
    
    # Build image
    build_image
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Deploy application
    deploy_application
    
    # Run health checks
    run_health_checks
    
    print_success "🎉 Deployment to $ENVIRONMENT completed successfully!"
    
    # Show service information
    echo ""
    print_status "Service Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Region: $REGION"
    echo "  Cluster: meli-crawler-cluster-$ENVIRONMENT"
    echo "  Service: meli-crawler-$ENVIRONMENT"
    echo ""
    print_status "You can monitor the deployment with:"
    echo "  aws ecs describe-services --cluster meli-crawler-cluster-$ENVIRONMENT --services meli-crawler-$ENVIRONMENT --region $REGION"
}

# Run main function
main "$@"
