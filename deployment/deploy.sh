#!/bin/bash
# Deployment script for Gold Sentiment Analysis Lambda function

set -e

echo "🚀 Gold Sentiment Analysis - AWS Lambda Deployment"
echo "=================================================="

# Configuration
FUNCTION_NAME="gold-sentiment-analysis"
PYTHON_VERSION="3.12"
PACKAGE_DIR="lambda_package"
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DEPLOYMENT_DIR")"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "\n${GREEN}▶ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi

    if ! command -v zip &> /dev/null; then
        print_error "zip is not installed"
        exit 1
    fi

    print_success "All prerequisites met"
}

# Create deployment package
create_package() {
    print_step "Creating deployment package..."

    # Clean up old package
    rm -rf "$PACKAGE_DIR"
    rm -f lambda_package.zip

    # Create package directory
    mkdir -p "$PACKAGE_DIR"

    # Install dependencies
    print_step "Installing dependencies..."
    pip3 install -r requirements-lambda.txt -t "$PACKAGE_DIR" \
        --platform manylinux2014_x86_64 \
        --only-binary=:all: \
        --upgrade

    # Copy source code
    print_step "Copying source code..."
    cp -r "$PROJECT_ROOT/src" "$PACKAGE_DIR/"

    # Copy Lambda handler
    cp lambda_handler.py "$PACKAGE_DIR/"

    # Create zip file
    print_step "Creating zip package..."
    cd "$PACKAGE_DIR"
    zip -r ../lambda_package.zip . -q
    cd ..

    # Get package size
    PACKAGE_SIZE=$(du -h lambda_package.zip | cut -f1)
    print_success "Package created: lambda_package.zip ($PACKAGE_SIZE)"

    # Check if package is too large (Lambda limit is 50MB zipped, 250MB unzipped)
    PACKAGE_SIZE_BYTES=$(stat -f%z lambda_package.zip 2>/dev/null || stat -c%s lambda_package.zip 2>/dev/null)
    if [ "$PACKAGE_SIZE_BYTES" -gt 52428800 ]; then
        print_warning "Package size exceeds 50MB. Consider using Lambda layers or S3."
    fi
}

# Deploy with Terraform
deploy_terraform() {
    print_step "Deploying with Terraform..."

    cd terraform

    # Check if terraform.tfvars exists
    if [ ! -f terraform.tfvars ]; then
        print_warning "terraform.tfvars not found. Please create it from terraform.tfvars.example"
        print_warning "Copy terraform.tfvars.example to terraform.tfvars and fill in your values"
        exit 1
    fi

    # Initialize Terraform
    print_step "Initializing Terraform..."
    terraform init

    # Plan deployment
    print_step "Planning deployment..."
    terraform plan -out=tfplan

    # Apply deployment
    read -p "Apply Terraform plan? (yes/no): " -n 3 -r
    echo
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        terraform apply tfplan
        print_success "Deployment complete!"

        # Show outputs
        print_step "Deployment outputs:"
        terraform output
    else
        print_warning "Deployment cancelled"
        rm tfplan
    fi

    cd ..
}

# Deploy with AWS CLI (alternative to Terraform)
deploy_aws_cli() {
    print_step "Deploying with AWS CLI..."

    # Check if function exists
    if aws lambda get-function --function-name "$FUNCTION_NAME" &> /dev/null; then
        print_step "Updating existing function..."
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://lambda_package.zip

        print_success "Function updated!"
    else
        print_error "Function does not exist. Please create it first using Terraform or AWS Console."
        print_warning "Or use: aws lambda create-function ..."
        exit 1
    fi
}

# Test locally
test_local() {
    print_step "Testing locally..."

    cd "$DEPLOYMENT_DIR"
    python3 lambda_handler.py
}

# Main execution
main() {
    cd "$DEPLOYMENT_DIR"

    case "${1:-terraform}" in
        package)
            check_prerequisites
            create_package
            ;;
        terraform)
            check_prerequisites
            create_package
            deploy_terraform
            ;;
        aws-cli)
            check_prerequisites
            create_package
            deploy_aws_cli
            ;;
        test)
            test_local
            ;;
        clean)
            print_step "Cleaning up..."
            rm -rf "$PACKAGE_DIR"
            rm -f lambda_package.zip
            rm -f terraform/tfplan
            print_success "Cleanup complete"
            ;;
        *)
            echo "Usage: $0 {package|terraform|aws-cli|test|clean}"
            echo ""
            echo "Commands:"
            echo "  package   - Create deployment package only"
            echo "  terraform - Deploy using Terraform (default)"
            echo "  aws-cli   - Update function using AWS CLI"
            echo "  test      - Test locally"
            echo "  clean     - Clean up build artifacts"
            exit 1
            ;;
    esac
}

main "$@"
