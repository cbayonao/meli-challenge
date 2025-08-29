#!/bin/bash

# Deploy Docker Script for Meli Challenge
# This script builds and deploys Docker containers to AWS ECR and Lambda

set -e

echo "🐳 Starting Docker deployment for Meli Challenge..."

# Configuration
STAGE=${1:-dev}
REGION=${2:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "📋 Configuration:"
echo "  Stage: $STAGE"
echo "  Region: $REGION"
echo "  Account ID: $ACCOUNT_ID"

# Check if we're in the right directory
if [ ! -f "serverless-docker.yml" ]; then
    echo "❌ Error: serverless-docker.yml not found. Please run this script from the project root."
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not running."
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ Environment checks passed"

# Step 1: Create ECR repositories first
echo "🏗️ Step 1: Creating ECR repositories..."
aws ecr create-repository --repository-name meli-challenge-identification --region $REGION --image-scanning-configuration scanOnPush=true || echo "Repository already exists"
aws ecr create-repository --repository-name meli-challenge-collection --region $REGION --image-scanning-configuration scanOnPush=true || echo "Repository already exists"

echo "✅ ECR repositories created successfully"

# Step 2: Deploy infrastructure (DynamoDB, SQS, etc.)
echo "🏗️ Step 2: Deploying infrastructure with Serverless..."
npx serverless deploy --config serverless-infra-docker.yml --stage $STAGE --region $REGION

echo "✅ Infrastructure deployed successfully"

# Step 3: Get ECR repository URIs from CloudFormation outputs
echo "📦 Step 3: Getting ECR repository information..."

IDENTIFICATION_REPO_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/meli-challenge-identification
COLLECTION_REPO_URI=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/meli-challenge-collection

echo "  Identification Repository: $IDENTIFICATION_REPO_URI"
echo "  Collection Repository: $COLLECTION_REPO_URI"

# Step 4: Login to ECR
echo "🔐 Step 4: Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

echo "✅ Logged into ECR successfully"

# Step 5: Build and push identification spider image
echo "🔨 Step 5: Building identification spider image..."
docker build -f Dockerfile.identification -t meli-challenge-identification:$STAGE .
docker tag meli-challenge-identification:$STAGE $IDENTIFICATION_REPO_URI:$STAGE
docker tag meli-challenge-identification:$STAGE $IDENTIFICATION_REPO_URI:latest

echo "📤 Pushing identification spider image to ECR..."
docker push $IDENTIFICATION_REPO_URI:$STAGE
docker push $IDENTIFICATION_REPO_URI:latest

echo "✅ Identification spider image pushed successfully"

# Step 6: Build and push collection spider image
echo "🔨 Step 6: Building collection spider image..."
docker build -f Dockerfile.collection -t meli-challenge-collection:$STAGE .
docker tag meli-challenge-collection:$STAGE $COLLECTION_REPO_URI:$STAGE
docker tag meli-challenge-collection:$STAGE $COLLECTION_REPO_URI:latest

echo "📤 Pushing collection spider image to ECR..."
docker push $COLLECTION_REPO_URI:$STAGE
docker push $COLLECTION_REPO_URI:latest

echo "✅ Collection spider image pushed successfully"

# Step 7: Update Lambda functions to use new images
echo "🔄 Step 7: Updating Lambda functions..."
npx serverless deploy function --config serverless-docker.yml --stage $STAGE --region $REGION --function identification-spider
npx serverless deploy function --config serverless-docker.yml --stage $STAGE --region $REGION --function collection-spider

echo "✅ Lambda functions updated successfully"

echo "🎉 Docker deployment completed successfully!"
echo "🚀 Your Meli Challenge application is now running on AWS Lambda with Docker containers!"
echo ""
echo "📊 Deployment Summary:"
echo "  - Infrastructure: ✅ Deployed"
echo "  - ECR Repositories: ✅ Created"
echo "  - Docker Images: ✅ Built and Pushed"
echo "  - Lambda Functions: ✅ Updated"
echo ""
echo "🔗 API Endpoint: https://$(aws cloudformation describe-stacks --stack-name meli-challenge-docker-$STAGE --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`ServiceEndpoint`].OutputValue' --output text)/$STAGE/scrape/identify"
