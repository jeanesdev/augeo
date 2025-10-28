// DNS Zone Module
// Creates Azure DNS Zone for custom domain management

@description('Environment name')
param environment string

@description('Custom domain name (e.g., augeo.app)')
param domainName string

@description('Resource tags')
param tags object = {}

// DNS Zone Resource
resource dnsZone 'Microsoft.Network/dnsZones@2023-07-01-preview' = {
  name: domainName
  location: 'global'
  tags: tags
  properties: {
    zoneType: 'Public'
  }
}

// Common DNS Records

// Root domain A record (points to Static Web App)
resource rootARecord 'Microsoft.Network/dnsZones/A@2023-07-01-preview' = {
  parent: dnsZone
  name: '@'
  properties: {
    TTL: 3600
    targetResource: {
      id: '' // Will be updated after Static Web App deployment
    }
  }
}

// WWW CNAME (points to root)
resource wwwCname 'Microsoft.Network/dnsZones/CNAME@2023-07-01-preview' = {
  parent: dnsZone
  name: 'www'
  properties: {
    TTL: 3600
    CNAMERecord: {
      cname: domainName
    }
  }
}

// Admin subdomain CNAME (points to Static Web App)
resource adminCname 'Microsoft.Network/dnsZones/CNAME@2023-07-01-preview' = {
  parent: dnsZone
  name: 'admin'
  properties: {
    TTL: 3600
    CNAMERecord: {
      cname: '' // Will be set to Static Web App default hostname
    }
  }
}

// API subdomain CNAME (points to App Service)
resource apiCname 'Microsoft.Network/dnsZones/CNAME@2023-07-01-preview' = {
  parent: dnsZone
  name: 'api'
  properties: {
    TTL: 3600
    CNAMERecord: {
      cname: '' // Will be set to App Service default hostname
    }
  }
}

// TXT record for domain verification
resource verificationTxt 'Microsoft.Network/dnsZones/TXT@2023-07-01-preview' = {
  parent: dnsZone
  name: '@'
  properties: {
    TTL: 3600
    TXTRecords: [
      {
        value: [
          'augeo-domain-verification'
        ]
      }
    ]
  }
}

// MX records for email (will be configured with ACS)
resource mxRecord 'Microsoft.Network/dnsZones/MX@2023-07-01-preview' = {
  parent: dnsZone
  name: '@'
  properties: {
    TTL: 3600
    MXRecords: [] // Will be populated after ACS email domain setup
  }
}

// Outputs
output dnsZoneId string = dnsZone.id
output dnsZoneName string = dnsZone.name
output nameServers array = dnsZone.properties.nameServers
output dnsZoneResourceGroup string = resourceGroup().name

// Output instructions for nameserver configuration
output nameServerInstructions string = '''
Configure these nameservers at your domain registrar:
${join(dnsZone.properties.nameServers, '\n')}

After configuring, DNS propagation may take 24-48 hours.
Verify with: dig NS ${domainName}
'''
