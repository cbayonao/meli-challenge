# Makefile for Meli Challenge Project
# Updated to use UV for dependency management

.PHONY: help setup install install-dev install-test install-docs install-serverless install-all security-check
.PHONY: test test-unit test-spiders test-pipelines test-integration test-coverage test-pattern test-list test-report test-clean
.PHONY: validation-setup validation-test validation-run validation-report validation-clean
.PHONY: setup-dirs setup-env clean deploy format lint type-check
.PHONY: serverless-setup serverless-deploy serverless-deploy-prod serverless-remove serverless-info serverless-logs
.PHONY: run-identify run-collect dev-setup quick-test quick-format quick-lint quick-check dev-workflow

# Default target
help:
	@echo "Meli Challenge - Available Commands (UV-based)"
	@echo "================================================"
	@echo ""
	@echo "🔧 Setup & Installation:"
	@echo "  setup           - Setup project with UV"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies"
	@echo "  install-test    - Install testing dependencies"
	@echo "  install-docs    - Install documentation dependencies"
	@echo "  install-serverless - Install serverless dependencies"
	@echo "  install-all     - Install all dependencies"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-spiders   - Run spider tests only"
	@echo "  test-pipelines - Run pipeline tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage  - Run tests with coverage"
	@echo "  test-pattern   - Run tests matching pattern"
	@echo "  test-list      - List all available tests"
	@echo "  test-report    - Generate test report"
	@echo "  test-clean     - Clean test artifacts"
	@echo ""
	@echo "🎨 Code Quality:"
	@echo "  format         - Format code with black and isort"
	@echo "  format         - Format code with black and isort"
	@echo "  lint           - Lint code with flake8"
	@echo "  type-check     - Type check with mypy"
	@echo ""
	@echo "🤖 AI Validation:"
	@echo "  validation-setup    - Setup validation system"
	@echo "  validation-test     - Test AI provider connection"
	@echo "  validation-run      - Run validation on sample data"
	@echo "  validation-report   - Generate validation report"
	@echo "  validation-clean    - Clean validation artifacts"
	@echo ""
	@echo "🔧 Setup & Maintenance:"
	@echo "  setup-dirs     - Create necessary directories"
	@echo "  setup-env      - Setup environment from template"
	@echo "  clean          - Clean build artifacts"
	@echo ""
	@echo "🚀 Serverless Deployment:"
	@echo "  serverless-setup      - Setup Serverless Framework"
	@echo "  serverless-deploy     - Deploy to dev stage"
	@echo "  serverless-deploy-prod - Deploy to production"
	@echo "  serverless-remove     - Remove deployment"
	@echo "  serverless-info       - Show deployment info"
	@echo "  serverless-logs       - Show function logs"
	@echo "  deploy                - Deploy to AWS (alias for serverless-deploy)"
	@echo ""
	@echo "🕷️ Spider Execution:"
	@echo "  run-identify   - Run identification spider"
	@echo "  run-collect    - Run collection spider"

# Setup and installation
setup: setup-dirs setup-env install-all
	@echo "✅ Project setup complete!"

install:
	@echo "📦 Installing production dependencies..."
	uv pip install -e .

install-dev: install
	@echo "🔧 Installing development dependencies..."
	uv pip install -e ".[dev]"

install-test: install
	@echo "🧪 Installing testing dependencies..."
	uv pip install -e ".[test]"

install-docs: install
	@echo "📚 Installing documentation dependencies..."
	uv pip install -e ".[docs]"

install-serverless: install
	@echo "☁️ Installing serverless dependencies..."
	uv pip install -e ".[serverless]"

install-all: install
	@echo "🌟 Installing all dependencies..."
	uv pip install -e ".[all]"

# Code quality
format:
	@echo "🎨 Formatting code..."
	uv run black .
	uv run isort .

lint:
	@echo "🔍 Linting code..."
	uv run flake8 .

security-check: ## Run security checks for hardcoded secrets
	@echo "🔒 Running security checks..."
	./security-check-safe.sh

type-check:
	@echo "🔍 Type checking..."
	uv run mypy meli_crawler validation

