# Makefile for Meli Challenge Project

.PHONY: help test test-unit test-spiders test-pipelines test-integration test-coverage test-pattern test-list test-report test-clean
.PHONY: validation-setup validation-test validation-run validation-report validation-clean
.PHONY: setup-dirs setup-env clean deploy

# Default target
help:
	@echo "Meli Challenge - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "Testing:"
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
	@echo "AI Validation:"
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
	@echo "Spider Execution:"
	@echo "  run-identify   - Run identification spider"
	@echo "  run-collect    - Run collection spider"

# Run tests
test:
	python -m unittest discover tests -v

# Run specific test categories
test-unit:
	python -m unittest discover tests -p "test_*.py" -v

test-spiders:
	python tests/run_tests.py --category spiders

test-pipelines:
	python tests/run_tests.py --category pipelines

test-integration:
	python tests/run_tests.py --category integration

# Run tests with coverage
test-coverage:
	python -m coverage run --source=meli_crawler,validation -m unittest discover tests -v
	python -m coverage report
	python -m coverage html

# Run tests with specific pattern
test-pattern:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-pattern PATTERN=TestClassName"; \
		exit 1; \
	fi
	python tests/run_tests.py --pattern $(PATTERN)

# List all tests
test-list:
	python tests/run_tests.py --list

# Generate test report
test-report:
	python tests/run_tests.py --report test_report.txt

# Clean test artifacts
test-clean:
	rm -rf test_reports/ coverage/ .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# AI Validation System
validation-setup:
	@echo "Setting up AI Validation System..."
	pip install -r validation/requirements.txt
	@echo "Validation system setup complete!"
	@echo "Set your API key: export OPENAI_API_KEY='your_key_here'"

validation-test:
	@echo "Testing AI provider connection..."
	python validation/validation_cli.py test --provider openai

validation-run:
	@echo "Running validation on sample data..."
	python validation/run_validation.py

validation-report:
	@echo "Generating validation report..."
	python validation/validation_cli.py generate-report validation_reports/ --output validation_summary.html

validation-clean:
	@echo "🧹 Cleaning validation artifacts..."
	rm -rf validation_reports/
	rm -f validation_cli.log
	@echo "Validation artifacts cleaned!"

# Spider execution
run-identify:
	@echo "Running identification spider..."
	scrapy crawl meli-uy-identify

run-collect:
	@echo "Running collection spider..."
	scrapy crawl meli-uy-collect

# Setup and maintenance
setup-dirs:
	mkdir -p logs data validation_reports

setup-env:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "Environment file created from template"; \
		echo "Edit .env with your credentials"; \
	else \
		echo ".env file already exists"; \
	fi

# Serverless deployment
serverless-setup:
	@echo "🚀 Setting up Serverless Framework..."
	npm install
	@echo "✅ Serverless setup complete!"

serverless-deploy:
	@echo "🚀 Deploying with Serverless Framework..."
	./deploy-serverless.sh deploy

serverless-deploy-prod:
	@echo "🚀 Deploying to production..."
	./deploy-serverless.sh deploy prod

serverless-remove:
	@echo "🗑️  Removing Serverless deployment..."
	./deploy-serverless.sh remove

serverless-info:
	@echo "📊 Getting Serverless deployment info..."
	./deploy-serverless.sh info

serverless-logs:
	@echo "📝 Showing Serverless logs..."
	./deploy-serverless.sh logs

clean:
	rm -rf logs/* data/* validation_reports/* coverage/ .coverage node_modules/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

deploy:
	@echo "🚀 Deploying with Serverless Framework..."
	./deploy-serverless.sh deploy
