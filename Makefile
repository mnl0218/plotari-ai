# Plotari Chatbot Development Makefile

.PHONY: help install test lint format clean run docker-build docker-run setup-dev

# Default target
help:
	@echo "Plotari Chatbot Development Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup-dev     Set up development environment"
	@echo "  install       Install dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  run           Start development server"
	@echo "  test          Run tests"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black"
	@echo "  clean         Clean up temporary files"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"
	@echo ""
	@echo "Quality Commands:"
	@echo "  security      Run security checks"
	@echo "  coverage      Run tests with coverage report"
	@echo "  all-checks    Run all quality checks"

# Setup development environment
setup-dev:
	@echo "Setting up development environment..."
	@bash scripts/setup-dev.sh

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black bandit safety

# Start development server
run:
	@echo "Starting development server..."
	python run.py

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --tb=short

# Run tests with coverage
coverage:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=src/ --cov-report=html --cov-report=term

# Run linting
lint:
	@echo "Running linting checks..."
	flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	@echo "Formatting code..."
	black src/ tests/

# Run security checks
security:
	@echo "Running security checks..."
	bandit -r src/ -ll
	safety check

# Run all quality checks
all-checks: lint test security
	@echo "All quality checks completed"

# Clean up temporary files
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t plotari-chatbot:latest .

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 --env-file .env plotari-chatbot:latest

# Development workflow
dev: install test lint
	@echo "Development checks completed"

# Pre-commit checks
pre-commit: lint test
	@echo "Pre-commit checks completed"

# CI pipeline simulation
ci: install lint test security
	@echo "CI pipeline simulation completed"
