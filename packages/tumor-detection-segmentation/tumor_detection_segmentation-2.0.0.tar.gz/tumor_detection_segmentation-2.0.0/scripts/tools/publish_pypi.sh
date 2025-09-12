#!/bin/bash

# PyPI Publishing Helper Script
# This script helps you publish the tumor-detection-segmentation package to PyPI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  PyPI Publishing for tumor-detection  ${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_tools() {
    print_info "Checking required tools..."

    if ! command -v python &> /dev/null; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi

    if ! python -c "import build" &> /dev/null; then
        print_warning "build package not found. Installing..."
        pip install build
    fi

    if ! python -c "import twine" &> /dev/null; then
        print_warning "twine package not found. Installing..."
        pip install twine
    fi

    print_success "All tools are available"
}

check_version() {
    print_info "Checking package version..."
    VERSION=$(python -c "import sys; sys.path.insert(0, 'src'); from tumor_detection import __version__; print(__version__)")
    print_info "Current version: $VERSION"

    # Check if version exists on PyPI
    if pip index versions tumor-detection-segmentation 2>/dev/null | grep -q "$VERSION"; then
        print_error "Version $VERSION already exists on PyPI!"
        print_info "Please increment the version in src/tumor_detection/__init__.py"
        exit 1
    fi

    print_success "Version $VERSION is new"
}

run_tests() {
    print_info "Running package tests..."

    # Install package in dev mode
    pip install -e .[dev] -q

    # Run basic tests (excluding GPU/download tests)
    if pytest tests/ -v --tb=short -m "not gpu and not download" -q; then
        print_success "Tests passed"
    else
        print_error "Tests failed"
        exit 1
    fi

    # Test imports
    if python -c "import tumor_detection; from tumor_detection import load_model, run_inference"; then
        print_success "Package imports work correctly"
    else
        print_error "Package import test failed"
        exit 1
    fi
}

clean_build() {
    print_info "Cleaning previous builds..."
    rm -rf dist/ build/ *.egg-info/ src/*.egg-info/
    print_success "Build artifacts cleaned"
}

build_package() {
    print_info "Building package..."

    if python -m build; then
        print_success "Package built successfully"
        print_info "Built files:"
        ls -la dist/
    else
        print_error "Build failed"
        exit 1
    fi
}

check_package() {
    print_info "Checking package integrity..."

    if twine check dist/*; then
        print_success "Package check passed"
    else
        print_error "Package check failed"
        exit 1
    fi
}

upload_testpypi() {
    print_info "Uploading to Test PyPI..."

    if twine upload --repository testpypi dist/*; then
        print_success "Uploaded to Test PyPI"
        print_info "Test installation with:"
        echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tumor-detection-segmentation"
    else
        print_warning "Upload to Test PyPI failed (might already exist)"
    fi
}

test_installation() {
    print_info "Testing installation from Test PyPI..."

    # Create temporary virtual environment
    TEMP_ENV="test_env_$$"
    python -m venv $TEMP_ENV
    source $TEMP_ENV/bin/activate

    if pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ tumor-detection-segmentation; then
        if python -c "import tumor_detection; print(f'Test installation successful: {tumor_detection.__version__}')"; then
            print_success "Test installation works"
        else
            print_error "Test installation import failed"
            deactivate
            rm -rf $TEMP_ENV
            exit 1
        fi
    else
        print_error "Test installation failed"
        deactivate
        rm -rf $TEMP_ENV
        exit 1
    fi

    deactivate
    rm -rf $TEMP_ENV
}

upload_pypi() {
    print_warning "Ready to upload to production PyPI!"
    read -p "Are you sure you want to publish to PyPI? (yes/no): " -r

    if [[ $REPLY == "yes" ]]; then
        print_info "Uploading to PyPI..."

        if twine upload dist/*; then
            print_success "Successfully published to PyPI!"
            print_info "Install with: pip install tumor-detection-segmentation"
        else
            print_error "Upload to PyPI failed"
            exit 1
        fi
    else
        print_info "Upload cancelled by user"
        exit 0
    fi
}

# Main execution
main() {
    print_header

    # Parse command line arguments
    case "${1:-}" in
        "test")
            print_info "Running test-only pipeline..."
            check_tools
            check_version
            run_tests
            clean_build
            build_package
            check_package
            upload_testpypi
            test_installation
            print_success "Test pipeline completed successfully!"
            ;;
        "publish")
            print_info "Running full publish pipeline..."
            check_tools
            check_version
            run_tests
            clean_build
            build_package
            check_package
            upload_testpypi
            test_installation
            upload_pypi
            print_success "Publishing completed successfully!"
            ;;
        "build")
            print_info "Building package only..."
            check_tools
            clean_build
            build_package
            check_package
            print_success "Build completed successfully!"
            ;;
        *)
            echo "Usage: $0 {test|publish|build}"
            echo ""
            echo "Commands:"
            echo "  test     - Build and test on Test PyPI"
            echo "  publish  - Full pipeline: test + publish to PyPI"
            echo "  build    - Build package only"
            exit 1
            ;;
    esac
}

main "$@"
