#!/bin/bash

# Deploy Local Script for Meli Challenge
# This script handles local deployment using uv for dependency management

set -e

echo "🚀 Starting local deployment..."

# Check if we're in the right directory
if [ ! -f "serverless.yml" ]; then
    echo "❌ Error: serverless.yml not found. Please run this script from the project root."
    exit 1
fi

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: .venv directory not found. Please run 'make setup' first."
    exit 1
fi

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it first."
    exit 1
fi

# Check if serverless is available
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx is not available. Please install Node.js first."
    exit 1
fi

echo "✅ Environment checks passed"

# Install dependencies using uv
echo "📦 Installing Python dependencies with uv..."
uv pip install -r requirements.txt

echo "✅ Dependencies installed"

# Deploy using serverless
echo "🚀 Deploying with Serverless Framework..."
npx serverless deploy --stage dev --verbose

echo "✅ Deployment completed successfully!"
echo "🎉 Your application is now deployed to AWS!"
