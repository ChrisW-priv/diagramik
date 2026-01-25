# GCP Global Load Balancer Terraform Module

This Terraform module provisions a complete GCP Global HTTP(S) Load Balancer with path-based routing, designed to serve a frontend application from Google Cloud Storage and route API requests to a Cloud Run service.

## Overview

This module creates a production-ready global load balancing infrastructure that:

- Routes frontend static assets from a GCS bucket (with optional CDN)
- Routes API traffic (by path prefix) to a Cloud Run backend service
- Provisions a global static IP address
- Manages SSL certificates automatically via Google-managed certificates
- Implements automatic HTTP to HTTPS redirect
- Supports multiple domains for SSL certificate

## Architecture

The module creates the following resource dependency structure:

```
Global IP Address
    |
    +-- HTTPS Forwarding Rule (port 443)
    |       |
    |       +-- HTTPS Target Proxy
    |               |
    |               +-- URL Map (path-based routing)
    |               |       |
    |               |       +-- Backend Bucket (GCS) --> Frontend
    |               |       +-- Backend Service (Cloud Run) --> API
    |               |
    |               +-- Managed SSL Certificate
    |
    +-- HTTP Forwarding Rule (port 80)
            |
            +-- HTTP Target Proxy
                    |
                    +-- HTTP Redirect URL Map
```

**Routing Logic:**

- Requests matching `api_path_prefix` (default: `/api/*`) → Cloud Run backend service
- All other requests → GCS backend bucket (frontend static files)

## Requirements

| Name      | Version |
| --------- | ------- |
| terraform | >= 1.0  |
| google    | >= 4.0  |

**Prerequisites:**

- GCP project with Compute Engine API enabled (module handles this automatically)
- Existing GCS bucket for frontend static files
- Existing Cloud Run service for API backend
- Domain DNS configured to point to the load balancer's IP address

## Resources Created

This module provisions the following GCP resources:

- `google_project_service.compute` - Enables Compute Engine API
- `google_compute_global_address` - Global static IPv4 address
- `google_compute_backend_bucket` - Backend for GCS-hosted frontend
- `google_compute_region_network_endpoint_group` - Serverless NEG for Cloud Run
- `google_compute_backend_service` - Backend service for Cloud Run API
- `google_compute_url_map` - Path-based routing configuration
- `google_compute_managed_ssl_certificate` - Auto-managed SSL certificate
- `google_compute_target_https_proxy` - HTTPS proxy
- `google_compute_global_forwarding_rule` (HTTPS) - HTTPS traffic forwarding
- `google_compute_url_map` (redirect) - HTTP to HTTPS redirect
- `google_compute_target_http_proxy` - HTTP proxy for redirect
- `google_compute_global_forwarding_rule` (HTTP) - HTTP traffic forwarding

## Usage

### Basic Example

```hcl
module "global_lb" {
  source = "./modules/global-lb"

  google_project_id         = "my-gcp-project-id"
  application_name          = "myapp"
  domain                    = "example.com"
  frontend_bucket_name      = "myapp-frontend-bucket"
  cloudrun_service_name     = "myapp-api-service"
  cloudrun_service_location = "us-central1"
}
```

### Advanced Example with Multiple Domains and Custom API Path

```hcl
module "global_lb" {
  source = "./modules/global-lb"

  google_project_id         = "my-gcp-project-id"
  application_name          = "myapp"
  domain                    = "example.com"
  additional_domains        = ["www.example.com", "app.example.com"]
  frontend_bucket_name      = "myapp-frontend-bucket"
  cloudrun_service_name     = "myapp-api-service"
  cloudrun_service_location = "us-central1"
  enable_cdn                = true
  api_path_prefix           = "/backend/*"
}

# Output the IP address for DNS configuration
output "load_balancer_ip" {
  value = module.global_lb.global_ip_address
}
```

## Variables

### Required Variables

| Name                        | Type     | Description                                                              |
| --------------------------- | -------- | ------------------------------------------------------------------------ |
| `google_project_id`         | `string` | The GCP project ID where resources will be created                       |
| `application_name`          | `string` | The name of the application, used as prefix for all resource names       |
| `domain`                    | `string` | Primary domain for the application (included in SSL certificate)         |
| `frontend_bucket_name`      | `string` | Name of the existing GCS bucket containing frontend static files         |
| `cloudrun_service_name`     | `string` | Name of the existing Cloud Run service for API backend                   |
| `cloudrun_service_location` | `string` | GCP region where the Cloud Run service is deployed (e.g., `us-central1`) |

