# Raw Kubernetes Manifests (Deprecated)

These raw manifests were early-stage scaffolding and have **not been maintained**
since the Helm chart was introduced. They contain critical issues including:

- PostgreSQL 10.1 (end-of-life since November 2022)
- Hardcoded weak passwords in ConfigMaps (should be Secrets)
- Missing health probes, resource limits, and security context
- Missing 40+ environment variables required by the gateway
- No PgBouncer, Redis auth, plugin support, or MindsDB

## Use the Helm Chart Instead

The production-grade Helm chart at `charts/mcp-stack/` provides all of these
features with proper templating, schema validation, and CI/CD workflows.

```bash
# Install from OCI registry
helm install mcp-gateway oci://ghcr.io/jrmatherly/mcp-context-forge/mcp-stack

# Or from local source
helm install mcp-gateway charts/mcp-stack/ -f my-values.yaml
```

See `charts/AGENTS.md` for developer commands and `docs/docs/deployment/helm/`
for the full deployment guide.

## Removal Plan

These manifests are retained temporarily for reference. They will be removed
in a future release once the Helm chart has been validated in production.
