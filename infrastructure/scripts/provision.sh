#!/bin/bash
# Infrastructure provisioning script for Augeo Platform
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ -z "$1" ]; then
  echo -e "${RED}Error: Environment parameter required${NC}"
  echo "Usage: $0 <environment> [subscription-id]"
  echo "  environment: dev, staging, or production"
  echo "  subscription-id: Optional Azure subscription ID (uses default if not provided)"
  exit 1
fi

ENVIRONMENT=$1
SUBSCRIPTION_ID=${2:-$(az account show --query id -o tsv)}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BICEP_DIR="$(dirname "$SCRIPT_DIR")/bicep"
LOCATION="eastus"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
  echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
  echo "Must be one of: dev, staging, production"
  exit 1
fi

echo -e "${GREEN}=== Augeo Platform Infrastructure Provisioning ===${NC}"
echo "Environment: $ENVIRONMENT"
echo "Location: $LOCATION"
echo "Subscription: $SUBSCRIPTION_ID"
echo ""

# Set subscription context
echo -e "${YELLOW}Setting Azure subscription context...${NC}"
az account set --subscription "$SUBSCRIPTION_ID"

# Validate Bicep template
echo -e "${YELLOW}Validating Bicep template...${NC}"
az bicep build --file "$BICEP_DIR/main.bicep"

# Run what-if analysis
echo -e "${YELLOW}Running deployment preview (what-if)...${NC}"
az deployment sub what-if \
  --location "$LOCATION" \
  --template-file "$BICEP_DIR/main.bicep" \
  --parameters environment="$ENVIRONMENT" location="$LOCATION"

# Confirm deployment
if [ "$ENVIRONMENT" == "production" ]; then
  echo ""
  echo -e "${RED}WARNING: You are about to deploy to PRODUCTION!${NC}"
  read -p "Are you sure you want to continue? (yes/no): " -r
  echo
  if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Deployment cancelled."
    exit 0
  fi
fi

# Deploy infrastructure
echo -e "${GREEN}Deploying infrastructure...${NC}"
DEPLOYMENT_NAME="augeo-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

az deployment sub create \
  --name "$DEPLOYMENT_NAME" \
  --location "$LOCATION" \
  --template-file "$BICEP_DIR/main.bicep" \
  --parameters environment="$ENVIRONMENT" location="$LOCATION" \
  --verbose

# Get deployment outputs
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo ""
echo "Deployment outputs:"
az deployment sub show \
  --name "$DEPLOYMENT_NAME" \
  --query properties.outputs

echo ""
echo -e "${GREEN}=== Provisioning Complete ===${NC}"
echo "Resource Group: augeo-${ENVIRONMENT}-rg"
echo "Region: $LOCATION"
echo ""
echo "Next steps:"
echo "  1. Verify resources in Azure Portal"
echo "  2. Configure secrets in Key Vault (see docs/operations/deployment-runbook.md)"
echo "  3. Deploy application code via CI/CD pipeline"
