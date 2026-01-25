# Regional to Global Load Balancer Migration - 2026-01-21

## Why the Regional Load Balancer Failed

### The Requirement

Serve static frontend files from GCS bucket (`gs://diagramik-frontend`) and route `/api/*` requests to Cloud Run backend.

### The Problem

The original setup used a **Regional External Application Load Balancer** (europe-west4). Regional load balancers **do not support GCS backend buckets** - this feature is only available with **Global External Application Load Balancers**.

Regional LB limitations:

- Cannot use `backend-buckets` (GCS)
- Can only use `backend-services` with instance groups or NEGs
- Limited to single region

### The Solution

Migrated to a Global External Application Load Balancer which supports:

- Backend buckets for GCS static hosting
- Backend services for Cloud Run (via serverless NEGs)
- Path-based routing between the two
- Cloud CDN integration

## Migration Steps

### 1. Create Global Static IP

```bash
gcloud compute addresses create diagramik-global-ip --global --ip-version=IPV4
# Result: 35.244.175.228
```

### 2. Create Backend Bucket for GCS Frontend

```bash
gcloud compute backend-buckets create diagramik-frontend-bucket \
  --gcs-bucket-name=diagramik-frontend \
  --enable-cdn
```

### 3. Create Serverless NEG for Cloud Run

```bash
gcloud compute network-endpoint-groups create diagramik-serverless-neg \
  --region=europe-west4 \
  --network-endpoint-type=serverless \
  --cloud-run-service=diagramik
```

### 4. Create Global Backend Service

```bash
# Note: Don't specify --protocol for serverless NEGs
gcloud compute backend-services create diagramik-api-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED

gcloud compute backend-services add-backend diagramik-api-backend \
  --global \
  --network-endpoint-group=diagramik-serverless-neg \
  --network-endpoint-group-region=europe-west4
```

### 5. Create URL Map with Routing Rules

```bash
# Default to frontend bucket
gcloud compute url-maps create diagramik-global-lb \
  --default-backend-bucket=diagramik-frontend-bucket

# Add /api/* path rule to Cloud Run
gcloud compute url-maps add-path-matcher diagramik-global-lb \
  --path-matcher-name=api-matcher \
  --default-backend-bucket=diagramik-frontend-bucket \
  --backend-service-path-rules="/api/*=diagramik-api-backend"
```

### 6. Create Global SSL Certificate

```bash
gcloud compute ssl-certificates create diagramik-global-cert \
  --domains=diagramik.com,www.diagramik.com \
  --global
```

### 7. Create HTTPS Proxy and Forwarding Rule

```bash
gcloud compute target-https-proxies create diagramik-global-https-proxy \
  --url-map=diagramik-global-lb \
  --ssl-certificates=diagramik-global-cert \
  --global

gcloud compute forwarding-rules create diagramik-global-https-rule \
  --global \
  --target-https-proxy=diagramik-global-https-proxy \
  --address=diagramik-global-ip \
  --ports=443 \
  --load-balancing-scheme=EXTERNAL_MANAGED
```

### 8. Create HTTP to HTTPS Redirect

```bash
# Create redirect URL map
gcloud compute url-maps import diagramik-http-redirect --source=/dev/stdin --global << 'EOF'
name: diagramik-http-redirect
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
EOF

gcloud compute target-http-proxies create diagramik-global-http-proxy \
  --url-map=diagramik-http-redirect --global

gcloud compute forwarding-rules create diagramik-global-http-rule \
  --global \
  --target-http-proxy=diagramik-global-http-proxy \
  --address=diagramik-global-ip \
  --ports=80 \
  --load-balancing-scheme=EXTERNAL_MANAGED
```

### 9. Update DNS Records

```bash
gcloud dns record-sets update diagramik.com. --zone=diagramik-com \
  --type=A --ttl=300 --rrdatas="35.244.175.228"

gcloud dns record-sets update www.diagramik.com. --zone=diagramik-com \
  --type=A --ttl=300 --rrdatas="35.244.175.228"
```

## Final Architecture

```
                                    Global Load Balancer (35.244.175.228)
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                   │
              HTTP (port 80)                                     HTTPS (port 443)
                    │                                                   │
                    ▼                                                   ▼
           301 Redirect to HTTPS                              URL Map Routing
                                                                       │
                                              ┌────────────────────────┴────────────────────────┐
                                              │                                                 │
                                        Default (/)                                       /api/*
                                              │                                                 │
                                              ▼                                                 ▼
                                    Backend Bucket                                    Backend Service
                                              │                                                 │
                                              ▼                                                 ▼
                                gs://diagramik-frontend                              Cloud Run (diagramik)
                                    (Static Files)                                    (Django API)
```

## Resources Created

| Resource Type   | Name                         | Purpose                     |
| --------------- | ---------------------------- | --------------------------- |
| Global Address  | diagramik-global-ip          | Static IP (35.244.175.228)  |
| Backend Bucket  | diagramik-frontend-bucket    | GCS static hosting with CDN |
| Serverless NEG  | diagramik-serverless-neg     | Cloud Run endpoint          |
| Backend Service | diagramik-api-backend        | API traffic routing         |
| URL Map         | diagramik-global-lb          | Path-based routing          |
| URL Map         | diagramik-http-redirect      | HTTP→HTTPS redirect         |
| SSL Certificate | diagramik-global-cert        | Managed TLS cert            |
| HTTPS Proxy     | diagramik-global-https-proxy | TLS termination             |
| HTTP Proxy      | diagramik-global-http-proxy  | HTTP redirect               |
| Forwarding Rule | diagramik-global-https-rule  | HTTPS frontend              |
| Forwarding Rule | diagramik-global-http-rule   | HTTP frontend               |

## Old Regional Resources (Can Be Cleaned Up)

- `diagramik-lb` (regional URL map)
- `diagramik-backend` (regional backend service)
- `diagramik-lb-target-proxy` (regional HTTPS proxy)
- `frontend` (regional forwarding rule)
- `diagramik-endpoint-group` (regional NEG)
- `diagramik-certificate-v2` (Certificate Manager cert)
- `diagramik-ip` (regional static IPs)
