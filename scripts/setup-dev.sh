#!/bin/bash

# Plotari Chatbot Development Setup Script
# This script helps new developers set up the project quickly

set -e  # Exit on any error

echo "🚀 Setting up Plotari Chatbot development environment..."

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

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 is not installed. Please install Python 3.8+ and try again."
        exit 1
    fi
}

# Check if Git is installed
check_git() {
    print_status "Checking Git installation..."
    if command -v git &> /dev/null; then
        GIT_VERSION=$(git --version | cut -d' ' -f3)
        print_success "Git $GIT_VERSION found"
    else
        print_error "Git is not installed. Please install Git and try again."
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Create .env file if it doesn't exist
create_env_file() {
    print_status "Setting up environment configuration..."
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Weaviate Configuration
WEAVIATE_URL=https://your-cluster.weaviate.cloud
WEAVIATE_API_KEY=your_weaviate_api_key
WEAVIATE_COLLECTION=Plotarichatbot

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
LOG_TO_FILE=false
ENVIRONMENT=development

# CORS Configuration (optional)
CORS_ORIGINS=*
EOF
        print_success ".env file created with template values"
        print_warning "Please update .env file with your actual API keys and configuration"
    else
        print_warning ".env file already exists"
    fi
}

# Set up Git hooks
setup_git_hooks() {
    print_status "Setting up Git hooks..."
    
    # Create pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook to run basic checks

echo "Running pre-commit checks..."

# Run linting
if command -v flake8 &> /dev/null; then
    flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
    if [ $? -ne 0 ]; then
        echo "❌ Linting failed. Please fix the issues before committing."
        exit 1
    fi
fi

# Run tests
if command -v pytest &> /dev/null; then
    pytest tests/ -v --tb=short
    if [ $? -ne 0 ]; then
        echo "❌ Tests failed. Please fix the issues before committing."
        exit 1
    fi
fi

echo "✅ Pre-commit checks passed"
EOF

    chmod +x .git/hooks/pre-commit
    print_success "Git hooks configured"
}

# Install development dependencies
install_dev_dependencies() {
    print_status "Installing development dependencies..."
    pip install pytest pytest-cov flake8 black bandit safety
    print_success "Development dependencies installed"
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short
        print_success "Tests completed"
    else
        print_warning "No tests directory found"
    fi
}

# Main setup function
main() {
    echo "=========================================="
    echo "  Plotari Chatbot Development Setup"
    echo "=========================================="
    echo
    
    check_python
    check_git
    create_venv
    activate_venv
    install_dependencies
    install_dev_dependencies
    create_env_file
    setup_git_hooks
    run_tests
    
    echo
    echo "=========================================="
    print_success "Setup completed successfully!"
    echo "=========================================="
    echo
    echo "Next steps:"
    echo "1. Update .env file with your API keys"
    echo "2. Run 'python run.py' to start the development server"
    echo "3. Visit http://localhost:8000/docs for API documentation"
    echo
    echo "For more information, see:"
    echo "- README.md for project overview"
    echo "- CONTRIBUTING.md for contribution guidelines"
    echo "- .github/workflows/ci.yml for CI/CD pipeline"
    echo
}

# Run main function
main "$@"
