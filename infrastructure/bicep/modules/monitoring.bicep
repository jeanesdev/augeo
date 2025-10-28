// Application Insights module for Augeo Platform

@description('Name of the Application Insights instance')
param appInsightsName string

@description('Azure region')
param location string = resourceGroup().location

@description('Environment (dev, staging, production)')
@allowed([
  'dev'
  'staging'
  'production'
])
param environment string

@description('Log Analytics Workspace ID')
param workspaceId string

@description('Tags for the resource')
param tags object = {}

// Sampling configuration based on environment
var samplingPercentage = environment == 'production' ? 10 : 100

// Daily cap configuration based on environment (GB per day)
var dailyCapGB = environment == 'dev' ? 0 : environment == 'staging' ? 1 : 5

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspaceId
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    SamplingPercentage: samplingPercentage
    IngestionMode: 'LogAnalytics'
    DisableIpMasking: false
    Request_Source: 'rest'
  }
}

// Configure daily cap (if specified)
resource dailyCap 'Microsoft.Insights/components/pricingPlans@2017-10-01' = if (dailyCapGB > 0) {
  parent: appInsights
  name: 'current'
  properties: {
    cap: dailyCapGB
    stopSendNotificationWhenHitCap: false
  }
}

output appInsightsId string = appInsights.id
output appInsightsName string = appInsights.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
