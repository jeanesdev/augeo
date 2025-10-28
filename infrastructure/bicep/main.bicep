// Main Bicep orchestration template for Augeo Platform
targetScope = 'subscription'

@description('Environment name')
@allowed([
  'dev'
  'staging'
  'production'
])
param environment string

@description('Azure region')
param location string = 'eastus'

@description('Application name prefix')
param appName string = 'augeo'

@description('Tags for all resources')
param tags object = {
  Environment: environment
  Project: 'augeo-platform'
  ManagedBy: 'Bicep'
}

// Naming convention
var resourceGroupName = '${appName}-${environment}-rg'

// Deploy Resource Group
module resourceGroup './modules/resource-group.bicep' = {
  name: 'resourceGroup-${environment}'
  params: {
    resourceGroupName: resourceGroupName
    location: location
    tags: tags
  }
}

// TODO: Add App Service Plan module (Phase 3)
// TODO: Add App Service (Backend) module (Phase 3)
// TODO: Add Static Web App (Frontend) module (Phase 3)
// TODO: Add PostgreSQL Flexible Server module (Phase 3)
// TODO: Add Redis Cache module (Phase 3)
// TODO: Add Key Vault module (Phase 3)
// TODO: Add Application Insights module (Phase 3)
// TODO: Add Log Analytics Workspace module (Phase 3)
// TODO: Add Storage Account module (Phase 3)
// TODO: Add DNS Zone module (Phase 5)
// TODO: Add Communication Services module (Phase 5)

// Outputs
output resourceGroupName string = resourceGroup.outputs.resourceGroupName
output resourceGroupId string = resourceGroup.outputs.resourceGroupId
output location string = location
output environment string = environment
