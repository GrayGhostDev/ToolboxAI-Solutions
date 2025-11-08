# Supabase SSL Certificate Configuration
**Purpose:** Secure database connections with SSL/TLS certificate verification
**Certificate Location:** `supabase/prod-ca-2021 (1).crt`
**Certificate:** Supabase Root 2021 CA

---

## 📋 SSL Connection Modes

PostgreSQL supports several SSL modes for database connections:

| Mode | Description | Certificate Required | Security Level |
|------|-------------|---------------------|----------------|
| `disable` | No SSL encryption | ❌ | ⚠️ Low (not recommended) |
| `require` | SSL required, no certificate verification | ❌ | ✅ Good (default) |
| `verify-ca` | Verify server certificate against CA | ✅ | ✅✅ Better |
| `verify-full` | Verify certificate + hostname | ✅ | ✅✅✅ Best |

---

## 🔧 Current Configuration (Recommended for Most Cases)

### Mode: `sslmode=require`

**DATABASE_URL:**
```bash
postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=require
```

**Benefits:**
- ✅ SSL/TLS encryption enabled
- ✅ Simple configuration (no certificate needed)
- ✅ Works on all platforms
- ✅ Recommended by Supabase for most use cases

**When to use:**
- Standard production deployments
- Cloud platforms (Render, Vercel, AWS, etc.)
- Development and testing environments

---

## 🔐 Enhanced Security Configuration (Optional)

### Mode: `sslmode=verify-ca`

For enhanced security with certificate verification:

**DATABASE_URL:**
```bash
postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=verify-ca&sslrootcert=/opt/render/project/.postgresql/root.crt
```

**Benefits:**
- ✅✅ SSL/TLS encryption + certificate verification
- ✅✅ Protects against man-in-the-middle attacks
- ✅✅ Validates server identity

**When to use:**
- High-security requirements
- Financial or healthcare applications
- Compliance requirements (PCI-DSS, HIPAA, SOC 2)

---

## 🚀 Render Deployment Setup

### Option 1: Standard SSL (Current - Recommended)

**No additional configuration needed!**

Your current DATABASE_URL already uses `sslmode=require`:
```bash
postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=require
```

This provides SSL encryption without requiring certificate management.

---

### Option 2: Enhanced SSL with Certificate Verification

If you need enhanced security with certificate verification:

#### Step 1: Add SSL Certificate to Render Dashboard

Navigate to: **Render Dashboard → Environment Variable Groups → toolboxai-secrets**

Add the following environment variable:

**Key:** `SUPABASE_SSL_CERT_B64`

