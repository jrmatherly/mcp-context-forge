# Atlassian Rovo MCP Server

## Overview

The Atlassian Rovo MCP Server is a cloud-hosted remote server that provides AI tools with direct access to Jira, Confluence, and Compass. It enables AI agents to search and create Jira issues, read and write Confluence pages, manage Compass service components, and link resources across Atlassian products through natural language interactions.

**Remote Server Endpoint:** `https://mcp.atlassian.com/v1/mcp`

**Authentication:** OAuth 2.0 (3LO) via `auth.atlassian.com`

## Use Cases

- **Issue Management:** Search issues via JQL, create and update Jira issues, bulk-create issues from meeting notes or specifications
- **Knowledge Management:** Summarize Confluence pages, create new pages, search across spaces, navigate accessible spaces
- **Service Catalog:** Create Compass service components, bulk import from CSV/JSON, query service dependencies
- **Cross-Product Linking:** Link Jira tickets to Confluence pages, fetch docs linked to Compass components

## Integration with MCP Gateway

The Atlassian Rovo MCP server is cloud-hosted by Atlassian -- no local server is required. MCP Context Forge acts as an OAuth relay, managing per-user tokens and providing unified discovery.

### Prerequisites

1. An Atlassian Cloud organization with Rovo MCP server enabled
2. An OAuth 2.0 (3LO) app created at [developer.atlassian.com/console/myapps/](https://developer.atlassian.com/console/myapps/)
3. Your MCF gateway domain added to the Atlassian domain allowlist (navigate to **Admin** > **Apps** > **AI settings** > **Rovo MCP server**)
4. OAuth callback URL set to `https://<MCF_DOMAIN>/oauth/callback`

### Option 1: Automated Registration (Docker Compose)

The simplest method uses the included registration script via Docker Compose:

```bash
# Set required environment variables in .env
ATLASSIAN_OAUTH_CLIENT_ID=your-client-id
ATLASSIAN_OAUTH_CLIENT_SECRET=your-client-secret
MCF_DOMAIN=mcp.yourdomain.com

# Start the gateway with Atlassian profile
docker compose --profile atlassian up -d
```

The `register_atlassian` init container will automatically register the gateway and create a virtual server.

### Option 2: Manual Registration (API)

```bash
# Register the Atlassian Rovo MCP server with OAuth configuration
curl -X POST http://localhost:4444/gateways \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "name": "atlassian-rovo",
    "url": "https://mcp.atlassian.com/v1/mcp",
    "transport": "STREAMABLEHTTP",
    "description": "Atlassian Rovo MCP Server (Jira + Confluence + Compass)",
    "auth_type": "oauth",
    "oauth_config": {
      "grant_type": "authorization_code",
      "issuer": "https://auth.atlassian.com",
      "authorization_url": "https://auth.atlassian.com/authorize?audience=api.atlassian.com",
      "token_url": "https://auth.atlassian.com/oauth/token",
      "redirect_uri": "https://<MCF_DOMAIN>/oauth/callback",
      "scopes": [
        "read:jira-work",
        "write:jira-work",
        "read:jira-user",
        "read:confluence-content.all",
        "write:confluence-content",
        "read:confluence-space.summary"
      ],
      "client_id": "<ATLASSIAN_OAUTH_CLIENT_ID>",
      "client_secret": "<ATLASSIAN_OAUTH_CLIENT_SECRET>"
    }
  }'
```

**Important notes:**

- The `audience=api.atlassian.com` parameter is required by Atlassian's authorization endpoint
- The `issuer` field (`https://auth.atlassian.com`) enables OIDC endpoint auto-discovery
- Leave **Passthrough Headers** empty -- MCF automatically injects each user's OAuth token into upstream requests

### User Authorization

After the gateway is registered, each user must complete the OAuth consent flow once:

1. Navigate to the MCF Admin UI gateway list
2. Click **Authorize** for the `atlassian-rovo` gateway
3. Complete the consent flow at `auth.atlassian.com`
4. Tools are automatically discovered after the first successful authorization

## Tool Configuration

### Available Tools

Tools are automatically discovered from Atlassian's MCP server after OAuth authorization.

| Product | Tools |
|---------|-------|
| **Jira** | Search issues (JQL), create issues, bulk-create issues, update issues |
| **Confluence** | Summarize pages, create pages, search content, list spaces |
| **Compass** | Create components, bulk import, query dependencies |

### OAuth Scopes

| Scope | Access |
|-------|--------|
| `read:jira-work` | Read Jira project and issue data, search for issues |
| `write:jira-work` | Create and edit issues, post comments, create worklogs |
| `read:jira-user` | View user information |
| `read:confluence-content.all` | Read all content with body and expansions |
| `write:confluence-content` | Create pages, blogs, comments |
| `read:confluence-space.summary` | Read space summaries |

Additional scopes can be added in the `oauth_config.scopes` array and the Atlassian OAuth app settings.

## Creating a Virtual Server

After registering the gateway, create a virtual server to expose the Atlassian tools:

```bash
# List discovered tools to get their IDs
curl -s http://localhost:4444/tools \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" | jq '.[] | {id, name}'

# Create virtual server with discovered tool IDs
curl -X POST http://localhost:4444/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "server": {
      "name": "admin-atlassian",
      "description": "Atlassian tools - Jira, Confluence, and Compass",
      "associated_tools": ["<TOOL_ID_1>", "<TOOL_ID_2>"],
      "visibility": "private"
    }
  }'
```

The automated registration script creates the `admin-atlassian` virtual server automatically.

## Using Atlassian Tools

Once configured and authorized, access tools through the MCP Gateway:

### List Available Tools

```bash
curl -X GET "http://localhost:4444/servers/{server_id}/tools" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}"
```

### Example Tool Invocations

#### Search Jira Issues
```bash
curl -X POST "http://localhost:4444/tools/invoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "server_id": "admin-atlassian",
    "tool_name": "search_issues",
    "arguments": {
      "jql": "project = PROJ AND status = Open ORDER BY created DESC"
    }
  }'
```

#### Create Jira Issue
```bash
curl -X POST "http://localhost:4444/tools/invoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "server_id": "admin-atlassian",
    "tool_name": "create_issue",
    "arguments": {
      "project": "PROJ",
      "summary": "Implement feature X",
      "description": "## Requirements\nDetailed description...",
      "issue_type": "Task"
    }
  }'
```

#### Search Confluence Pages
```bash
curl -X POST "http://localhost:4444/tools/invoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "server_id": "admin-atlassian",
    "tool_name": "search_pages",
    "arguments": {
      "query": "architecture design document"
    }
  }'
```

## Security Considerations

1. **Per-User OAuth Isolation**: Each user's Atlassian token is stored separately, encrypted at rest with AES-256-GCM. No cross-user token reuse is possible.
2. **Permission Inheritance**: Tools operate within the user's existing Atlassian permissions -- no privilege escalation occurs.
3. **Domain Allowlisting**: Only approved domains can initiate OAuth flows with Atlassian.
4. **Automatic Token Refresh**: MCF automatically refreshes expired tokens using stored refresh tokens, or prompts re-authorization if refresh fails.
5. **Audit Trail**: All MCP tool invocations are logged by both MCF and Atlassian's organization audit logs.

## Troubleshooting

### OAuth Authorization Fails

- Verify the MCF gateway domain is added to Atlassian's domain allowlist at **Admin** > **Apps** > **AI settings** > **Rovo MCP server**
- Check that the OAuth callback URL matches exactly: `https://<MCF_DOMAIN>/oauth/callback`
- Ensure the OAuth app at `developer.atlassian.com` has the required Jira and Confluence APIs and scopes enabled

### No Tools Discovered

- Tools only appear after at least one user completes the OAuth consent flow
- The first user must have access to the requested Atlassian products (Jira, Confluence)
- Check gateway status: `GET /gateways` and verify the `atlassian-rovo` entry shows healthy

### Token Refresh Errors

- Atlassian refresh tokens can expire if unused for an extended period
- Users may need to re-authorize: navigate to the gateway in MCF Admin UI and click **Authorize**
- Check that the OAuth app has not been deleted or had its scopes changed at `developer.atlassian.com`

## Additional Resources

- [Atlassian Rovo MCP Server Repository](https://github.com/atlassian/atlassian-mcp-server)
- [Atlassian OAuth 2.0 (3LO) Documentation](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [Atlassian REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [MCP Gateway Documentation](../../../../index.md)