# Run tests
test:
	@echo "🧪 Running all tests..."
	uv run python -m unittest discover tests -v

# Run specific test categories
test-unit:
	@echo "🧪 Running unit tests..."
	uv run python -m unittest discover tests -p "test_*.py" -v

test-spiders:
	@echo "🕷️ Running spider tests..."
	uv run python tests/run_tests.py --category spiders

test-pipelines:
	@echo "🔗 Running pipeline tests..."
	uv run python tests/run_tests.py --category pipelines

test-integration:
	@echo "🔗 Running integration tests..."
	uv run python tests/run_tests.py --category integration

# Run tests with coverage
test-coverage:
	@echo "📊 Running tests with coverage..."
	uv run python -m coverage run --source=meli_crawler,validation -m unittest discover tests -v
	uv run python -m coverage report
	uv run python -m coverage html

# Run tests with specific pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=TestClassName"; \
		exit 1; \
	fi
	@echo "🔍 Running tests matching pattern: $(PATTERN)"
	uv run python tests/run_tests.py --pattern $(PATTERN)

# List all tests
test-list:
	@echo "📋 Listing all available tests..."
	uv run python tests/run_tests.py --list

# Generate test report
test-report:
	@echo "📊 Generating test report..."
	uv run python tests/run_tests.py --report test_report.txt

# Clean test artifacts
test-clean:
	@echo "🧹 Cleaning test artifacts..."
	rm -rf test_reports/ coverage/ coverage_html/ .coverage coverage.xml
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# AI Validation System
validation-setup:
	@echo "🤖 Setting up AI Validation System..."
	uv pip install -e ".[validation]"
	@echo "✅ Validation system setup complete!"
	@echo "🔑 Set your API key: export OPENAI_API_KEY='your_key_here'"

validation-test:
	@echo "🧪 Testing AI provider connection..."
	uv run python validation/validation_cli.py test

validation-run:
	@echo "🚀 Running validation on sample data..."
	uv run python validation/run_validation.py

validation-report:
	@echo "📊 Generating validation report..."
	uv run python validation/validation_cli.py generate-report validation_reports/ --output validation_summary.html

validation-clean:
	@echo "🧹 Cleaning validation artifacts..."
	rm -rf validation_reports/
	rm -f validation_cli.log
	@echo "Validation artifacts cleaned!"

# Spider execution
run-identify:
	@echo "🕷️ Running identification spider..."
	uv run scrapy crawl meli-uy-identify

run-collect:
	@echo "🕷️ Running collection spider..."
	uv run scrapy crawl meli-uy-collect

# Setup and maintenance
setup-dirs:
	@echo "📁 Creating necessary directories..."
	mkdir -p logs data validation_reports test_reports coverage_html
	@echo "✅ Directories created!"

setup-env:
	@echo "🔧 Setting up environment..."
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Environment file created from template"; \
		echo "⚠️  Please edit .env with your actual values"; \
	else \
		echo "✅ Environment file already exists"; \
	fi

# Serverless deployment
serverless-setup:
	@echo "☁️ Setting up Serverless Framework..."
	uv run npm install
	@echo "✅ Serverless setup complete!"

serverless-deploy:
	@echo "🚀 Deploying to development stage..."
	uv run npx serverless deploy --stage dev --verbose

serverless-deploy-prod:
	@echo "🚀 Deploying to production stage..."
	uv run npx serverless deploy --stage prod --verbose

serverless-remove:
	@echo "🗑️ Removing deployment..."
	uv run npx serverless remove --verbose

serverless-info:
	@echo "ℹ️ Showing deployment info..."
	uv run npx serverless info

serverless-logs:
	@echo "📋 Showing function logs..."
	uv run npx serverless logs -f validation

clean: test-clean validation-clean
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ logs/* data/* node_modules/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

deploy: serverless-deploy

# Development workflow
dev-setup: setup install-dev install-test
	@echo "🚀 Development environment ready!"

# Quick development commands
quick-test: test-unit
quick-format: format
quick-lint: lint
quick-check: type-check

# Full development workflow
dev-workflow: quick-format quick-lint quick-check quick-test
	@echo "✅ Development workflow complete!"
