# Publishing the Helm chart for MCP Context-Forge

## Lint & package

```bash
helm lint .
helm package .   # → mcp-stack-1.0.0-rc.1.tgz
```

## Log in to GHCR

```bash
echo "${CR_PAT}" | \
  helm registry login ghcr.io -u <your-github-user> --password-stdin
# Login Succeeded
```

## Push the chart (separate package path)

```bash
helm push mcp-stack-*.tgz oci://ghcr.io/jrmatherly/mcp-context-forge
```

## Link the package to this repo (once)

1. In GitHub → **Packages** → `mcp-stack`
2. **Package Settings** → **Manage package**
3. "**Add repository**" → pick the current repo and save

This lets others see the chart in the repo's **Packages** sidebar.

---

## Verify & use

```bash
helm pull oci://ghcr.io/jrmatherly/mcp-context-forge/mcp-stack --version 1.0.0-rc.1
```
