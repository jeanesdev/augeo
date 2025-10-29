// Minimal development environment parameters
using '../main-minimal.bicep'

param environment = 'dev'
param location = 'eastus'
param appName = 'augeo'
param customDomain = 'augeo.app'
param enableDns = true

param tags = {
  Environment: 'dev'
  Project: 'augeo-platform'
  ManagedBy: 'Bicep'
  CostCenter: 'development'
  Owner: 'devops-team'
  Purpose: 'local-development-with-dns'
}
