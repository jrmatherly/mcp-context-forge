---
name: mcf-plugin
description: Author gateway plugins for MCP Context Forge — native Python plugins or external MCP plugins. Use when asked to create a new plugin, add a hook, build a filter/guard/validator, write a content transformer, implement rate limiting or PII detection, or add any pre/post processing to the gateway pipeline. Also use when the user mentions plugin configuration, hook types, or policy enforcement.
---

Create a gateway plugin for: $ARGUMENTS

## Plugin Type Decision

Ask the user unless obvious from context:
- **Native (in-process)** — Python class extending `Plugin`. Runs inside the gateway process. Best for transforms, filters, validators, and anything needing low latency.
- **External (MCP server)** — Separate MCP server connected via Streamable HTTP, STDIO, or UDS. Best for integrating third-party services, policies requiring isolation, or non-Python implementations.

## Hook Types

Six production hooks — plugins override only the hooks they need:

| Hook | When | Typical Use |
|------|------|-------------|
| `prompt_pre_fetch` | Before retrieving a prompt | Validate/transform args, mask PII, block |
| `prompt_post_fetch` | After rendering a prompt | Filter/sanitize content, add metadata |
| `tool_pre_invoke` | Before executing a tool | Auth/validation, policy checks, arg mutation, block |
| `tool_post_invoke` | After tool returns | Redact outputs, transform result, audit |
| `resource_pre_fetch` | Before fetching a URI | Protocol/domain checks, metadata injection, block |
| `resource_post_fetch` | After content fetched | Size checks, redaction, content transformation |

## Native Plugin

### Step 1: Create plugin directory

```
plugins/<plugin_name>/
  <plugin_name>.py    # Plugin class
  __init__.py          # empty
```

Convention: 42 built-in plugins exist under `plugins/`. Follow the same flat structure.

### Step 2: Write the plugin class

```python
# -*- coding: utf-8 -*-
"""<Plugin description>."""
from mcpgateway.plugins.framework.base import Plugin
from mcpgateway.plugins.framework.models import (
    PluginConfig,
    PluginContext,
    PluginViolation,
    ToolPreInvokePayload,
    ToolPreInvokeResult,
)


class MyPlugin(Plugin):
    """<Description of what this plugin does>."""

    async def tool_pre_invoke(
        self, payload: ToolPreInvokePayload, context: PluginContext
    ) -> ToolPreInvokeResult:
        # Access plugin-specific config
        threshold = self.config.config.get("threshold", 100)

        # Check condition
        if some_violation_detected(payload):
            return ToolPreInvokeResult(
                continue_processing=False,
                violation=PluginViolation(
                    reason="Policy violation",
                    description="Detailed explanation",
                    code="MY_PLUGIN_VIOLATION",
                    details={"matched": True},
                ),
            )

        # Pass through (optionally modify payload)
        return ToolPreInvokeResult(
            continue_processing=True,
            modified_payload=payload,
            metadata={"checked_by": "my_plugin"},
        )
```

### Key interfaces

**Payload models** (in `mcpgateway/plugins/framework/models.py`):
- `PromptPrehookPayload(name: str, args: dict[str, str])`
- `PromptPosthookPayload(name: str, result: PromptResult)`
- `ToolPreInvokePayload(name: str, args: dict[str, Any])`
- `ToolPostInvokePayload(name: str, result: Any)`
- `ResourcePreFetchPayload(uri: str, metadata: dict[str, Any])`
- `ResourcePostFetchPayload(uri: str, content: Any)`

**Result model** — all hooks return `PluginResult[T]`:
- `continue_processing: bool = True` — set False to block
- `modified_payload: Optional[T]` — when transforming
- `violation: Optional[PluginViolation]` — when blocking or auditing
- `metadata: dict[str, Any] = {}` — accumulates across plugins

**Context**:
- `context.state` — local plugin data (persists between pre/post)
- `context.global_context.state` — shared across all plugins in the request
- `context.global_context.request_id` — unique request identifier

### Step 3: Register in `plugins/config.yaml`

```yaml
plugins:
  - name: "MyPlugin"
    kind: "plugins.<plugin_name>.<plugin_name>.MyPlugin"
    hooks: ["tool_pre_invoke"]
    mode: "enforce"           # enforce | enforce_ignore_error | permissive | disabled
    priority: 100             # lower runs first (ArgumentNormalizer=40, PIIFilter=50)
    description: "What this plugin does"
    config:
      threshold: 100          # plugin-specific settings
    # Optional: conditions for selective execution
    # conditions:
    #   - tools: ["specific-tool-*"]
    #     server_ids: ["uuid-here"]
```

