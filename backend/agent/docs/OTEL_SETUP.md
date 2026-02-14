# OpenTelemetry Tracing Setup Guide

This guide covers configuring OpenTelemetry inspection tools for the diagram-agent service, both for local development and production (GCP with Tempo + Grafana).

## Architecture Overview

```
┌─────────────────┐     OTLP/HTTP      ┌──────────────────┐
│  diagram-agent  │ ──────────────────►│  OTel Collector  │
│   (Python)      │    :4318           │                  │
└─────────────────┘                    └────────┬─────────┘
                                                │
                                                ▼
                                       ┌──────────────────┐
                                       │  Grafana Tempo   │
                                       │   (Traces DB)    │
                                       └────────┬─────────┘
                                                │
                                                ▼
                                       ┌──────────────────┐
                                       │     Grafana      │
                                       │  (Visualization) │
                                       └──────────────────┘
```

______________________________________________________________________

## Part 1: Local Development Setup

### Option A: Grafana LGTM Docker Image (Recommended)

The simplest approach uses Grafana's all-in-one `docker-otel-lgtm` image which includes:

- **L**oki (logs)
- **G**rafana (visualization)
- **T**empo (traces)
- **M**imir (metrics)
- OpenTelemetry Collector (pre-configured)

#### Quick Start

```bash
# Run the LGTM stack
docker run -d --name lgtm \
  -p 3000:3000 \
  -p 4317:4317 \
  -p 4318:4318 \
  grafana/otel-lgtm:latest
```

#### With Data Persistence

```bash
docker run -d --name lgtm \
  -p 3000:3000 \
  -p 4317:4317 \
  -p 4318:4318 \
  -v lgtm-data:/data \
  grafana/otel-lgtm:latest
```

#### Access

- **Grafana UI**: http://localhost:3000 (admin/admin)
- **OTLP gRPC**: localhost:4317
- **OTLP HTTP**: localhost:4318

### Option B: Docker Compose Full Stack

For more control, use a dedicated docker-compose setup:

```yaml
# docker-compose.otel.yaml
version: "3.9"

services:
  tempo:
    image: grafana/tempo:latest
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo
    ports:
      - "3200:3200"   # Tempo API
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
      - GF_AUTH_DISABLE_LOGIN_FORM=true
    volumes:
      - ./grafana-datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml
    ports:
      - "3000:3000"
    depends_on:
      - tempo

volumes:
  tempo-data:
```

#### Tempo Configuration (`tempo.yaml`)

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal

metrics_generator:
  registry:
    external_labels:
      source: tempo
  storage:
    path: /var/tempo/generator/wal
```

#### Grafana Datasources (`grafana-datasources.yaml`)

```yaml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    isDefault: true
    editable: false
```

#### Run

```bash
docker compose -f docker-compose.otel.yaml up -d
```

### Configure the Agent for Local Development

Set environment variables before running the agent:

```bash
# Enable OTLP export to local stack
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_DEBUG=1  # Optional: also log spans to console

# Run the agent
task dev
```

Or in your `.env` file:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_DEBUG=1
```

______________________________________________________________________

## Part 2: Production Setup (GCP + Tempo + Grafana)

### Infrastructure Components

1. **GCS Bucket** - Stores trace data
1. **Tempo** - Deployed on Cloud Run or GKE
1. **Grafana** - Deployed on Cloud Run or GKE
1. **Service Account** - For GCS access

### Step 1: Create GCS Bucket

```bash
# Create bucket for trace storage
gsutil mb -l us-central1 gs://diagramik-traces

# Set lifecycle policy (optional - delete old traces after 30 days)
cat > lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 30}
    }
  ]
}
EOF
gsutil lifecycle set lifecycle.json gs://diagramik-traces
```

### Step 2: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create tempo-traces \
  --display-name="Tempo Trace Storage"

# Grant GCS permissions
gsutil iam ch \
  serviceAccount:tempo-traces@PROJECT_ID.iam.gserviceaccount.com:objectAdmin \
  gs://diagramik-traces
```

Required IAM permissions:

- `storage.objects.create`
- `storage.objects.delete`
- `storage.objects.get`
- `storage.buckets.get`
- `storage.objects.list`

### Step 3: Tempo Configuration for GCS

```yaml
# tempo-gcs.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

storage:
  trace:
    backend: gcs
    gcs:
      bucket_name: diagramik-traces
      prefix: traces/
      # Optional performance tuning
      chunk_buffer_size: 10485760  # 10MB
      list_blocks_concurrency: 3
      hedge_requests_at: 500ms
      hedge_requests_up_to: 2

compactor:
  compaction:
    block_retention: 720h  # 30 days

metrics_generator:
  registry:
    external_labels:
      source: tempo
      environment: production
  storage:
    path: /var/tempo/generator/wal
    remote_write:
      - url: http://prometheus:9090/api/v1/write
```

### Step 4: Terraform Configuration

Add to your existing infrastructure:

```hcl
# infrastructure/tempo.tf

resource "google_storage_bucket" "traces" {
  name          = "diagramik-traces"
  location      = var.region
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  uniform_bucket_level_access = true
}

resource "google_service_account" "tempo" {
  account_id   = "tempo-traces"
  display_name = "Tempo Trace Storage"
}

resource "google_storage_bucket_iam_member" "tempo_object_admin" {
  bucket = google_storage_bucket.traces.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.tempo.email}"
}

