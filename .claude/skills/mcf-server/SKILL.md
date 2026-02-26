---
name: mcf-server
description: Scaffold and create new MCP servers for MCP Context Forge. Use when asked to create a new MCP server, add a tool server, scaffold a Python or Go MCP server, build an MCP integration, or register an external service with the gateway. Also use when the user mentions adding new tools, creating a server for a specific API, or building a FastMCP service.
---

Create an MCP server for: $ARGUMENTS

## Language Decision

Ask the user which language unless obvious from context:
- **Python (FastMCP 2.x)** — Default choice. 20 existing examples in `mcp-servers/python/`. Best for rapid development, API integrations, and data processing.
- **Go (mcp-go)** — 6 existing examples in `mcp-servers/go/`. Best for high-performance, low-latency, or standalone binary deployments.

## Python Server (FastMCP 2.x)

### Project Layout

```
mcp-servers/python/<server-name>/
  pyproject.toml
  Makefile
  Containerfile
  README.md
  src/<package_name>/
    __init__.py
    server_fastmcp.py   # FastMCP entry point
    tools.py             # optional: separate tool logic
  tests/
    test_server.py
```

### Step 1: Scaffold the project

Use the naming convention: kebab-case for directory, snake_case for package.

```bash
# Example: mcp-servers/python/weather-server/src/weather_server/
mkdir -p mcp-servers/python/<server-name>/src/<package_name>
mkdir -p mcp-servers/python/<server-name>/tests
touch mcp-servers/python/<server-name>/src/<package_name>/__init__.py
```

### Step 2: Create `server_fastmcp.py`

Follow this pattern (all 20 existing servers use it):

```python
# -*- coding: utf-8 -*-
from fastmcp import FastMCP
import argparse

mcp = FastMCP("<server-name>", version="0.1.0")


@mcp.tool
def my_tool(param: str) -> str:
    """Tool description — type hints define the MCP schema."""
    return f"Result: {param}"


def main() -> None:
    """Entry point with transport selection."""
    parser = argparse.ArgumentParser(description="<Server Name> FastMCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
```

Key patterns:
- Use `@mcp.tool` decorator — type hints become the MCP schema automatically
- Support both stdio and HTTP transports via argparse
- Use Pydantic models for complex tool arguments/returns
- Log to stderr under stdio to avoid corrupting the protocol stream
- Keep FastMCP objects in `server_fastmcp.py`; move heavy logic to `tools.py`

### Step 3: Create `pyproject.toml`

```toml
[project]
name = "<server-name>"
version = "0.1.0"
description = "<description>"
requires-python = ">=3.11"
dependencies = [
  "fastmcp==2.11.3",
  "pydantic>=2.5.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-asyncio>=0.21.0", "pytest-cov>=4.0.0", "ruff>=0.0.290"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/<package_name>"]

[project.scripts]
<server-name> = "<package_name>.server_fastmcp:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "B", "I", "N", "UP"]
```

Critical: Always pin FastMCP to an exact version (`fastmcp==2.11.3`).

### Step 4: Create `Makefile`

```makefile
.PHONY: help install dev-install test dev serve-http serve-sse clean

PYTHON ?= python3
HTTP_PORT ?= 8000
HTTP_HOST ?= 0.0.0.0

help:
	@awk 'BEGIN {FS=":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install in editable mode
	$(PYTHON) -m pip install -e .

dev-install: ## Install with dev extras
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run tests
	pytest -v --cov=<package_name> --cov-report=term-missing

dev: ## Run (stdio)
	$(PYTHON) -m <package_name>.server_fastmcp

serve-http: ## Run with native HTTP
	$(PYTHON) -m <package_name>.server_fastmcp --transport http --host $(HTTP_HOST) --port $(HTTP_PORT)

serve-sse: ## Run with translate SSE bridge
	$(PYTHON) -m mcpgateway.translate --stdio "$(PYTHON) -m <package_name>.server_fastmcp" --host $(HTTP_HOST) --port $(HTTP_PORT) --expose-sse

clean: ## Remove caches
	rm -rf .pytest_cache .ruff_cache .mypy_cache __pycache__ */__pycache__ *.egg-info
```

