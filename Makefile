# Makefile for Meli Challenge Project
# Includes commands for building, running, testing, and validation

.PHONY: help build up down logs shell clean test deploy setup-dirs setup-env
.PHONY: dev-up dev-down dev-logs dev-shell prod-up prod-down prod-logs
.PHONY: status restart run-spider run-collect run-identify
.PHONY: test-unit test-spiders test-pipelines test-integration test-coverage test-docker test-pattern test-list test-report test-clean
.PHONY: validation-setup validation-test validation-run validation-report validation-clean

# Default target
help:
	@echo "🚀 Meli Challenge - Available Commands"
	@echo "======================================"
	@echo ""
	@echo "🏗️  Build & Run:"
	@echo "  build          - Build Docker image"
	@echo "  up             - Start all services"
	@echo "  down           - Stop all services"
	@echo "  restart        - Restart services"
	@echo "  status         - Check service status"
	@echo ""
	@echo "🔧 Development:"
	@echo "  dev-up         - Start development environment"
	@echo "  dev-down       - Stop development environment"
	@echo "  dev-logs       - View development logs"
	@echo "  dev-shell      - Access development container"
	@echo ""
	@echo "🚀 Production:"
	@echo "  prod-up        - Start production environment"
	@echo "  prod-down      - Stop production environment"
	@echo "  prod-logs      - View production logs"
	@echo ""
	@echo "🕷️  Spider Execution:"
	@echo "  run-spider     - Run identification spider"
	@echo "  run-collect    - Run collection spider"
	@echo "  run-identify   - Run identification spider"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-spiders   - Run spider tests only"
	@echo "  test-pipelines - Run pipeline tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-coverage  - Run tests with coverage"
	@echo "  test-docker    - Run tests in Docker"
	@echo "  test-pattern   - Run tests matching pattern"
	@echo "  test-list      - List all available tests"
	@echo "  test-report    - Generate test report"
	@echo "  test-clean     - Clean test artifacts"
	@echo ""
	@echo "🧠 AI Validation:"
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
	@echo "  deploy         - Deploy to AWS"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  logs           - View all service logs"
	@echo "  shell          - Access main container shell"

# Build and run
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec meli-crawler /bin/bash

restart:
	docker-compose restart

status:
	docker-compose ps

# Development environment
dev-up:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

dev-down:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml down

dev-logs:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f

dev-shell:
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec meli-crawler /bin/bash

# Production environment
prod-up:
	docker-compose -f docker-compose.yml up -d

prod-down:
	docker-compose -f docker-compose.yml down

prod-logs:
	docker-compose -f docker-compose.yml logs -f

# Spider execution
run-spider:
	docker-compose exec meli-crawler scrapy crawl meli-uy-identify

run-collect:
	docker-compose exec meli-crawler scrapy crawl meli-uy-collect

run-identify:
	docker-compose exec meli-crawler scrapy crawl meli-uy-identify

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

# Run tests in Docker
test-docker:
	docker-compose run --rm meli-crawler python -m unittest discover tests -v

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
	@echo "🧠 Setting up AI Validation System..."
	pip install -r validation/requirements.txt
	@echo "✅ Validation system setup complete!"
	@echo "🔑 Set your API key: export OPENAI_API_KEY='your_key_here'"

validation-test:
	@echo "🧪 Testing AI provider connection..."
	python validation/validation_cli.py test --provider openai

validation-run:
	@echo "🔍 Running validation on sample data..."
	python validation/run_validation.py

validation-report:
	@echo "📊 Generating validation report..."
	python validation/validation_cli.py generate-report validation_reports/ --output validation_summary.html

validation-clean:
	@echo "🧹 Cleaning validation artifacts..."
	rm -rf validation_reports/
	rm -f validation_cli.log
	@echo "✅ Validation artifacts cleaned!"

# Setup and maintenance
setup-dirs:
	mkdir -p logs data validation_reports

setup-env:
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Environment file created from template"; \
		echo "📝 Edit .env with your credentials"; \
	else \
		echo "⚠️  .env file already exists"; \
	fi

clean:
	docker-compose down --volumes --remove-orphans
	docker system prune -f
	rm -rf logs/* data/* validation_reports/*

deploy:
	./deploy.sh
