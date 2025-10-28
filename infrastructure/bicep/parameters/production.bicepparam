// Production environment parameters for Augeo Platform
using './main.bicep'

param environment = 'production'
param location = 'eastus'
param appName = 'augeo'

// PostgreSQL admin password (retrieve from environment variable or Key Vault)
// Usage: az deployment sub create --parameters production.bicepparam --parameters postgresAdminPassword=$POSTGRES_PASSWORD
param postgresAdminPassword = ''

param tags = {
  Environment: 'production'
  Project: 'augeo-platform'
  ManagedBy: 'Bicep'
  CostCenter: 'operations'
  Compliance: 'required'
}
