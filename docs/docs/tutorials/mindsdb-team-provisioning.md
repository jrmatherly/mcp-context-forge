# MindsDB Team Provisioning

> Repeatable process for adding a new team to the MindsDB + Context Forge + LibreChat integration. Follow these steps each time a new department or team needs its own Knowledge Base and scoped agent.

---

## Prerequisites

Before provisioning a new team, ensure:

- MindsDB container is running and healthy (`docker compose --profile mindsdb ps`)
- Context Forge is running and accessible
- LibreChat is configured with the existing MindsDB integration
- You have admin tokens for both MindsDB (`MINDSDB_AUTH_TOKEN`) and Context Forge (`CONTEXT_FORGE_ADMIN_TOKEN`)
- The federated `query` tool ID is known (from initial gateway registration)

```bash
# Get the query tool ID if not already known
QUERY_TOOL_ID=$(curl -s http://context-forge:8000/tools \
  -H "Authorization: Bearer ${CONTEXT_FORGE_ADMIN_TOKEN}" | \
  jq -r '.[] | select(.federation_source == "mindsdb" and .name == "query") | .id')
echo "Query tool ID: ${QUERY_TOOL_ID}"
```

---

## Step 1: Create Knowledge Base in MindsDB

Connect to MindsDB and create a Knowledge Base for the new team.

```sql
-- Replace <team> with the team name (e.g., engineering, finance, marketing)
CREATE KNOWLEDGE_BASE <team>_kb
USING
    embedding_model = {
        "provider": "openai_azure",
        "model_name": "text-embedding-3-large",
        "api_key": "<AZURE_OPENAI_API_KEY>",
        "base_url": "<AZURE_OPENAI_ENDPOINT>",
        "api_version": "2024-02-01"
    },
    content_columns = ['content'],
    metadata_columns = ['source_file', 'department'];
```

!!! tip "Embedding Model"
    Adjust the embedding model configuration to match your deployment. OpenAI, Azure OpenAI, and HuggingFace models are supported. See MindsDB documentation for all options.

### Verify KB Creation

```sql
SHOW KNOWLEDGE_BASES;
-- Confirm <team>_kb appears in the list
```

---

## Step 2: Ingest Documents

Upload documents to the new team's Knowledge Base.

```bash
# Upload a PDF
curl -X PUT "http://localhost:47334/api/files/<team>_document_name" \
  -H "Authorization: Bearer ${MINDSDB_AUTH_TOKEN}" \
  -F "file=@/path/to/document.pdf"

# Insert the uploaded file into the KB
curl -X PUT "http://localhost:47334/api/projects/mindsdb/knowledge_bases/<team>_kb" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MINDSDB_AUTH_TOKEN}" \
  -d '{"knowledge_base": {"files": ["<team>_document_name"]}}'
```

!!! warning "PDF Limitations"
    MindsDB only supports searchable text PDFs. Scanned/image-only PDFs will not be ingested correctly.

### Verify Ingestion

```sql
SELECT * FROM <team>_kb WHERE content = 'test query' LIMIT 3;
-- Should return document chunks with relevance scores
```

---

## Step 3: Create Virtual Server in Context Forge

Generate a stable UUID for the new team and create a team-scoped Virtual Server.

```bash
# Generate a deterministic UUID from the team name (or choose your own)
# Convention: pad team name hex to fill UUID
TEAM_UUID="00000000-0000-0000-0000-$(printf '%012x' "$(echo -n '<team>' | od -A n -t x1 | tr -d ' \n' | head -c 12)")"

# Create the Virtual Server
curl -X POST http://context-forge:8000/servers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${CONTEXT_FORGE_ADMIN_TOKEN}" \
  -d '{
    "id": "'${TEAM_UUID}'",
    "name": "<team>-team-data",
    "description": "<Team Name> department Knowledge Base access. Query tool available for semantic search over <team> documents.",
    "tags": ["<team>", "knowledge-base"],
    "associated_tools": ["'${QUERY_TOOL_ID}'"],
    "team_id": "<team>",
    "visibility": "team"
  }'
```

**Key fields:**

| Field | Value | Purpose |
|-------|-------|---------|
| `id` | Stable UUID | Survives delete/recreate; used in LibreChat config |
| `associated_tools` | `[query_tool_id]` | Only the `query` tool (no `list_databases`) |
| `team_id` | Team identifier | Middleware enforces HTTP 403 for cross-team access |
| `visibility` | `"team"` | Only visible to users with matching team in JWT |

### Verify Virtual Server

```bash
# Confirm the server exists
curl -s http://context-forge:8000/servers/${TEAM_UUID} \
  -H "Authorization: Bearer ${CONTEXT_FORGE_ADMIN_TOKEN}" | jq '.name'
```

