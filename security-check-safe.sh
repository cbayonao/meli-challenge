#!/bin/bash

# Security Check Script for Meli Challenge (SAFE VERSION)
# This script checks for potential security vulnerabilities without exposing secrets

set -e

echo "🔒 Running security check for Meli Challenge..."

# Check for common secret patterns
echo "🔍 Checking for common secret patterns..."

# Check for API key patterns (generic patterns, not actual keys)
if grep -r "sk-[a-zA-Z0-9]{20,}" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.serverless --exclude=.env --exclude=security-check*.sh 2>/dev/null; then
    echo "❌ WARNING: Found potential OpenAI API key pattern!"
    exit 1
fi

# Check for AWS access key patterns
if grep -r "AKIA[0-9A-Z]{16}" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.serverless --exclude=.env --exclude=security-check*.sh 2>/dev/null; then
    echo "❌ WARNING: Found potential AWS access key pattern!"
    exit 1
fi

# Check for generic API key patterns
if grep -r "api_key.*=.*['\"][a-zA-Z0-9]{20,}['\"]" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.serverless --exclude=.env --exclude=security-check*.sh 2>/dev/null; then
    echo "❌ WARNING: Found potential hardcoded API key!"
    exit 1
fi

# Check for .env file in git
if git ls-files | grep -q "\.env"; then
    echo "❌ WARNING: .env file is tracked in Git!"
    exit 1
fi

# Check for hardcoded URLs with credentials (only in source files)
if grep -r "https://.*:.*@" *.py *.yml *.yaml *.json *.md *.sh --exclude=security-check*.sh 2>/dev/null; then
    echo "❌ WARNING: Found potential hardcoded credentials in URLs!"
    exit 1
fi

echo "✅ Security check passed - no obvious secrets found!"
echo "🔒 Remember to always use environment variables for sensitive data."
echo "💡 Tip: Run 'make security-check' for a more thorough check."
