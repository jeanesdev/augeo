# Email Configuration Guide

This guide explains how to set up email sending using Azure Communication Services (ACS) with custom domain authentication for the Augeo platform.

## Overview

The Augeo platform uses Azure Communication Services for transactional email sending with:
- **Custom domain**: `augeo.app`
- **Sender addresses**: `noreply@augeo.app`, `support@augeo.app`, `billing@augeo.app`
- **Authentication**: SPF, DKIM, DMARC for 95%+ deliverability
- **Delivery time**: < 30 seconds average
- **Cost**: ~$0.0012 per email sent

## Architecture

```
Application → Azure Communication Services → Email Domain → Recipient
                     ↓
              Authentication (SPF/DKIM/DMARC)
                     ↓
              DNS Records (augeo.app)
```

## Prerequisites

- Azure DNS Zone configured for `augeo.app` (see [DNS Configuration Guide](./dns-configuration.md))
- Azure Communication Services deployed (automatic in production)
- Access to Azure Portal
- Domain registrar access (if not using Azure DNS)

## Step 1: Deploy Azure Communication Services

ACS is automatically deployed with production infrastructure when `customDomain` is configured:

```bash
# Deploy infrastructure with email services
./infrastructure/scripts/provision.sh production <postgres-password>
```

The Bicep template creates:
- Communication Services resource
- Email Services resource
- Email domain configuration (custom or Azure-managed)

## Step 2: Retrieve Email Configuration Values

After deployment, get the required DNS records and configuration:

```bash
# Get deployment outputs
az deployment sub show \
  --name augeo-production-<timestamp> \
  --query properties.outputs

# Get ACS connection string (save to Key Vault)
az communication show \
  --name augeo-production-acs \
  --resource-group augeo-production-rg \
  --query "connectionString"

# Get email domain verification token
az communication email domain show \
  --email-service-name augeo-production-email \
  --domain-name augeo.app \
  --resource-group augeo-production-rg \
  --query "verificationStates.Domain.verificationToken"
```

## Step 3: Configure DNS Records for Email Authentication

Add the following DNS records to your Azure DNS Zone (or domain registrar):

### Domain Verification TXT Record
```bash
az network dns record-set txt add-record \
  --zone-name augeo.app \
  --resource-group augeo-production-rg \
  --record-set-name @ \
  --value "<verification-token-from-acs>"
```

### SPF Record (Sender Policy Framework)
```bash
az network dns record-set txt add-record \
  --zone-name augeo.app \
  --resource-group augeo-production-rg \
  --record-set-name @ \
  --value "v=spf1 include:spf.protection.outlook.com include:spf.azurecomm.net ~all"
```

### DMARC Record (Domain-based Message Authentication)
```bash
az network dns record-set txt add-record \
  --zone-name augeo.app \
  --resource-group augeo-production-rg \
  --record-set-name _dmarc \
  --value "v=DMARC1; p=quarantine; rua=mailto:dmarc@augeo.app; pct=100; fo=1"
```

### DKIM Records (DomainKeys Identified Mail)

Retrieve DKIM selectors from ACS:
```bash
# Get DKIM selector 1
az communication email domain show \
  --email-service-name augeo-production-email \
  --domain-name augeo.app \
  --resource-group augeo-production-rg \
  --query "verificationStates.DKIM.domainKey1"

# Get DKIM selector 2
az communication email domain show \
  --email-service-name augeo-production-email \
  --domain-name augeo.app \
  --resource-group augeo-production-rg \
  --query "verificationStates.DKIM.domainKey2"
```

Add CNAME records:
```bash
# DKIM selector 1
az network dns record-set cname set-record \
  --zone-name augeo.app \
  --resource-group augeo-production-rg \
  --record-set-name selector1-azurecomm-prod-net._domainkey \
  --cname "<dkim-selector-1-value>"

# DKIM selector 2
az network dns record-set cname set-record \
  --zone-name augeo.app \
  --resource-group augeo-production-rg \
  --record-set-name selector2-azurecomm-prod-net._domainkey \
  --cname "<dkim-selector-2-value>"
```

## Step 4: Verify Domain in Azure Portal

1. Navigate to Azure Portal → Communication Services → augeo-production-email
2. Go to "Provision domains" → "Custom domains"
3. Select `augeo.app`
4. Click "Verify" button
5. Wait 5-15 minutes for verification

Check verification status:
```bash
az communication email domain show \
  --email-service-name augeo-production-email \
  --domain-name augeo.app \
  --resource-group augeo-production-rg \
  --query "verificationStates"
```

Expected output:
```json
{
  "Domain": {
    "status": "Verified"
  },
  "SPF": {
    "status": "Verified"
  },
  "DKIM": {
    "status": "Verified"
  },
  "DMARC": {
    "status": "Verified"
  }
}
```

