// ============================================================================
// Azure Cost Budget Module
// ============================================================================
// Purpose: Configure cost budgets with alerts at 80% and 100% thresholds
// Dependencies: None (subscription-level resource)
// ============================================================================

targetScope = 'subscription'

@description('Environment name (dev, staging, production)')
@allowed(['dev', 'staging', 'production'])
param environment string

@description('Monthly budget amount in USD')
param budgetAmount int

@description('Email addresses to notify on budget alerts')
param alertEmailAddresses array

@description('Resource group name for budget scope')
param resourceGroupName string

@description('Budget start date (YYYY-MM-DD format). Defaults to current month.')
param startDate string = utcNow('yyyy-MM-01')

@description('Budget end date (YYYY-MM-DD format). Defaults to 3 years from now.')
param endDate string = dateTimeAdd(utcNow(), 'P3Y', 'yyyy-MM-01')

// ============================================================================
// Budget Configuration
// ============================================================================

var budgetName = 'budget-${environment}'

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
