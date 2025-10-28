// ============================================================================
// Azure Cost Budget Module
// ============================================================================
// Purpose: Configure cost budgets with alerts at 80% and 100% thresholds
// Dependencies: None (subscription-level resource)
// ============================================================================

@description('Environment name (dev, staging, production)')
@allowed(['dev', 'staging', 'production'])
param environment string

@description('Monthly budget amount in USD')
param budgetAmount int

@description('Email addresses to notify on budget alerts')
param alertEmailAddresses array

@description('Resource group name for budget scope')
param resourceGroupName string

@description('Tags to apply to all resources')
param tags object = {}

// ============================================================================
// Budget Configuration
// ============================================================================

var budgetName = 'budget-${environment}'
var startDate = '${utcNow('yyyy')}-${utcNow('MM')}-01'

// Calculate next year's date for end date
var nextYear = string(int(utcNow('yyyy')) + 1)
var endDate = '${nextYear}-${utcNow('MM')}-01'

resource budget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: budgetName
  properties: {
    category: 'Cost'
    amount: budgetAmount
    timeGrain: 'Monthly'
    timePeriod: {
      startDate: startDate
      endDate: endDate
    }
    filter: {
      dimensions: {
        name: 'ResourceGroupName'
        operator: 'In'
        values: [
          resourceGroupName
        ]
      }
    }
    notifications: {
      // 80% Warning Alert
      warning80: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        contactEmails: alertEmailAddresses
        thresholdType: 'Actual'
        locale: 'en-us'
      }
      // 100% Critical Alert
      critical100: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        contactEmails: alertEmailAddresses
        thresholdType: 'Actual'
        locale: 'en-us'
      }
      // 90% Forecasted Alert (predictive)
      forecasted90: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 90
        contactEmails: alertEmailAddresses
        thresholdType: 'Forecasted'
        locale: 'en-us'
      }
    }
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Budget resource ID')
output budgetId string = budget.id

@description('Budget name')
output budgetName string = budget.name

@description('Monthly budget amount')
output budgetAmount int = budgetAmount

@description('Budget alert configuration')
output alertConfiguration object = {
  warning: 80
  critical: 100
  forecasted: 90
  emailAddresses: alertEmailAddresses
}