## Step 5: Configure Sender Addresses

The following sender addresses are pre-configured:

| Address | Purpose | Display Name |
|---------|---------|--------------|
| noreply@augeo.app | System notifications, no-reply emails | Augeo Platform |
| support@augeo.app | Support inquiries, help tickets | Augeo Support |
| billing@augeo.app | Invoices, payment receipts | Augeo Billing |
| notifications@augeo.app | User notifications, alerts | Augeo Notifications |

No additional configuration required - these are automatically enabled.

## Step 6: Store ACS Connection String in Key Vault

Securely store the connection string:

```bash
# Get connection string
ACS_CONNECTION_STRING=$(az communication list-key \
  --name augeo-production-acs \
  --resource-group augeo-production-rg \
  --query "primaryConnectionString" -o tsv)

# Store in Key Vault
az keyvault secret set \
  --vault-name augeo-production-kv \
  --name acs-connection-string \
  --value "$ACS_CONNECTION_STRING"
```

## Step 7: Update Application Configuration

### Backend Environment Variables

Update App Service configuration:

```bash
az webapp config appsettings set \
  --name augeo-production-api \
  --resource-group augeo-production-rg \
  --settings \
    EMAIL_PROVIDER="azure_communication_services" \
    ACS_CONNECTION_STRING="@Microsoft.KeyVault(SecretUri=https://augeo-production-kv.vault.azure.net/secrets/acs-connection-string/)" \
    EMAIL_FROM="noreply@augeo.app" \
    EMAIL_SUPPORT="support@augeo.app" \
    EMAIL_BILLING="billing@augeo.app"
```

### Backend Code Integration

Update `backend/app/services/email_service.py`:

```python
from azure.communication.email import EmailClient

class EmailService:
    def __init__(self):
        self.client = EmailClient.from_connection_string(
            settings.ACS_CONNECTION_STRING
        )

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_address: str = "noreply@augeo.app"
    ):
        message = {
            "senderAddress": from_address,
            "recipients": {
                "to": [{"address": to}]
            },
            "content": {
                "subject": subject,
                "plainText": body,
                "html": body  # Can also send HTML
            }
        }

        poller = self.client.begin_send(message)
        result = poller.result()
        return result
```

## Step 8: Test Email Delivery

### Send Test Email via Azure CLI

```bash
az communication email send \
  --sender "noreply@augeo.app" \
  --subject "Test Email from Augeo Platform" \
  --text "This is a test email to verify email configuration." \
  --to "your-email@example.com" \
  --connection-string "$ACS_CONNECTION_STRING"
```

### Test via Application

```bash
# SSH into App Service
az webapp ssh --name augeo-production-api --resource-group augeo-production-rg

# Test email sending
poetry run python -c "
from app.services.email_service import EmailService
import asyncio

async def test():
    service = EmailService()
    result = await service.send_email(
        to='your-email@example.com',
        subject='Test from Augeo',
        body='Testing email configuration'
    )
    print(f'Message ID: {result.message_id}')

asyncio.run(test())
"
```

## Step 9: Verify Email Authentication Score

