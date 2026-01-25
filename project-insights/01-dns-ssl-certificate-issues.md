# DNS and SSL Certificate Issues - 2026-01-21

## Initial Problem

`curl diagramik.com` returned "could not resolve host" - the domain was completely unreachable.

## Root Causes

### 1. Missing DNS A Record

The Cloud DNS zone `diagramik-com` existed but contained only NS and SOA records. No A record was pointing to the load balancer IP.

**Fix:** Added A record via:

```bash
gcloud dns record-sets create diagramik.com. --zone=diagramik-com --type=A --ttl=300 --rrdatas="34.12.232.96"
```

### 2. Missing SSL Certificate DNS Authorization CNAME

The SSL certificate (managed by Google Certificate Manager) was stuck in `PROVISIONING` state with `AUTHORIZATION_ISSUE`. The certificate validation requires a CNAME record for domain ownership verification.

**Expected CNAME:**

```
_acme-challenge_qchnhgshrbgyighz.diagramik.com → eae3b9fe-5bed-450d-be1c-fc8ca0bdd25f.0.europe-west4.authorize.certificatemanager.goog.
```

**Fix:** Added the CNAME record:

```bash
gcloud dns record-sets create "_acme-challenge_qchnhgshrbgyighz.diagramik.com." \
  --zone=diagramik-com --type=CNAME --ttl=300 \
  --rrdatas="eae3b9fe-5bed-450d-be1c-fc8ca0bdd25f.0.europe-west4.authorize.certificatemanager.goog."
```

### 3. Certificate Manager Not Retrying Validation

After adding the CNAME, the certificate remained in FAILED state because Certificate Manager didn't automatically retry validation. The `attemptTime` showed an old timestamp from before the CNAME was added.

**Attempted fixes that didn't work:**

- Updating certificate labels to force refresh
- Updating DNS authorization labels

**Fix that worked:** Created a new certificate with the same DNS authorization:

```bash
gcloud certificate-manager certificates create diagramik-certificate-v2 \
  --location=europe-west4 \
  --domains="diagramik.com" \
  --dns-authorizations=dns-authz-diagramik-com
```

Then updated the target HTTPS proxy to use the new certificate:

```bash
gcloud compute target-https-proxies update diagramik-lb-target-proxy \
  --region=europe-west4 \
  --certificate-manager-certificates=diagramik-certificate-v2
```

### 4. Incorrect Bucket Website Configuration

The frontend bucket `gs://diagramik-frontend` had `mainPageSuffix` set to "diagramik.com" instead of "index.html".

**Fix:**

```bash
gsutil web set -m index.html -e 404.html gs://diagramik-frontend
```

## Verification Commands

```bash
# Check DNS resolution
curl -s "https://dns.google/resolve?name=diagramik.com&type=A"

# Check certificate status
gcloud certificate-manager certificates describe diagramik-certificate-v2 \
  --location=europe-west4 --format="value(managed.state)"

# Test TLS handshake
curl -v https://diagramik.com
```

## Lessons Learned

1. **Always verify DNS records exist** - Cloud DNS zones can exist without any useful records
1. **Certificate Manager DNS authorization requires manual CNAME setup** - It's not automatic
1. **Certificate Manager retry is slow** - Creating a new certificate is faster than waiting for retry
1. **Use dns.google API to verify DNS propagation** - Local DNS cache can be misleading
