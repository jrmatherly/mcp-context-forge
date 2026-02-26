# Bitbucket MCP Server

## Overview

The Bitbucket MCP Server is a custom MCP server that provides AI tools for interacting with Bitbucket Cloud repositories, pull requests, pipelines, and code search via the Bitbucket REST API v2.

Bitbucket is **not covered** by Atlassian's official Rovo MCP Server. This custom server fills that gap and can be composed with the Rovo server into a single virtual server for complete Atlassian coverage.

**Server Type:** Self-hosted (custom FastMCP server)

**Authentication:** Bitbucket OAuth 2.0 (separate from Atlassian 3LO)

## Use Cases

- **Repository Management:** List and browse repositories, search code across a workspace
- **Pull Request Workflows:** List, create, review, and merge pull requests, manage PR comments
- **CI/CD Monitoring:** List pipeline runs, check pipeline status, trigger new builds

## Integration with MCP Gateway

### Prerequisites

1. A Bitbucket Cloud workspace
2. A Bitbucket OAuth consumer created at **Workspace settings** > **OAuth consumers**
3. OAuth callback URL set to `https://<MCF_DOMAIN>/oauth/callback`
4. Required permissions selected on the consumer (repository, pullrequest)

### Option 1: Automated Registration (Docker Compose)

Set the Bitbucket OAuth credentials in `.env` alongside the Atlassian credentials:

```bash
# Required for Bitbucket (in addition to Atlassian credentials)
BITBUCKET_OAUTH_CLIENT_ID=your-consumer-key
BITBUCKET_OAUTH_CLIENT_SECRET=your-consumer-secret

# Start with the Atlassian profile
docker compose --profile atlassian up -d
```

The registration script conditionally registers the Bitbucket gateway when these environment variables are set.

### Option 2: Manual Registration (API)

```bash
# Register the custom Bitbucket MCP server
curl -X POST http://localhost:4444/gateways \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "name": "atlassian-bitbucket",
    "url": "http://bitbucket-mcp-server:8000/mcp",
    "transport": "STREAMABLEHTTP",
    "description": "Custom Bitbucket Cloud MCP Server",
    "auth_type": "oauth",
    "oauth_config": {
      "grant_type": "authorization_code",
      "authorization_url": "https://bitbucket.org/site/oauth2/authorize",
      "token_url": "https://bitbucket.org/site/oauth2/access_token",
      "redirect_uri": "https://<MCF_DOMAIN>/oauth/callback",
      "scopes": [],
      "client_id": "<BITBUCKET_OAUTH_CLIENT_ID>",
      "client_secret": "<BITBUCKET_OAUTH_CLIENT_SECRET>"
    }
  }'
```

**Important notes:**

- Bitbucket OAuth is completely separate from Atlassian 3LO -- different endpoints (`bitbucket.org` vs `auth.atlassian.com`)
- Bitbucket scopes are configured on the OAuth consumer, not passed in the authorization URL
- Access tokens expire after 1 hour; refresh tokens are included in responses
- Do **not** set an `issuer` field -- Bitbucket does not support OIDC discovery

## Tool Configuration

### Available Tools

| Category | Tool | Description |
|----------|------|-------------|
| **Repositories** | `bitbucket_list_repos` | List repositories in a workspace |
| | `bitbucket_get_repo` | Get repository details |
| | `bitbucket_search_code` | Search code across repositories |
| **Pull Requests** | `bitbucket_list_prs` | List pull requests for a repository |
| | `bitbucket_get_pr` | Get PR details with diff |
| | `bitbucket_create_pr` | Create a new pull request |
| | `bitbucket_merge_pr` | Merge a pull request |
| | `bitbucket_pr_comments` | List PR comments |
| **Pipelines** | `bitbucket_list_pipelines` | List pipeline runs |
| | `bitbucket_get_pipeline` | Get pipeline status |
| | `bitbucket_trigger_pipeline` | Trigger a pipeline run |

### Bitbucket OAuth Permissions

Permissions are configured on the OAuth consumer (not per-request):

| Permission | Access |
|------------|--------|
| `repository` | Read repository data |
| `repository:write` | Push to repositories |
| `pullrequest` | Read PRs and collaboration |
| `pullrequest:write` | Create, merge, decline PRs |
| `pipeline` | Read pipeline data |
| `pipeline:write` | Trigger pipeline runs |

## Creating a Virtual Server

Compose Bitbucket tools with Atlassian Rovo tools in a single virtual server:

```bash
# List all discovered tools
curl -s http://localhost:4444/tools \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" | jq '.[] | {id, name}'

# Create a combined virtual server
curl -X POST http://localhost:4444/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "server": {
      "name": "atlassian-full",
      "description": "Complete Atlassian suite - Jira, Confluence, Compass, and Bitbucket",
      "associated_tools": [
        "<JIRA_TOOL_ID>",
        "<CONFLUENCE_TOOL_ID>",
        "<BITBUCKET_LIST_REPOS_TOOL_ID>",
        "<BITBUCKET_LIST_PRS_TOOL_ID>"
      ],
      "visibility": "private"
    }
  }'
```

## Using Tools

After completing the OAuth consent flow, Bitbucket tools become available through the virtual server. Example interactions:

```bash
# List repositories in a workspace
curl -X POST http://localhost:4444/servers/admin-atlassian/call_tool \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "tool_name": "bitbucket_list_repos",
    "arguments": {"workspace": "my-workspace"}
  }'

# Get pull request details
curl -X POST http://localhost:4444/servers/admin-atlassian/call_tool \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "tool_name": "bitbucket_get_pr",
    "arguments": {"workspace": "my-workspace", "repo_slug": "my-repo", "pr_id": 42}
  }'
```

Each user's requests are authenticated with their own Bitbucket OAuth token, so tool results are scoped to their individual permissions.

## Security Considerations

1. **Separate OAuth Systems**: Bitbucket uses its own OAuth endpoints at `bitbucket.org`, completely independent of Atlassian 3LO at `auth.atlassian.com`
2. **Per-User Tokens**: Each user authenticates independently with their own Bitbucket permissions
3. **Destructive Tool Annotations**: The `bitbucket_merge_pr` tool is annotated with `destructiveHint: true` to prompt human confirmation before execution

## Troubleshooting

### OAuth Consumer Setup

- Ensure the OAuth consumer is created at the **workspace** level, not the repository level
- Verify the callback URL matches: `https://<MCF_DOMAIN>/oauth/callback`
- Check that required permissions (repository, pullrequest) are selected on the consumer

### Connection Issues

- The Bitbucket MCP server must be accessible from the MCF gateway container (same Docker network)
- Default server port is 8000 -- verify with `docker logs bitbucket-mcp-server`

## Additional Resources

- [Bitbucket Cloud REST API v2](https://developer.atlassian.com/cloud/bitbucket/rest/)
- [Bitbucket OAuth 2.0](https://support.atlassian.com/bitbucket-cloud/docs/use-oauth-on-bitbucket-cloud/)
- [MCP Gateway Documentation](../../../../index.md)
