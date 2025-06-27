#!/bin/bash

# Tally Backend End-to-End Test Runner

set -e  # Exit on any error

echo "🚀 Tally Backend End-to-End Test Runner"
echo "=" $(printf '=%.0s' {1..50})

# Function to check API health
check_api_health() {
    echo "🔍 Checking API health..."
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ API is healthy and responding"
        return 0
    else
        echo "❌ API server is not accessible at http://localhost:8000"
        echo "   Make sure to start the server with:"
        echo "   cd tally-backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
        return 1
    fi
}

# Function to install test dependencies
install_deps() {
    echo "📦 Installing test dependencies..."
    if command -v uv >/dev/null 2>&1; then
        uv sync --extra test
        echo "✅ Test dependencies installed"
    else
        echo "❌ uv not found. Please install uv first."
        exit 1
    fi
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    uv run pytest tests/ -v --tb=short --timeout=60
}

# Main execution
case "${1:-all}" in
    "install")
        install_deps
        ;;
    "health")
        check_api_health
        ;;
    "all"|"")
        install_deps
        check_api_health
        run_tests
        ;;
    "test-only")
        run_tests
        ;;
    *)
        echo "Usage: $0 [install|health|all|test-only]"
        echo "  install   - Install test dependencies only"
        echo "  health    - Check API health only"
        echo "  all       - Install deps, check health, and run tests (default)"
        echo "  test-only - Run tests only (skip deps and health check)"
        exit 1
        ;;
esac

echo "🎉 Test runner completed successfully!" 