**Value:** (Base64-encoded certificate)
```
LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUR4RENDQXF5Z0F3SUJBZ0lVYkx4TW9kNjJQMmt0Q2lBa3huS0p3dEU5VlBZd0RRWUpLb1pJaHZjTkFRRUwKQlFBd2F6RUxNQWtHQTFVRUJoTUNWVk14RURBT0JnTlZCQWdNQjBSbGJIZGhjbVV4RXpBUkJnTlZCQWNNQ2s1bApkeUJEWVhOMGJHVXhGVEFUQmdOVkJBb01ERk4xY0dGaVlYTmxJRWx1WXpFZU1Cd0dBMVVFQXd3VlUzVndZV0poCmMyVWdVbTl2ZENBeU1ESXhJRU5CTUI0WERUSXhNRFF5T0RFd05UWTFNMW9YRFRNeE1EUXlOakV3TlRZMU0xb3cKYXpFTE1Ba0dBMVVFQmhNQ1ZWTXhFREFPQmdOVkJBZ01CMFJsYkhkaGNtVXhFekFSQmdOVkJBY01DazVsZHlCRApZWE4wYkdVeEZUQVRCZ05WQkFvTURGTjFjR0ZpWVhObElFbHVZekVlTUJ3R0ExVUVBd3dWVTNWd1lXSmhjMlVnClVtOXZkQ0F5TURJeElFTkJNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQXFRWFcKUXlIT0IrcVIyR0pvYkNxL0NCbVE0MEcwb0RtQ0MzbXpWbm44c3Y0WE5lV3RFNVhjRUwwdVZpaDdKbzREa3gxUQpEbUdIQkgxekRmZ3MycVhpTGI2eHB3L0NLUVB5cFpXMUpzc09UTUlmUXBwTlE4N0s3NVlhMHAyNVkzZVBTMnQyCkd0dkh4TmpVVjZrak9aakVuMnlXRWNCZHBPVkNVWUJWRkJOTUI0WUJIa05SRGEvK1M0dXl3QW9hVFduQ0pMVWkKY3ZUbEhtTXc2eFNRUW4xVWZSUUhrNTBETUNFSjdDeTFSeHJaSnJrWFhSUDNMcVFMMmlqSjZGNHlNZmgrR3liNApPNFhham9Wai8rUjRHd3l3S1lyclM4UHJTTnR3eHI1U3RsUU84eklRVVNNaXEyNndNOG1nRUxGbFMvMzJVY2x0Ck5hUTF4QlJpemt6cFpjdDlEd0lEQVFBQm8yQXdYakFMQmdOVkhROEVCQU1DQVFZd0hRWURWUjBPQkJZRUZLalgKdVhZMzJDenRraEltbmc0eUpOVXRhVVlzTUI4R0ExVWRJd1FZTUJhQUZLalh1WFkzMkN6dGtoSW1uZzR5Sk5VdAphVVlzTUE4R0ExVWRFd0VCL3dRRk1BTUJBZjh3RFFZSktvWklodmNOQVFFTEJRQURnZ0VCQUI4c3B6Tm4rNFZVCnRWeGJkTWFYKzM5WjUwc2M3dUFUbXVzMTZqbW1IamhJSHorbC85R2xKNUtxQU1PeDI2bVBaZ2Z6RzdvbmVMMmIKVlcrV2dZVWtUVDNYRVBGV25UcDJSSndRYW84L3RZUFhXRUpEYzBXVlFIcnBtbldPRktVL2QzTXFCZ0JtNXkrNgpqQjgxVFUvUkcyclZlclBEV1ArMU1NY05OeTA0OTFDVEw1WFFaN0pmREpKOUNDbVhTZHRUbDR1VVFuU3V2L1F4CkNlYTEzQlgyWmdKYzdBdTMwdmloTGh1YjUyRGU0UC80Z29uS3NOSFlkYldqZzdPV0t3TnYveml0R0RWREI5WTIKQ01UeVpLRzNYRXU1R2hsMUxFbkkzUW1FS3NxYUNMdjEyQm5WamJrU2Vac01uZXZKUHMxWWU2VGpqSndkaWs1UApvL2JLaUl6K0ZxOD0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
```

#### Step 2: Update DATABASE_URL

Change your DATABASE_URL to use `verify-ca`:

**From:**
```bash
postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=require
```

**To:**
```bash
postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=verify-ca&sslrootcert=/opt/render/project/.postgresql/root.crt
```

#### Step 3: Deploy

The certificate will be automatically:
1. Decoded from base64 during pre-deployment
2. Written to `/opt/render/project/.postgresql/root.crt`
3. Used by PostgreSQL for certificate verification

**Pre-deploy script** (already added to render.yaml):
```bash
if [ ! -z "$SUPABASE_SSL_CERT_B64" ]; then
  echo "Setting up Supabase SSL certificate..."
  mkdir -p /opt/render/project/.postgresql
  echo "$SUPABASE_SSL_CERT_B64" | base64 -d > /opt/render/project/.postgresql/root.crt
  chmod 600 /opt/render/project/.postgresql/root.crt
  echo "SSL certificate configured"
fi
```

---

## 🧪 Testing SSL Connection

### Local Testing (macOS/Linux)

#### Test with sslmode=require:
```bash
psql "postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=require" -c "SELECT version();"
```

#### Test with certificate verification:
```bash
# Set certificate path
export PGSSLROOTCERT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/supabase/prod-ca-2021 (1).crt"

# Test connection
psql "postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=verify-ca" -c "SELECT version();"
```

### Python Testing

#### Test with sslmode=require:
```python
import asyncpg

async def test_connection():
    conn = await asyncpg.connect(
        "postgresql://postgres:YOUR_PASSWORD@db.your-project-id.supabase.co:6543/postgres?sslmode=require"
    )
    version = await conn.fetchval("SELECT version()")
    print(f"Connected! PostgreSQL version: {version}")
    await conn.close()

# Run test
import asyncio
asyncio.run(test_connection())
```

