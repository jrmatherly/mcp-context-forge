# MindsDB v26.0.0 & Streamable HTTP Transport Research

**Research Date**: 2026-02-26  
**Status**: COMPLETED - Streamable HTTP NOT supported in MindsDB v26.0.0

## Key Findings

### 1. MindsDB v26.0.0 Release Status
- **Version**: v26.0.0 exists (released February 25, 2025)
- **Breaking Changes**: Marked as "contains breaking changes" but specifics not documented in release notes
- **Notable Change**: pgvector is new default KB store (ChromaDB deprecated)
- **MCP Status**: No transport protocol changes mentioned

### 2. Streamable HTTP Transport Support - NOT IMPLEMENTED
**Critical Finding**: MindsDB v26.0.0 **DOES NOT** support Streamable HTTP transport for MCP.

**Evidence**:
- Memory note (MEMORY.md line 44): "SSE transport deprecated in MCP spec 2025-03-26; MindsDB hasn't adopted streamable HTTP"
- MindsDB still exposes SSE-only endpoint at `/mcp/sse`
- No `/mcp` endpoint for Streamable HTTP found in documentation
- MCP SDK v1.10.0+ supports Streamable HTTP (spec 2025-03-26), but MindsDB hasn't updated

### 3. ASGI "http.response.start" AssertionError - IDENTIFIED
**Pattern Found**: Multiple FastMCP implementations report ASGI assertion errors with SSE:
- Error: `AssertionError: Unexpected message 'http.response.start' sent, after response already completed`
- Root cause: Unhandled exceptions in SSE TaskGroup bubble up to Starlette middleware, violating ASGI lifecycle
- Happens when response already started streaming and error occurs in background task

**MindsDB Incidents**:
- Issue #12089: MCP SSE endpoint fails with "Invalid Host header" behind proxy (relates to MCP SDK v1.23.0+ DNS rebinding protection)
- Issue #11106: Log formatting broken by MCP and A2A APIs (July 2025)

### 4. Current MindsDB MCP Endpoints
- **SSE**: `http://mindsdb:47334/mcp/sse` (working, but deprecated in MCP spec)
- **Auth**: `/mcp/status` requires auth token (returns 401 without it)
- **Healthcheck**: Use `/api/status` instead of `/mcp/status`
- **A2A**: `/a2a/` endpoint exists (JSONRPC, PAT auth)

### 5. Why SSE is Problematic

| Issue | Impact |
|-------|--------|
| Dual-endpoint complexity | SSE endpoint + messages endpoint = 2 connections |
| Connection reliability | SSE drops = data loss during long operations |
| ASGI protocol violations | Streaming errors hard to handle correctly |
| Scalability | Per-connection state management overhead |

### 6. Why Streamable HTTP is Better

| Advantage | Benefit |
|-----------|---------|
| Single HTTP endpoint | Simpler client/server architecture |
| POST + stream response | Standard HTTP semantics |
| 202 Accepted pattern | Clear async handling |
| MCP standard (2025-03-26) | Future-proof protocol |

## Recommendation

**Cannot switch to Streamable HTTP** because MindsDB v26.0.0 does not implement it.

**Mitigation Options**:
1. **Wait for MindsDB update** - Monitor releases for Streamable HTTP adoption
2. **Use proxy/translation layer** - Tools like `mcp-proxy` can translate between SSE and Streamable HTTP
3. **Fork/patch MindsDB** - Add Streamable HTTP endpoint (high effort, maintenance burden)
4. **Workaround current SSE issues**:
   - Ensure proper Host header: `localhost:47334` (not bare `localhost`)
   - Monitor `/mcp/sse` for transient failures
   - Implement automatic reconnection + exponential backoff
   - Add request timeout handling

## Related Resources

- MindsDB GitHub: https://github.com/mindsdb/mindsdb
- MindsDB MCP Issue #12089: https://github.com/mindsdb/mindsdb/issues/12089
- FastMCP ASGI Bug #671: https://github.com/jlowin/fastmcp/issues/671
- MCP SDK Security (DNS rebinding): https://github.com/modelcontextprotocol/python-sdk/issues/464
- MCP Spec 2025-03-26 (Streamable HTTP): https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- Why MCP deprecated SSE: https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http

## Next Steps

1. Document SSE workarounds in MindsDB integration guide
2. Monitor MindsDB releases for Streamable HTTP adoption
3. Consider adding Streamable HTTP adapter/proxy layer if MindsDB adoption lags
4. Test current SSE endpoint resilience under failure conditions