**Modes:**
- `enforce` — violations block the request
- `enforce_ignore_error` — violations block, but plugin errors don't
- `permissive` — log violations, don't block
- `disabled` — loaded but not executed

**Priority ordering** (existing conventions):
- 40: ArgumentNormalizer (stabilize inputs first)
- 50: PIIFilter (detect on stabilized input)
- 75: ResourceFilter
- 100+: Custom plugins (deny, regex, etc.)

### Step 4: Write tests

```python
# -*- coding: utf-8 -*-
import pytest
from mcpgateway.plugins.framework.models import (
    HookType, PluginConfig, PluginContext, GlobalContext,
    ToolPreInvokePayload,
)
from plugins.<plugin_name>.<plugin_name> import MyPlugin


@pytest.mark.asyncio
async def test_allows_valid_request():
    cfg = PluginConfig(
        name="MyPlugin",
        kind="plugins.<plugin_name>.<plugin_name>.MyPlugin",
        hooks=[HookType.TOOL_PRE_INVOKE],
        priority=100,
        config={"threshold": 100},
    )
    plugin = MyPlugin(cfg)
    payload = ToolPreInvokePayload(name="some_tool", args={"key": "value"})
    ctx = PluginContext(global_context=GlobalContext(request_id="test-1"))

    result = await plugin.tool_pre_invoke(payload, ctx)
    assert result.continue_processing is True


@pytest.mark.asyncio
async def test_blocks_violation():
    cfg = PluginConfig(
        name="MyPlugin",
        kind="plugins.<plugin_name>.<plugin_name>.MyPlugin",
        hooks=[HookType.TOOL_PRE_INVOKE],
        priority=100,
        config={"threshold": 1},
    )
    plugin = MyPlugin(cfg)
    payload = ToolPreInvokePayload(name="bad_tool", args={"malicious": "data"})
    ctx = PluginContext(global_context=GlobalContext(request_id="test-2"))

    result = await plugin.tool_pre_invoke(payload, ctx)
    assert result.continue_processing is False
    assert result.violation is not None
    assert result.violation.code == "MY_PLUGIN_VIOLATION"
```

## External Plugin (MCP Server)

External plugins implement the same hooks but run as separate MCP servers.

### Required MCP tools

The server must expose these tool names (implement only the hooks you need):
- `get_plugin_config` — returns `PluginConfig`-compatible JSON
- `prompt_pre_fetch`, `prompt_post_fetch`
- `tool_pre_invoke`, `tool_post_invoke`
- `resource_pre_fetch`, `resource_post_fetch`

### Call contract

Request to each hook:
```json
{"plugin_name": "str", "payload": "<HookPayload>", "context": "<PluginContext>"}
```

Response must be exactly ONE of:
```json
{"result": "<PluginResult serialized>"}
{"context": "<PluginContext serialized>"}
{"error": "<PluginErrorModel>"}
```

### Registration in `plugins/config.yaml`

```yaml
- name: "MyExternalPlugin"
  kind: "external"
  priority: 100
  hooks: ["tool_pre_invoke"]
  mode: "enforce"
  mcp:
    proto: STREAMABLEHTTP          # or STDIO
    url: http://localhost:8000/mcp  # for HTTP
    # script: path/to/server.py    # for STDIO
    # uds: /var/run/plugin.sock    # for Unix Domain Socket
```

### Bootstrap from template

```bash
mcpplugins bootstrap --destination plugins/<name> --type external
```

## Integration testing with PluginManager

```python
@pytest.mark.asyncio
async def test_manager_pipeline(tmp_path):
    cfg = tmp_path / "plugins.yaml"
    cfg.write_text("""
plugins:
  - name: "MyPlugin"
    kind: "plugins.<name>.<name>.MyPlugin"
    hooks: ["tool_pre_invoke"]
    mode: "enforce"
    priority: 100
    config: {}
plugin_settings:
  plugin_timeout: 5
  fail_on_plugin_error: false
plugin_dirs: []
""")
    mgr = PluginManager(str(cfg), timeout=5)
    await mgr.initialize()
    ctx = GlobalContext(request_id="req-1")
    payload = ToolPreInvokePayload(name="test_tool", args={"x": "y"})
    result, _ = await mgr.tool_pre_invoke(payload, ctx)
    assert result.continue_processing
    await mgr.shutdown()
```

## Checklist

- [ ] Plugin class implements correct hook methods with proper type signatures
- [ ] Registered in `plugins/config.yaml` with appropriate mode and priority
- [ ] Tests cover both allow and block paths
- [ ] `PLUGINS_ENABLED=true` in `.env`
- [ ] Plugin ordering makes sense (normalizers before detectors before policy)
