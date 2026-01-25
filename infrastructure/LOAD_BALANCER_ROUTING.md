# Load Balancer Path-Based Routing Configuration

## Overview

The global load balancer module has been refactored to support flexible path-based routing to multiple CloudRun backend services. This allows different URL paths to be routed to different backend services while maintaining a unified external API surface.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Global Load Balancer                      │
│                   (diagramik.com / HTTPS)                    │
└──────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   /api/*              /mcp/*           /* (default)
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Django     │   │     MCP      │   │   Frontend   │
│  Monolith    │   │   Diagrams   │   │  GCS Bucket  │
│ (CloudRun)   │   │  (CloudRun)  │   │    (CDN)     │
└──────────────┘   └──────────────┘   └──────────────┘
```

## Key Features

### 1. Multiple Backend Support

The load balancer now supports routing to multiple CloudRun services through the `cloudrun_backends` variable:

```hcl
cloudrun_backends = {
  api = {
    service_name = "django-service"
    location     = "us-central1"
    path_prefix  = "/api/*"
    priority     = 1
  }
  mcp = {
    service_name = "mcp-service"
    location     = "us-central1"
    path_prefix  = "/mcp/*"
    priority     = 2
  }
}
```

### 2. Priority-Based Path Matching

Each backend has a `priority` field (lower number = higher priority). This ensures predictable path matching when multiple patterns could match the same URL.

**Example:**

- Priority 1: `/api/*` - Matches first
- Priority 2: `/mcp/*` - Matches second
- Default: GCS bucket for all other paths

### 3. Security: Load Balancer-Only Access

The MCP service is configured with:

```hcl
ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
```

This ensures:

- Direct access to the MCP CloudRun service is **blocked**
- Only traffic routed through the global load balancer can reach the service
- The MCP service is **only** accessible via `diagramik.com/mcp/*` paths

### 4. Backward Compatibility

The module maintains backward compatibility with legacy single-backend configuration through deprecated variables:

- `cloudrun_service_name`
- `cloudrun_service_location`
- `api_path_prefix`

If `cloudrun_backends` is not provided, the module falls back to legacy behavior.

## Configuration

### Adding a New Backend Service

To add a new CloudRun service to the load balancer:

1. **Create the CloudRun service** (via module or resource)

1. **Add to cloudrun_backends map** in `main.tf`:

```hcl
module "global-lb" {
  source = "./modules/global-lb"
  # ... other config ...

  cloudrun_backends = {
    api = { ... }
    mcp = { ... }

    # Add new backend
    new-service = {
      service_name = module.new-service.service_name
      location     = module.new-service.location
      path_prefix  = "/new-path/*"
      priority     = 3  # Lower number = higher priority
    }
  }
}
```

3. **Configure service ingress** (recommended):

```hcl
module "new-service" {
  source = "./modules/cloudrun-service"
  # ... other config ...

  # Restrict to load balancer traffic only
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
}
```

### Path Prefix Format

Path prefixes follow Google Cloud URL Map syntax:

- `/api/*` - Matches `/api/` and all sub-paths
- `/mcp/*` - Matches `/mcp/` and all sub-paths
- `/exact-path` - Matches only this exact path

**Important:** Paths are evaluated in priority order. More specific paths should have lower priority numbers.

## Resources Created

For each backend in `cloudrun_backends`, the module creates:

1. **Network Endpoint Group (NEG)**

   - Name: `{application_name}-{backend_key}-neg`
   - Type: Serverless (CloudRun)
   - Region: Per backend configuration

1. **Backend Service**

   - Name: `{application_name}-{backend_key}-backend`
   - Load balancing scheme: EXTERNAL_MANAGED
   - Protocol: HTTPS

1. **URL Map Path Rules**

   - Dynamically generated based on priority
   - Routes matching paths to corresponding backend service

## State Impact

### Migration from Legacy Configuration

**WARNING:** Migrating from legacy single-backend to multi-backend configuration will cause resource recreation.

**State Impact:**

- **Destroyed:** `google_compute_region_network_endpoint_group.cloudrun_neg`
- **Destroyed:** `google_compute_backend_service.api`
- **Created:** `google_compute_region_network_endpoint_group.cloudrun_neg["api"]`
- **Created:** `google_compute_backend_service.cloudrun_backends["api"]`

**Downtime:** ~30-60 seconds during backend service recreation

**Migration Steps:**

1. **Review planned changes:**

   ```bash
   task infra:plan
   ```

1. **Option A: Zero-downtime migration using moved blocks**

   Add to `modules/global-lb/main.tf`:

   ```hcl
   moved {
     from = google_compute_region_network_endpoint_group.cloudrun_neg
     to   = google_compute_region_network_endpoint_group.cloudrun_neg["api"]
   }

   moved {
     from = google_compute_backend_service.api
     to   = google_compute_backend_service.cloudrun_backends["api"]
   }
   ```

1. **Option B: Accept brief downtime**

   ```bash
   task infra:apply
   ```

### Adding New Backends

Adding new entries to `cloudrun_backends` only creates new resources - no existing resources are modified or destroyed.

**State Impact:** Zero impact on existing backends

## Outputs

### New Outputs

- `backend_services` - Map of all backend service names

  ```hcl
  {
    "api" = "diagramik-api-backend"
    "mcp" = "diagramik-mcp-backend"
  }
  ```

- `backend_negs` - Map of all Network Endpoint Group IDs

  ```hcl
  {
    "api" = "projects/.../regions/.../networkEndpointGroups/diagramik-api-neg"
    "mcp" = "projects/.../regions/.../networkEndpointGroups/diagramik-mcp-neg"
  }
  ```

### Deprecated Outputs

- `backend_service_name` - Returns only the "api" backend name for backward compatibility

## Security Considerations

### CloudRun Ingress Settings

| Setting                                  | Use Case           | Access                                  |
| ---------------------------------------- | ------------------ | --------------------------------------- |
| `INGRESS_TRAFFIC_ALL`                    | Public service     | Anyone can access CloudRun URL directly |
| `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` | Load balancer only | **Recommended for services behind LB**  |
| `INGRESS_TRAFFIC_INTERNAL_ONLY`          | VPC only           | Same project VPC traffic only           |

**Best Practice:** Always use `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` for services exposed through the global load balancer to prevent direct access bypass.

### IAM Policies

The load balancer automatically handles authentication to CloudRun services. No additional IAM bindings are required.

## Testing

### Verify Path Routing

```bash
# Test API backend
curl https://diagramik.com/api/v1/diagrams/

# Test MCP backend (only accessible via LB)
curl https://diagramik.com/mcp/health

# Test direct access (should fail for MCP with proper ingress)
curl https://mcp-service-hash-uc.a.run.app/health
# Expected: 403 Forbidden
```

### Verify Load Balancer Configuration

```bash
# View URL map configuration
gcloud compute url-maps describe diagramik-global-lb \
  --global \
  --project=your-project-id

# View backend services
gcloud compute backend-services list \
  --global \
  --project=your-project-id

# View NEGs
gcloud compute network-endpoint-groups list \
  --project=your-project-id
```

## Troubleshooting

### Issue: 502 Bad Gateway

**Cause:** CloudRun service is not ready or ingress is misconfigured

**Solution:**

1. Verify CloudRun service is running:

   ```bash
   gcloud run services describe SERVICE_NAME --region=REGION
   ```

1. Check ingress settings match load balancer configuration

1. Verify NEG points to correct service

### Issue: 404 Not Found

**Cause:** Path pattern doesn't match request URL

**Solution:**

1. Review path_prefix patterns in `cloudrun_backends`
1. Check priority ordering
1. Verify URL map configuration:
   ```bash
   gcloud compute url-maps describe diagramik-global-lb --global
   ```

### Issue: Direct CloudRun URL accessible

**Cause:** Ingress setting allows public access

**Solution:**
Change ingress to `INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER`:

```hcl
module "service" {
  # ...
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
}
```

## Example: Full Configuration

```hcl
# main.tf

module "global-lb" {
  source = "./modules/global-lb"

  google_project_id    = var.google_project_id
  application_name     = "diagramik"
  domain               = "diagramik.com"
  additional_domains   = ["www.diagramik.com"]
  frontend_bucket_name = module.frontend-bucket.bucket_name
  enable_cdn           = true

  cloudrun_backends = {
    # Django API - Priority 1 (highest)
    api = {
      service_name = module.django.service_name
      location     = module.django.location
      path_prefix  = "/api/*"
      priority     = 1
    }

    # MCP Diagrams - Priority 2
    mcp = {
      service_name = module.mcp-service.service_name
      location     = module.mcp-service.location
      path_prefix  = "/mcp/*"
      priority     = 2
    }

    # Admin interface - Priority 3
    admin = {
      service_name = module.admin.service_name
      location     = module.admin.location
      path_prefix  = "/admin/*"
      priority     = 3
    }
  }
}
```

## Future Enhancements

Potential improvements to consider:

1. **Per-backend CDN configuration** - Allow CDN settings per backend
1. **Custom health checks** - Configure health check paths per backend
1. **Traffic splitting** - Support A/B testing with traffic percentages
1. **Region-based routing** - Route to different backends based on client location
1. **Rate limiting** - Per-backend rate limiting configuration
1. **Custom headers** - Add/remove headers per backend route
