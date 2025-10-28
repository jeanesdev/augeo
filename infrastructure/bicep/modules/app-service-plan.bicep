// App Service Plan module for Augeo Platform

@description('Name of the App Service Plan')
param appServicePlanName string

@description('Azure region')
param location string = resourceGroup().location

@description('Environment (dev, staging, production)')
@allowed([
  'dev'
  'staging'
  'production'
])
param environment string

@description('Tags for the resource')
param tags object = {}

// SKU configuration based on environment
var skuConfigs = {
  dev: {
    tier: 'Basic'
    name: 'B1'
    capacity: 1
  }
  staging: {
    tier: 'Standard'
    name: 'S1'
    capacity: 1
  }
  production: {
    tier: 'Standard'
    name: 'S1'
    capacity: 2 // Initial capacity, autoscale configured separately
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: appServicePlanName
  location: location
  tags: tags
  sku: skuConfigs[environment]
  kind: 'linux'
  properties: {
    reserved: true // Required for Linux
    perSiteScaling: false
  }
}

output appServicePlanId string = appServicePlan.id
output appServicePlanName string = appServicePlan.name
output appServicePlanSku string = appServicePlan.sku.name
