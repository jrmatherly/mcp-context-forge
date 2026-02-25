# deployment/AGENTS.md

Infrastructure and deployment guidance for AI coding assistants.

## Directory Structure

```
deployment/
├── README.md
├── CHARTS.md           # Helm chart reference
├── k8s/                # Kubernetes manifests
├── knative/            # Knative serverless configs
├── ansible/            # Ansible playbooks
└── terraform/          # Terraform IaC

infra/                  # Local development infrastructure
├── postgres/           # PostgreSQL Docker setup
├── nginx/              # Nginx reverse proxy
└── monitoring/         # Prometheus/Grafana
```

## Container Operations

From repository root:

```bash
# Build
make container-build              # Auto-detect Docker/Podman

# Run
make container-run-ssl-host       # Run with TLS on :4444, host networking

# Manage
make container-stop               # Stop and remove container
make container-logs               # Show container logs

# Security
make security-scan                # Run Trivy + Grype vulnerability scans
```

## Kubernetes Deployment

### Using Helm (Recommended)

See `charts/AGENTS.md` for Helm chart usage.

```bash
cd charts/mcp-stack
make install
```

### Raw Manifests (Deprecated)

The `k8s/` directory contains **deprecated** raw Kubernetes manifests. Use the Helm chart instead. See `deployment/k8s/README.md` for details.

## Knative Serverless

The `knative/` directory contains Knative Service definitions for serverless deployment.
- All credentials use `mcpgateway-secrets` Secret (not ConfigMaps) — `postgres-config.yaml` was removed
- See `KNATIVE_SCALE_TO_ZERO.md` for deployment steps and Secret creation instructions

## Terraform

The `terraform/` directory contains infrastructure-as-code for cloud providers.
- Uses `yamlencode` to pass Helm values matching chart's `values.yaml` structure
- Separate secrets per service (`mcpgw_db`, `mcpgw_redis`) with keys matching chart's external DB/Redis pattern
- Run `terraform fmt` after edits — auto-formats HCL files

## Ansible

The `ansible/` directory contains playbooks for traditional server deployment.
- `group_vars/all.yml` defines variables consumed by Jinja2 templates in `roles/k8s/templates/`
- Image split: `gateway_image` (repository) + `gateway_image_tag` (tag) — templates must concatenate both

## Local Infrastructure

The `infra/` directory provides Docker Compose components for local development:

```bash
# Start PostgreSQL
docker-compose -f infra/postgres/docker-compose.yml up -d

# Start monitoring stack (Prometheus/Grafana)
docker-compose -f infra/monitoring/docker-compose.yml up -d

# Start Nginx reverse proxy
docker-compose -f infra/nginx/docker-compose.yml up -d
```

## TLS/SSL

```bash
# Generate self-signed certificates
make certs

# Run with TLS
make serve-ssl                    # Gunicorn on :4444 with TLS
make container-run-ssl-host       # Container with TLS
```

Certificates are stored in `./certs/`.

## Environment Configuration

Key deployment environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379

# Server
HOST=0.0.0.0
PORT=4444

# TLS (for serve-ssl)
SSL_CERTFILE=certs/server.crt
SSL_KEYFILE=certs/server.key
```

## Documentation

- [Container Deployment](docs/docs/deployment/container.md)
- [Kubernetes Deployment](docs/docs/deployment/kubernetes.md)
- [Cloud Deployments](docs/docs/deployment/) - AWS, Azure, GCP, Fly.io guides

## Shared Nginx (Cross-Stack Production)

In production, LibreChat's nginx reverse proxy handles both stacks:
- `shared-proxy` external Docker network connects LibreChat's nginx to MCF's gateway
- Subdomain routing: `${LIBRECHAT_DOMAIN}` → LibreChat, `${MCF_DOMAIN}` → MCF gateway
- MCF config uses `resolver 127.0.0.11` + variable-based `proxy_pass` for runtime DNS (no startup dependency)
- nginx:1-alpine's built-in envsubst processes `templates/*.conf.template` → `conf.d/*.conf`
- Stock `default.conf` suppressed via `/dev/null` mount
- Design doc: `.scratchpad/plans/shared-nginx-consolidation.md`
- MCF's standalone nginx: `docker compose --profile standalone up` (local dev only)

## Key Files

- `Makefile` (root) - Container build/run commands
- `Containerfile` / `Dockerfile` - Container image definition
- `deployment/k8s/` - Kubernetes manifests
- `charts/mcp-stack/` - Helm chart
- `infra/` - Local development infrastructure
