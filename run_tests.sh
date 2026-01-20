#!/bin/bash
# Test runner script for dumpsterr project
# Makes running common test commands easier

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Dumpsterr Test Suite ===${NC}\n"

# Default: run all non-Plex tests
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Running all tests (excluding Plex integration)...${NC}"
    python3 -m pytest tests/ -v -m "not plex" --cov=src --cov-report=term-missing --cov-report=html
    echo -e "\n${GREEN}✓ Tests complete!${NC}"
    echo -e "${YELLOW}Coverage report: htmlcov/index.html${NC}"
    exit 0
fi

# Parse command argument
case "$1" in
    "all")
        echo -e "${GREEN}Running all tests including Plex integration...${NC}"
        python3 -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
        ;;
    "plex")
        echo -e "${GREEN}Running only Plex integration tests...${NC}"
        echo -e "${YELLOW}Note: Requires .env.test file with valid credentials${NC}"
        python3 -m pytest tests/ -v -m "plex"
        ;;
    "config")
        echo -e "${GREEN}Running config module tests...${NC}"
        python3 -m pytest tests/test_config.py -v
        ;;
    "filesystem")
        echo -e "${GREEN}Running filesystem module tests...${NC}"
        python3 -m pytest tests/test_filesystem.py -v
        ;;
    "client")
        echo -e "${GREEN}Running Plex client tests...${NC}"
        python3 -m pytest tests/test_plex_client.py -v -m "not plex"
        ;;
    "main")
        echo -e "${GREEN}Running main module tests...${NC}"
        python3 -m pytest tests/test_main.py -v
        ;;
    "fast")
        echo -e "${GREEN}Running fast test suite (no coverage)...${NC}"
        python3 -m pytest tests/ -v -m "not plex" --tb=line
        ;;
    "coverage")
        echo -e "${GREEN}Generating detailed coverage report...${NC}"
        python3 -m pytest tests/ -m "not plex" --cov=src --cov-report=html --cov-report=term-missing
        echo -e "\n${YELLOW}Opening coverage report...${NC}"
        open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html manually"
        ;;
    "watch")
        echo -e "${GREEN}Running tests in watch mode...${NC}"
        echo -e "${YELLOW}Note: Requires pytest-watch (pip install pytest-watch)${NC}"
        ptw tests/ -- -m "not plex"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: ./run_tests.sh [OPTION]"
        echo ""
        echo "Options:"
        echo "  (none)      Run all non-Plex tests with coverage (default)"
        echo "  all         Run all tests including Plex integration"
        echo "  plex        Run only Plex integration tests"
        echo "  config      Run config module tests"
        echo "  filesystem  Run filesystem module tests"
        echo "  client      Run Plex client tests"
        echo "  main        Run main module tests"
        echo "  fast        Run tests without coverage (faster)"
        echo "  coverage    Generate and open HTML coverage report"
        echo "  watch       Run tests in watch mode (requires pytest-watch)"
        echo "  help        Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh          # Run standard test suite"
        echo "  ./run_tests.sh fast     # Quick test run"
        echo "  ./run_tests.sh coverage # Generate coverage report"
        echo "  ./run_tests.sh plex     # Test Plex integration"
        ;;
    *)
        echo -e "${YELLOW}Unknown option: $1${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

echo -e "\n${GREEN}✓ Tests complete!${NC}"
