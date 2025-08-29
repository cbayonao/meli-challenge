#!/bin/bash

# Meli Challenge - Serverless Framework Deployment Script
# Replaces Terraform deployment with Serverless Framework

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="meli-challenge"
DEFAULT_STAGE="dev"
DEFAULT_REGION="us-east-1"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed. Please install npm first."
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install AWS CLI first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    log_success "All prerequisites are met!"
}

install_dependencies() {
    log_info "Installing Node.js dependencies..."
    
    if [ ! -d "node_modules" ]; then
        npm install
        log_success "Node.js dependencies installed!"
    else
        log_info "Node.js dependencies already installed, skipping..."
    fi
    
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    log_success "Python dependencies installed!"
}

check_aws_credentials() {
    log_info "Checking AWS credentials..."
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured or invalid."
        log_info "Please run 'aws configure' or set environment variables."
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    log_success "AWS credentials valid!"
    log_info "Account ID: $account_id"
    log_info "User ARN: $user_arn"
}

check_environment_file() {
    log_info "Checking environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            log_warning ".env file not found. Creating from template..."
            cp env.example .env
            log_warning "Please edit .env file with your credentials before continuing."
            read -p "Press Enter after editing .env file..."
        else
            log_error "No .env file or env.example template found."
            exit 1
        fi
    fi
    
    # Check required environment variables
    source .env
    
    local required_vars=(
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
        "AWS_DEFAULT_REGION"
        "ZYTE_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set in .env file."
            exit 1
        fi
    done
    
    log_success "Environment configuration is valid!"
}

deploy_stage() {
    local stage=$1
    local region=$2
    
    log_info "Deploying to stage: $stage in region: $region"
    
    # Set environment variables for deployment
    export STAGE=$stage
    export AWS_DEFAULT_REGION=$region
    
    # Deploy using Serverless Framework
    log_info "Running serverless deploy..."
    
    if npx serverless deploy --stage $stage --region $region --verbose; then
        log_success "Deployment to $stage completed successfully!"
        
        # Get deployment info
        log_info "Getting deployment information..."
        npx serverless info --stage $stage --region $region
        
    else
        log_error "Deployment to $stage failed!"
        exit 1
    fi
}

remove_stage() {
    local stage=$1
    local region=$2
    
    log_warning "Removing stage: $stage in region: $region"
    
    read -p "Are you sure you want to remove the $stage stage? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Removing $stage stage..."
        
        if npx serverless remove --stage $stage --region $region --verbose; then
            log_success "Removal of $stage stage completed successfully!"
        else
            log_error "Removal of $stage stage failed!"
            exit 1
        fi
    else
        log_info "Removal cancelled."
    fi
}

show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  deploy [STAGE] [REGION]  Deploy to specified stage and region"
    echo "  remove [STAGE] [REGION]  Remove specified stage and region"
    echo "  info [STAGE] [REGION]    Show deployment information"
    echo "  logs [STAGE] [REGION]    Show function logs"
    echo "  help                     Show this help message"
    echo ""
    echo "Options:"
    echo "  STAGE                    Deployment stage (dev, staging, prod) [default: $DEFAULT_STAGE]"
    echo "  REGION                   AWS region [default: $DEFAULT_REGION]"
    echo ""
    echo "Examples:"
    echo "  $0 deploy                    # Deploy to dev stage in default region"
    echo "  $0 deploy staging            # Deploy to staging stage in default region"
    echo "  $0 deploy prod us-west-2    # Deploy to prod stage in us-west-2"
    echo "  $0 remove dev               # Remove dev stage"
    echo "  $0 info prod                # Show prod stage information"
    echo "  $0 logs dev                 # Show dev stage logs"
}

main() {
    local command=${1:-"deploy"}
    local stage=${2:-$DEFAULT_STAGE}
    local region=${3:-$DEFAULT_REGION}
    
    log_info "Meli Challenge - Serverless Framework Deployment"
    log_info "Command: $command"
    log_info "Stage: $stage"
    log_info "Region: $region"
    echo ""
    
    case $command in
        "deploy")
            check_prerequisites
            install_dependencies
            check_aws_credentials
            check_environment_file
            deploy_stage $stage $region
            ;;
        "remove")
            check_prerequisites
            check_aws_credentials
            remove_stage $stage $region
            ;;
        "info")
            check_prerequisites
            check_aws_credentials
            log_info "Getting deployment information for $stage stage..."
            npx serverless info --stage $stage --region $region
            ;;
        "logs")
            check_prerequisites
            check_aws_credentials
            log_info "Showing logs for $stage stage..."
            npx serverless logs --stage $stage --region $region --tail
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