---

## Step 4: Add MCP Server Entry in LibreChat

Add the new team's Virtual Server to `librechat.yaml`:

```yaml
mcpServers:
  # ... existing entries ...

  mindsdb-<team>:
    type: sse
    url: 'http://context-forge:8000/servers/<TEAM_UUID>/sse'
    title: '<Team Name> Documents'
    description: 'Search <team name> department knowledge bases'
    timeout: 60000
    apiKey:
      source: admin
      authorization_type: bearer
      key: '${MCP_CONTEXT_FORGE_TOKEN}'
    startup: true
    chatMenu: false
    serverInstructions: |
      You have access to the <team name> department Knowledge Base.
      When the user asks a question, use the query tool to search for relevant documents.
      ALWAYS construct your query as:
        SELECT * FROM <team>_kb WHERE content = '<user question>'
      You may also filter by relevance:
        SELECT * FROM <team>_kb WHERE content = '<question>' AND relevance >= 0.5
      NEVER query any table or knowledge base other than <team>_kb.
      NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, GRANT, or REVOKE statements.
```

!!! note "chatMenu: false"
    This is a security requirement. Setting `chatMenu: false` prevents users from accessing the MCP server directly through the global dropdown, forcing access through the scoped agent only.

---

## Step 5: Create Scoped Agent in LibreChat

Create an agent via the Agent Builder UI or API:

```json
{
  "name": "<Team Name> Assistant",
  "description": "Search and answer questions from <team name> department documents",
  "instructions": "You are a <team name> assistant. You have access to the <team name> department's document knowledge base.\n\nWhen the user asks a question:\n1. Use the query tool to search: SELECT * FROM <team>_kb WHERE content = '<their question>'\n2. Review the returned document chunks and relevance scores\n3. Synthesize an answer citing specific documents\n4. If no relevant results, say so clearly\n\nYou can ONLY search the <team>_kb knowledge base. Do not attempt to query other databases or knowledge bases.",
  "provider": "azureOpenAI",
  "model": "<YOUR_DEPLOYMENT_NAME>",
  "tools": [],
  "mcpServerNames": ["mindsdb-<team>"]
}
```

Configure agent permissions to restrict visibility to the appropriate team members.

---

## Step 6: Verify End-to-End

Run these verification checks after provisioning:

| # | Check | Command/Action | Expected Result |
|---|-------|---------------|-----------------|
| 1 | KB exists | `SHOW KNOWLEDGE_BASES;` in MindsDB | `<team>_kb` listed |
| 2 | KB has data | `SELECT * FROM <team>_kb WHERE content = 'test' LIMIT 1;` | Returns chunks |
| 3 | VS accessible | `GET /servers/<TEAM_UUID>` with admin token | 200 OK |
| 4 | Team scoping | `GET /servers/<TEAM_UUID>` with wrong team token | 403 Forbidden |
| 5 | Agent visible | Log in as team member, check agent list | Agent appears |
| 6 | Agent isolated | Log in as different team, check agent list | Agent NOT visible |
| 7 | Query works | Ask agent a question about team documents | Returns relevant results |
| 8 | SQL blocked | Tell agent to "DROP TABLE <team>_kb" | Blocked by sql_sanitizer |

---

## Quick Reference: Security Layers per Team

Each provisioned team benefits from the full six-layer security model:

| Layer | Type | What It Prevents |
|-------|------|-----------------|
| Team-scoped Virtual Server | Hard | Cross-team access (HTTP 403) |
| Agent permissions | Hard | Wrong team seeing the agent |
| `chatMenu: false` | Hard | Direct MCP server access via UI |
| sql_sanitizer plugin | Hard | Destructive SQL (DROP, INSERT, etc.) |
| Agent instructions | Soft | Querying wrong KB (~95% effective) |
| serverInstructions | Soft | Additional KB-specific SQL guidance |

---

## Rollback

To remove a team's MindsDB integration:

1. **Delete the agent** in LibreChat (via Agent Builder UI)
2. **Remove the MCP server entry** from `librechat.yaml`
3. **Delete the Virtual Server** in Context Forge:
   ```bash
   curl -X DELETE http://context-forge:8000/servers/<TEAM_UUID> \
     -H "Authorization: Bearer ${CONTEXT_FORGE_ADMIN_TOKEN}"
   ```
4. **Drop the Knowledge Base** in MindsDB:
   ```sql
   DROP KNOWLEDGE_BASE <team>_kb;
   ```
5. **Restart LibreChat** to pick up the config change

---

## Automation Opportunity

For frequent team provisioning, consider creating a script that automates Steps 1-5. See the Phase 9 enhancements document for the planned team provisioning automation script.