resource "google_cloud_run_v2_service" "tempo" {
  name     = "tempo"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.tempo.email

    containers {
      image = "grafana/tempo:latest"
      args  = ["-config.file=/etc/tempo/tempo.yaml"]

      ports {
        container_port = 3200
      }

      volume_mounts {
        name       = "config"
        mount_path = "/etc/tempo"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }
    }

    volumes {
      name = "config"
      secret {
        secret = google_secret_manager_secret.tempo_config.secret_id
      }
    }
  }
}

resource "google_secret_manager_secret" "tempo_config" {
  secret_id = "tempo-config"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "tempo_config" {
  secret      = google_secret_manager_secret.tempo_config.id
  secret_data = file("${path.module}/tempo-gcs.yaml")
}
```

### Step 5: Configure Agent for Production

Update `telemetry.py` to use the production endpoint:

```python
# In production, set this environment variable:
# OTEL_EXPORTER_OTLP_ENDPOINT=https://tempo.your-domain.com
```

Or configure via Cloud Run environment:

```hcl
# In your Cloud Run service for django-monolith
resource "google_cloud_run_v2_service" "monolith" {
  # ... existing config ...

  template {
    containers {
      # ... existing config ...

      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = "http://tempo:4318"  # Internal service URL
      }
    }
  }
}
```

### Step 6: Add Load Balancer Route (Optional)

If Tempo needs external access for the Grafana UI:

```hcl
# Add to your URL map
resource "google_compute_url_map" "default" {
  # ... existing config ...

  host_rule {
    hosts        = ["tempo.your-domain.com"]
    path_matcher = "tempo"
  }

  path_matcher {
    name            = "tempo"
    default_service = google_compute_backend_service.tempo.id
  }
}
```

______________________________________________________________________

## Part 3: Grafana Dashboard Configuration

### Connect Grafana to Tempo

1. Open Grafana (http://localhost:3000 or your production URL)
1. Go to **Configuration** > **Data Sources**
1. Click **Add data source**
1. Select **Tempo**
1. Configure:
   - **URL**: `http://tempo:3200` (Docker) or your Tempo endpoint
   - **Authentication**: None (internal) or Basic Auth (production)

### Exploring Traces

1. Go to **Explore**
1. Select **Tempo** data source
1. Use **Search** tab to find traces by:
   - Service name: `diagram-agent`
   - Span name: `agent.generate_diagram`
   - Duration: `> 1s`
   - Tags: `agent.has_history=true`

### Example TraceQL Queries

```
# Find all diagram generation traces
{resource.service.name="diagram-agent"}

# Find slow traces (> 5 seconds)
{resource.service.name="diagram-agent"} | duration > 5s

# Find traces with history
{resource.service.name="diagram-agent" && span.agent.has_history=true}

# Find failed traces
{resource.service.name="diagram-agent" && status=error}
```

______________________________________________________________________

## Part 4: Verifying the Setup

### Local Verification

```bash
# 1. Start LGTM stack
docker run -d --name lgtm -p 3000:3000 -p 4318:4318 grafana/otel-lgtm

# 2. Set environment
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_DEBUG=1

# 3. Run agent (generates traces)
cd backend && task dev

# 4. Make a diagram request
curl -X POST http://localhost:8000/api/v1/diagrams/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Create a 3-tier AWS architecture"}'

# 5. View traces in Grafana
open http://localhost:3000/explore
```

### Check Telemetry Module

```python
# Quick verification script
from agent.telemetry import get_tracer

tracer = get_tracer()
with tracer.start_as_current_span("test.span") as span:
    span.set_attribute("test.key", "test.value")
    print("Span created:", span.get_span_context().trace_id)
```

______________________________________________________________________

## Environment Variables Reference

| Variable                      | Description                              | Default         |
| ----------------------------- | ---------------------------------------- | --------------- |
| `DEPLOYMENT_ENVIRONMENT`      | Set to `DEPLOYED_SERVICE` for production | `DEBUG`         |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint                  | None            |
| `OTEL_DEBUG`                  | Enable console span logging              | None            |
| `OTEL_SERVICE_NAME`           | Override service name                    | `diagram-agent` |

______________________________________________________________________

## Troubleshooting

### No traces appearing

1. Check OTLP endpoint is reachable:

   ```bash
   curl -v http://localhost:4318/v1/traces
   ```

1. Enable debug logging:

   ```bash
   export OTEL_DEBUG=1
   ```

1. Verify Tempo is receiving data:

   ```bash
   curl http://localhost:3200/ready
   ```

### Connection refused errors

- Ensure Tempo ports are exposed (4317 for gRPC, 4318 for HTTP)
- Check Docker network connectivity
- Verify firewall rules in GCP

### GCS permission errors

```bash
# Verify service account permissions
gcloud storage ls gs://diagramik-traces/

# Check IAM bindings
gsutil iam get gs://diagramik-traces
```

______________________________________________________________________

## Sources

- [Grafana LGTM Docker Image](https://grafana.com/docs/opentelemetry/docker-lgtm/)
- [Deploy Tempo using Docker Compose](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/locally/docker-compose/)
- [Tempo GCS Configuration](https://grafana.com/docs/tempo/latest/configuration/hosted-storage/gcs/)
- [Tempo Configuration Reference](https://grafana.com/docs/tempo/latest/configuration/)
- [OpenTelemetry Python OTLP Exporter](https://opentelemetry-python.readthedocs.io/en/latest/exporter/otlp/otlp.html)