Use [mail-tester.com](https://www.mail-tester.com) to verify email authentication:

1. Get unique test email from mail-tester.com
2. Send test email to that address
3. Check score (target: 10/10 or 9/10+)

Check for:
- ✅ SPF: Pass
- ✅ DKIM: Pass
- ✅ DMARC: Pass
- ✅ Not blacklisted
- ✅ Valid SMTP setup

### Using mail-tester.com
```bash
# Get test address from https://www.mail-tester.com
TEST_EMAIL="test-abc123@srv1.mail-tester.com"

# Send test email
az communication email send \
  --sender "noreply@augeo.app" \
  --subject "Authentication Test" \
  --text "Testing SPF, DKIM, and DMARC configuration" \
  --to "$TEST_EMAIL" \
  --connection-string "$ACS_CONNECTION_STRING"

# Check results at mail-tester.com
```

## Step 10: Monitor Email Delivery

### View Email Logs

```bash
# Check App Insights for email events
az monitor app-insights query \
  --app augeo-production-insights \
  --resource-group augeo-production-rg \
  --analytics-query "
    traces
    | where message contains 'email'
    | order by timestamp desc
    | take 100
  "
```

### Email Metrics

Monitor in Azure Portal:
- Communication Services → Metrics
- Email Services → Email status
- Track: Sent, Delivered, Bounced, Opened

### Common Email Headers

Example of properly configured email:
```
Received-SPF: pass
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
  d=augeo.app; s=selector1-azurecomm-prod-net;
Authentication-Results: spf=pass smtp.mailfrom=augeo.app;
  dkim=pass header.d=augeo.app;
  dmarc=pass action=none header.from=augeo.app;
```

## Troubleshooting

### Domain Verification Fails

**Issue**: Domain shows "Not Verified" status

**Solutions**:
```bash
# 1. Check DNS records are published
dig TXT augeo.app
dig TXT _dmarc.augeo.app
dig CNAME selector1-azurecomm-prod-net._domainkey.augeo.app

# 2. Wait for DNS propagation (up to 48 hours)
# 3. Verify TXT record matches exactly
az communication email domain show \
  --email-service-name augeo-production-email \
  --domain-name augeo.app \
  --resource-group augeo-production-rg

# 4. Re-trigger verification
az communication email domain update \
  --email-service-name augeo-production-email \
  --domain-name augeo.app \
  --resource-group augeo-production-rg
```

### Emails Landing in Spam

**Issue**: Emails delivered but marked as spam

**Solutions**:
1. **Check authentication score** (mail-tester.com should be 9+/10)
2. **Warm up your domain**: Start with low volume, gradually increase
3. **Review email content**: Avoid spam trigger words
4. **Set up reverse DNS** (PTR record)
5. **Monitor bounce rates**: Keep < 5%
6. **Add unsubscribe link**: Required for bulk email

### High Bounce Rate

**Issue**: Many emails bouncing back

**Solutions**:
- Validate email addresses before sending
- Maintain clean email list
- Remove invalid addresses after 2-3 bounces
- Check bounce reasons in ACS logs

### Slow Delivery

**Issue**: Emails taking > 30 seconds to deliver

**Solutions**:
```bash
# Check ACS service health
az communication show \
  --name augeo-production-acs \
  --resource-group augeo-production-rg \
  --query "provisioningState"

# Review Application Insights for errors
# Check network connectivity from App Service
```

### Connection String Invalid

**Issue**: Authentication errors when sending

**Solutions**:
```bash
# Rotate connection string
az communication regenerate-key \
  --name augeo-production-acs \
  --resource-group augeo-production-rg \
  --key-type primary

# Update Key Vault secret
# Restart App Service
```

## Email Templates

Recommended email templates for common scenarios:

### Welcome Email
```python
subject = "Welcome to Augeo Platform"
body = """
Hello {name},

Welcome to Augeo! Your account has been successfully created.

Get started:
- Complete your profile
- Explore features
- Contact support: support@augeo.app

Best regards,
The Augeo Team
"""
```

### Password Reset
```python
subject = "Reset Your Augeo Password"
body = """
Hello {name},

You requested to reset your password. Click the link below:

{reset_link}

This link expires in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
The Augeo Team
"""
```

### Email Verification
```python
subject = "Verify Your Email Address"
body = """
Hello {name},

Please verify your email address by clicking:

{verification_link}

This link expires in 24 hours.

Best regards,
The Augeo Team
"""
```

## Best Practices

1. **Use appropriate sender addresses**:
   - `noreply@` for automated emails
   - `support@` for support responses
   - `billing@` for payment-related emails

2. **Include unsubscribe links** for marketing emails

3. **Monitor bounce and complaint rates**:
   - Bounce rate: < 5%
   - Complaint rate: < 0.1%

4. **Implement rate limiting**:
   - Max 100 emails/min per sender
   - Warm up new domains gradually

5. **Use email templates** for consistency

6. **Track email metrics**:
   - Delivery rate
   - Open rate
   - Click rate
   - Bounce rate

## Cost Optimization

**ACS Email Pricing** (as of 2024):
- First 100 emails/month: Free
- Additional emails: $0.0012 per email

**Estimated monthly cost**:
- 1,000 emails: $1.08
- 10,000 emails: $11.88
- 100,000 emails: $119.88

**Tips**:
- Batch emails when possible
- Use transactional emails only (avoid marketing spam)
- Implement email preferences
- Remove bounced addresses

## Security Considerations

1. **Store connection strings in Key Vault** (never in code)
2. **Use managed identities** where possible
3. **Rotate connection strings** quarterly
4. **Monitor for anomalous sending patterns**
5. **Implement rate limiting** to prevent abuse
6. **Log all email sending** for audit trail

## Next Steps

- Set up DNS records: [DNS Configuration Guide](./dns-configuration.md)
- Configure monitoring: [Monitoring Guide](./monitoring.md)
- Review security: [Security Checklist](./security-checklist.md)

## References

- [Azure Communication Services Documentation](https://docs.microsoft.com/en-us/azure/communication-services/)
- [Email Authentication Best Practices](https://docs.microsoft.com/en-us/microsoft-365/security/office-365-security/email-authentication-about)
- [SPF Record Syntax](https://www.rfc-editor.org/rfc/rfc7208)
- [DKIM Specification](https://www.rfc-editor.org/rfc/rfc6376)
- [DMARC Guide](https://dmarc.org/overview/)
- [Mail Tester](https://www.mail-tester.com/)