### Optional Variables

| Name                 | Type           | Default    | Description                                                                      |
| -------------------- | -------------- | ---------- | -------------------------------------------------------------------------------- |
| `additional_domains` | `list(string)` | `[]`       | Additional domains to include in the SSL certificate (e.g., `www` subdomain)     |
| `enable_cdn`         | `bool`         | `true`     | Enable Cloud CDN for the frontend bucket to improve performance and reduce costs |
| `api_path_prefix`    | `string`       | `"/api/*"` | Path prefix pattern for routing API requests to Cloud Run backend                |

## Outputs

| Name                   | Description                                                                          |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `global_ip_address`    | The global static IP address - configure your DNS A/AAAA records to point to this IP |
| `global_ip_name`       | The GCP resource name of the global static IP address                                |
| `ssl_certificate_name` | The name of the managed SSL certificate resource                                     |
| `url_map_name`         | The name of the URL map resource used for routing                                    |
| `backend_bucket_name`  | The name of the backend bucket resource for the frontend                             |
| `backend_service_name` | The name of the API backend service resource                                         |

## Important Notes

### SSL Certificate Provisioning

Google-managed SSL certificates can take 15-60 minutes to provision after initial deployment. During this time:

1. The load balancer will not serve HTTPS traffic
1. Certificate status can be checked with: `gcloud compute ssl-certificates describe <cert-name> --global`
1. DNS must be properly configured pointing to the global IP address before certificate provisioning completes

### DNS Configuration

After applying this module:

1. Note the `global_ip_address` output value
1. Create DNS A records for all domains (primary and additional) pointing to this IP
1. Wait for DNS propagation (typically 5-30 minutes)
1. SSL certificate will provision automatically once DNS is validated

### State Impact Considerations

**Destructive Operations:**

- Changing `application_name` will recreate ALL resources (causing downtime)
- Changing `domain` or modifying `additional_domains` will recreate the SSL certificate
- Modifying `cloudrun_service_location` will recreate the Network Endpoint Group

**Non-Destructive Operations:**

- Changing `enable_cdn` updates the backend bucket in-place
- Modifying `api_path_prefix` updates the URL map in-place
- Changing `frontend_bucket_name` or `cloudrun_service_name` updates backend references in-place

### Resource Dependencies

This module assumes the following resources already exist:

- GCS bucket specified in `frontend_bucket_name`
- Cloud Run service specified in `cloudrun_service_name` in the specified region

The module will fail if these resources don't exist or aren't accessible in the specified project.

### CDN and Caching

When `enable_cdn = true` (default):

- Static assets from GCS will be cached globally at Google's edge locations
- Cache behavior is controlled by Cache-Control headers on objects in the bucket
- First request to each asset may be slower; subsequent requests will be served from cache
- Invalidating cache requires updating object metadata or using cache invalidation API

## Example DNS Configuration

After deployment, configure your DNS provider with A records:

```
example.com.        300 IN A    <global_ip_address output>
www.example.com.    300 IN A    <global_ip_address output>
app.example.com.    300 IN A    <global_ip_address output>
```

Or use CNAME records pointing to a single A record:

```
@                   300 IN A     <global_ip_address output>
www                 300 IN CNAME example.com.
app                 300 IN CNAME example.com.
```

## Troubleshooting

### SSL Certificate Not Provisioning

Check certificate status:

```bash
gcloud compute ssl-certificates describe <application_name>-global-cert --global --project <project_id>
```

Common issues:

- DNS not pointing to the load balancer IP yet
- Domain validation pending (can take up to 60 minutes)
- CAA DNS records blocking Google certificate authority

### 404 Errors for Frontend

Verify:

- GCS bucket exists and contains index.html (or appropriate files)
- Bucket is readable by the load balancer
- Backend bucket configuration points to correct bucket name

### API Requests Not Reaching Cloud Run

Verify:

- Cloud Run service exists and is deployed
- Service allows unauthenticated invocations (or IAM is properly configured)
- API path matches the `api_path_prefix` pattern
- Check Cloud Run logs for incoming requests

## License

This module is provided as-is for use within your infrastructure.