### Step 5: Create `Containerfile`

```dockerfile
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN python -m venv /app/.venv && /app/.venv/bin/pip install --upgrade pip setuptools wheel && /app/.venv/bin/pip install -e .
RUN useradd -u 1001 -m appuser && chown -R 1001:1001 /app
USER 1001
CMD ["python", "-m", "<package_name>.server_fastmcp"]
```

### Step 6: Create basic tests

```python
# -*- coding: utf-8 -*-
"""Tests for <server-name> FastMCP server."""
import pytest
from <package_name>.server_fastmcp import mcp


def test_server_name():
    assert mcp.name == "<server-name>"


@pytest.mark.asyncio
async def test_tool_list():
    tools = await mcp.get_tools()
    tool_names = [t.name for t in tools]
    assert "my_tool" in tool_names
```

## Go Server (mcp-go)

### Project Layout

```
mcp-servers/go/<server-name>/
  go.mod
  main.go
  Makefile
  Dockerfile
  README.md
```

### Step 1: Scaffold and write `main.go`

```go
package main

import (
    "encoding/json"
    "log"
    "os"

    "github.com/mark3labs/mcp-go/mcp"
    "github.com/mark3labs/mcp-go/server"
)

const (
    appName    = "<server-name>"
    appVersion = "0.1.0"
)

func handleMyTool(req mcp.CallToolRequest) (mcp.ToolResult, error) {
    payload := map[string]string{"result": "hello"}
    b, _ := json.Marshal(payload)
    return mcp.StringResult(string(b)), nil
}

func main() {
    logger := log.New(os.Stderr, "", log.LstdFlags)
    logger.Printf("starting %s %s (stdio)", appName, appVersion)

    s := server.NewMCPServer(appName, appVersion,
        server.WithToolCapabilities(false),
        server.WithLogging(),
        server.WithRecovery(),
    )

    tool := mcp.NewTool("my_tool",
        mcp.WithDescription("Tool description"),
        mcp.WithReadOnlyHintAnnotation(true),
    )
    s.AddTool(tool, handleMyTool)

    if err := server.ServeStdio(s); err != nil {
        logger.Fatalf("stdio error: %v", err)
    }
}
```

Key: Log to stderr to avoid protocol noise on stdio.

### Step 2: Create `go.mod`

```go
module github.com/jrmatherly/mcp-context-forge/mcp-servers/go/<server-name>

go 1.23
toolchain go1.23.10

require github.com/mark3labs/mcp-go v0.32.0
```

Then run `go mod tidy`.

## Gateway Integration

After the server is running, register it with the gateway:

### Option A: Translate stdio to HTTP (for stdio-only servers)
```bash
python -m mcpgateway.translate --stdio "python -m <package>.server_fastmcp" --port 9000
```

### Option B: Register HTTP endpoint directly
```bash
curl -s -X POST -H "Authorization: Bearer $MCPGATEWAY_BEARER_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "http://localhost:8000/mcp",
           "name": "<server-name>",
           "transport": "STREAMABLEHTTP",
           "description": "<description>"
         }' \
     http://localhost:4444/gateways | jq
```

### Option C: Docker Compose service
Add to `docker-compose.yml` with `profiles: ["<profile-name>"]` and a registration init container.
If the registration script needs to run in the container image, add it to `Containerfile.lite`:
```dockerfile
COPY scripts/register-<name>.py /app/scripts/
```

## Checklist

- [ ] Server runs locally: `make dev` (stdio) or `make serve-http` (HTTP)
- [ ] Tools discoverable: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | make dev`
- [ ] Tests pass: `make test`
- [ ] Registered with gateway (if applicable)
- [ ] Virtual server created (if applicable): `POST /servers`