#### Test with certificate verification:
```python
import asyncpg
import ssl
import base64

async def test_connection_with_cert():
    # Decode certificate from base64
    cert_b64 = "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0t..."
    cert_pem = base64.b64decode(cert_b64).decode('utf-8')

    # Write to temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as f:
        f.write(cert_pem)
        cert_path = f.name

    # Create SSL context
    ssl_context = ssl.create_default_context(cafile=cert_path)

    # Connect with certificate verification
    conn = await asyncpg.connect(
        host="db.jlesbkscprldariqcbvt.supabase.co",
        port=6543,
        user="postgres",
        password="YOUR_PASSWORD",
        database="postgres",
        ssl=ssl_context
    )

    version = await conn.fetchval("SELECT version()")
    print(f"Connected with cert verification! PostgreSQL version: {version}")
    await conn.close()

# Run test
import asyncio
asyncio.run(test_connection_with_cert())
```

---

## 📊 SSL Configuration Comparison

### For Production on Render:

| Configuration | SSL Encryption | Cert Verification | Complexity | Recommended |
|---------------|----------------|-------------------|------------|-------------|
| **sslmode=require** | ✅ Yes | ❌ No | 🟢 Low | ✅ **Yes** (default) |
| **sslmode=verify-ca** | ✅ Yes | ✅ Yes | 🟡 Medium | ✅ For high-security |
| **sslmode=verify-full** | ✅ Yes | ✅ Yes + Hostname | 🟡 Medium | ✅ For compliance |

---

## 🔐 Security Best Practices

### Current Setup (sslmode=require)
✅ **Good for:**
- Standard production deployments
- Most SaaS applications
- E-commerce platforms
- Internal tools

### Enhanced Setup (sslmode=verify-ca)
✅✅ **Required for:**
- Financial services applications
- Healthcare (HIPAA compliance)
- Payment processing (PCI-DSS)
- Government contracts
- Enterprise security policies

---

## 📝 Certificate Information

**Certificate Details:**
- **Name:** Supabase Root 2021 CA
- **Issuer:** Supabase Inc
- **Location:** Delaware, US
- **Valid From:** 2021-04-28
- **Valid Until:** 2031-04-26
- **Format:** X.509 PEM

**Certificate Fingerprint:**
```
SHA256: (verify in Supabase dashboard)
```

---

## 🔄 Certificate Rotation

Supabase manages certificate rotation automatically. If the certificate is updated:

1. Download new certificate from Supabase Dashboard
2. Encode to base64:
   ```bash
   base64 -i supabase/new-cert.crt | tr -d '\n'
   ```
3. Update `SUPABASE_SSL_CERT_B64` in Render Dashboard
4. Redeploy services

---

## 🆘 Troubleshooting

### Error: "certificate verify failed"

**Cause:** Certificate not found or incorrect path

**Solution:**
```bash
# Check if certificate was created during pre-deploy
render logs toolboxai-backend --tail 50 | grep "SSL certificate"

# Should see:
# "Setting up Supabase SSL certificate..."
# "SSL certificate configured at /opt/render/project/.postgresql/root.crt"
```

### Error: "sslmode value 'verify-ca' invalid"

**Cause:** Old PostgreSQL driver version

**Solution:**
Update asyncpg or psycopg2:
```bash
pip install --upgrade asyncpg
# or
pip install --upgrade psycopg2-binary
```

### Error: "PGSSLROOTCERT environment variable not set"

**Cause:** Using sslmode=verify-ca without specifying certificate path

**Solution:**
Add `sslrootcert` parameter to DATABASE_URL:
```bash
postgresql://...?sslmode=verify-ca&sslrootcert=/path/to/cert.crt
```

---

## ✅ Recommendations

### For Most Users: Use sslmode=require (Current Setup)
- ✅ SSL/TLS encryption enabled
- ✅ Simple configuration
- ✅ Reliable across all platforms
- ✅ **No additional setup needed!**

### For High-Security Requirements: Upgrade to verify-ca
- Follow "Option 2: Enhanced SSL" instructions above
- Add certificate to environment variables
- Update DATABASE_URL with verify-ca and sslrootcert

### Performance Impact
- **sslmode=require**: No performance impact
- **sslmode=verify-ca**: Negligible (< 1ms per connection)
- **sslmode=verify-full**: Negligible (< 1ms per connection)

---

**Current Status:** ✅ SSL encryption enabled with sslmode=require
**Enhanced Security:** Optional - follow instructions above if needed
**Certificate Location:** `supabase/prod-ca-2021 (1).crt`
**Last Updated:** 2025-11-07
