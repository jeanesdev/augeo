// ============================================================================
// Resource Locks Module
// ============================================================================
// Purpose: Apply CanNotDelete locks to critical production resources
// Dependencies: Target resource must exist
// ============================================================================

@description('Environment name (dev, staging, production)')
@allowed(['dev', 'staging', 'production'])
param environment string

@description('Target resource ID to lock')
param targetResourceId string

@description('Target resource name (for lock naming)')
param targetResourceName string

@description('Lock notes explaining why resource is locked')
param lockNotes string = 'Critical production resource - prevent accidental deletion'

// Only apply locks in production
var shouldApplyLock = environment == 'production'

// ============================================================================
// Resource Lock
// ============================================================================

resource resourceLock 'Microsoft.Authorization/locks@2020-05-01' = if (shouldApplyLock) {
  name: '${targetResourceName}-lock'
  scope: resourceGroup()
  properties: {
    level: 'CanNotDelete'
    notes: lockNotes
  }
}

// ============================================================================
// Outputs
// ============================================================================

@description('Whether lock was applied')
output lockApplied bool = shouldApplyLock

@description('Lock name if applied')
output lockName string = shouldApplyLock ? resourceLock.name : ''
