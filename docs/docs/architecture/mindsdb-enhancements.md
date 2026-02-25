# MindsDB Integration: Future Enhancements

!!! info "Status"
    These items are planned improvements to the MindsDB + Context Forge + LibreChat integration. The current deployment (Phases 1-8) provides a functional multi-tenant Knowledge Base system with six-layer security. The enhancements below add production hardening, automation, and advanced capabilities.

---

## Enhancement Summary

| # | Enhancement | Priority | Effort | Dependencies |
|---|------------|----------|--------|-------------|
| 1 | [KB Access Guard Plugin](#1-kb-access-guard-plugin) | High | Low (~80 LOC) | Plugin framework |
| 2 | [String-Literal-Aware SQL Sanitizer](#2-string-literal-aware-sql-sanitizer) | High | Medium | `sqlparse` library |
| 3 | [Query Audit Logging](#3-query-audit-logging) | High | Medium | Database migration |
| 4 | [Resource Limits](#4-resource-limits) | Medium | Low | Docker Compose |
| 5 | [HTTPS/TLS Termination](#5-httpstls-termination) | High (prod) | Low | Reverse proxy |
| 6 | [Team Provisioning Automation](#6-team-provisioning-automation) | Medium | Medium | All prior phases |
| 7 | [Custom MCP Server for MindsDB REST API](#7-custom-mcp-server-for-mindsdb-rest-api) | Medium | High | MCP server templates |
| 8 | [A2A Agent Registration](#8-a2a-agent-registration) | Low | Low | A2A support |
| 9 | [PGVector Upgrade](#9-pgvector-upgrade) | Medium | Medium | PostgreSQL |
| 10 | [Backup Strategy](#10-backup-strategy) | High (prod) | Low | Volume management |

---

## 1. KB Access Guard Plugin

**Problem:** The current sql_sanitizer blocks destructive SQL but does not prevent a legal agent from querying `hr_kb` if the LLM's instructions are bypassed via prompt injection.

**Approach:** Build a lightweight `TOOL_PRE_INVOKE` plugin (~80 lines) that validates the `FROM` clause targets only authorized Knowledge Bases for the requesting team.

**Architecture:**

```python
# plugins/kb_access_guard/kb_access_guard.py
class KBAccessGuardPlugin(Plugin):
    """Validates query tool invocations target only authorized KBs."""

    async def tool_pre_invoke(self, payload, context):
        if payload.tool_name != "query":
            return PluginResult(continue_processing=True)

        sql = payload.arguments.get("query", "")
        # Extract table names from FROM clause
        tables = extract_from_tables(sql)

        # Get allowed KBs from tool/server metadata (team_id mapping)
        allowed_kbs = self.config.get("team_kb_mapping", {}).get(
            context.team_id, []
        )

        for table in tables:
            if table not in allowed_kbs:
                return PluginResult(
                    continue_processing=False,
                    violation=f"Access denied: {table} is not authorized for team {context.team_id}"
                )

        return PluginResult(continue_processing=True)
```

**Configuration:**

```yaml
# plugins/config.yaml
kb_access_guard:
  enabled: true
  config:
    team_kb_mapping:
      legal: ["legal_kb"]
      hr: ["hr_kb"]
      engineering: ["eng_kb"]
```

**Dependencies:** Plugin framework (`TOOL_PRE_INVOKE` hook), `sqlparse` library for reliable table extraction.

**Files to create/modify:**

- `plugins/kb_access_guard/kb_access_guard.py` (new, ~80 LOC)
- `plugins/kb_access_guard/manifest.json` (new)
- `plugins/config.yaml` (add kb_access_guard section)

---

## 2. String-Literal-Aware SQL Sanitizer

**Problem:** The current sql_sanitizer uses regex `\b` word-boundary matching that cannot distinguish SQL keywords in actual SQL syntax from those appearing inside string literals. For example, `SELECT * FROM kb WHERE content = 'How to create a policy'` triggers `\bCREATE\b` on the word "create" in the search text.

**Approach:** Replace or augment the regex-based scanner with `sqlparse`-based tokenization that understands SQL structure.

**Implementation sketch:**

```python
import sqlparse

def find_issues_with_parser(sql: str, blocked: list[str]) -> list[str]:
    """Check SQL for blocked statements, ignoring string literals."""
    issues = []
    parsed = sqlparse.parse(sql)
    for statement in parsed:
        for token in statement.flatten():
            # Skip string literals and comments
            if token.ttype in (
                sqlparse.tokens.Literal.String.Single,
                sqlparse.tokens.Comment.Single,
                sqlparse.tokens.Comment.Multiline,
            ):
                continue
            # Check remaining tokens against blocked patterns
            for pattern in blocked:
                if re.search(pattern, str(token), re.IGNORECASE):
                    issues.append(f"Blocked statement: {token}")
    return issues
```

**Trade-offs:**

| Approach | Pros | Cons |
|----------|------|------|
| Current regex | Fast, zero dependencies | False positives in string literals |
| `sqlparse` tokenizer | Accurate, understands SQL structure | Adds dependency, slightly slower |
| Hybrid (regex first, sqlparse on match) | Best of both — fast path + accurate fallback | More complex code |

**Recommendation:** Hybrid approach. Keep the fast regex check as the first pass. If a violation is detected, run `sqlparse` to confirm it's not inside a string literal before blocking.

**Dependencies:** `sqlparse` Python package (add to `pyproject.toml`).

**Files to modify:**

- `plugins/sql_sanitizer/sql_sanitizer.py` (modify `_find_issues()`)
- `pyproject.toml` (add `sqlparse` dependency)

---

## 3. Query Audit Logging

**Problem:** No audit trail of which users executed which SQL queries through the MindsDB integration. Required for compliance in regulated environments.

**Approach:** Leverage the existing `TOOL_POST_INVOKE` hook and `AuditTrail` / `TokenUsageLog` database models to log all `query` tool invocations.

**Implementation options:**

### Option A: Plugin-based (recommended for initial deployment)

Create a lightweight audit plugin that logs to the existing `AuditTrail` table:

```python
# plugins/query_audit/query_audit.py
class QueryAuditPlugin(Plugin):
    async def tool_post_invoke(self, payload, context):
        if payload.tool_name == "query":
            log_entry = {
                "user": context.user_email,
                "team": context.team_id,
                "tool": "query",
                "sql": payload.arguments.get("query", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success" if not payload.error else "error",
            }
            # Write to AuditTrail table or structured log
            await self.audit_service.log(log_entry)
```

### Option B: Database model extension (for advanced analytics)

Extend the database with a dedicated `query_audit_log` table:

```python
# New Alembic migration
class QueryAuditLog(Base):
    __tablename__ = "query_audit_log"
    id = Column(Integer, primary_key=True)
    user_email = Column(String, nullable=False, index=True)
    team_id = Column(String, nullable=True, index=True)
    sql_query = Column(Text, nullable=False)
    target_kb = Column(String, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    status = Column(String, nullable=False)  # success, blocked, error
    blocked_by = Column(String, nullable=True)  # sql_sanitizer, kb_access_guard
    created_at = Column(DateTime, default=func.now(), index=True)
```

**Dependencies:** Plugin framework, database access. Option B requires an Alembic migration.

**Files to create/modify:**

- `plugins/query_audit/query_audit.py` (new)
- `plugins/query_audit/manifest.json` (new)
- `plugins/config.yaml` (add query_audit section)
- Option B: `mcpgateway/db.py` (add model), Alembic migration

---

## 4. Resource Limits

**Problem:** MindsDB container has no resource constraints, which could lead to memory exhaustion during large KB ingestion or complex queries.

**Approach:** Add Docker Compose resource limits.

```yaml
# docker-compose.yml — update mindsdb service
mindsdb:
  # ... existing config ...
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
      reservations:
        cpus: '1.0'
        memory: 2G
```

**Tuning guidance:**

| Workload | CPU | Memory | Notes |
|----------|-----|--------|-------|
| Small KB (< 1000 docs) | 2 cores | 4 GB | Sufficient for most teams |
| Medium KB (1000-10000 docs) | 4 cores | 8 GB | Recommended default |
| Large KB (10000+ docs) | 8 cores | 16 GB | Consider dedicated host |

**Files to modify:** `docker-compose.yml`

---

## 5. HTTPS/TLS Termination

**Problem:** MindsDB communication is unencrypted within Docker network. While internal traffic may be acceptable in some environments, production deployments should encrypt all traffic.

**Approaches:**

### Option A: Reverse proxy (recommended)

Add an Nginx or Traefik service in front of MindsDB:

```yaml
# docker-compose.yml
mindsdb-proxy:
  image: nginx:alpine
  volumes:
    - ./deployment/nginx/mindsdb.conf:/etc/nginx/conf.d/default.conf
    - ./certs:/etc/nginx/certs:ro
  ports:
    - "47334:443"
  networks: [mcpnet]
  depends_on: [mindsdb]
  profiles: ["mindsdb"]
```

### Option B: MindsDB native TLS

Mount TLS certificates into MindsDB via `config.json`:

```json
{
  "api": {
    "http": {
      "host": "0.0.0.0",
      "port": 47334,
      "ssl": true,
      "ssl_certfile": "/certs/cert.pem",
      "ssl_keyfile": "/certs/key.pem"
    }
  }
}
```

**Recommendation:** Option A provides more flexibility (certificate rotation, header injection, rate limiting) without depending on MindsDB's TLS implementation.

---

## 6. Team Provisioning Automation

**Problem:** Adding a new team requires 5 manual steps across 3 systems (MindsDB, Context Forge, LibreChat). This is error-prone and slow.

**Approach:** Create a provisioning script that automates the entire process.

```bash
#!/usr/bin/env bash
# scripts/provision-mindsdb-team.sh
# Usage: ./scripts/provision-mindsdb-team.sh <team_name> <display_name>
#
# Example: ./scripts/provision-mindsdb-team.sh engineering "Engineering"
#
# Steps automated:
# 1. Create Knowledge Base in MindsDB
# 2. Create Virtual Server in Context Forge (with stable UUID)
# 3. Generate LibreChat YAML snippet for MCP server entry
# 4. Generate LibreChat agent JSON for import
# 5. Print verification checklist
```

**What the script generates (but cannot auto-apply):**

- LibreChat `librechat.yaml` MCP server entry (printed for manual insertion)
- LibreChat agent JSON (printed for API import or Agent Builder)

**What the script executes directly:**

- MindsDB KB creation via SQL API
- Context Forge Virtual Server creation via REST API

**Dependencies:** `curl`, `jq`, access to MindsDB and Context Forge APIs.

**Files to create:** `scripts/provision-mindsdb-team.sh`

---

## 7. Custom MCP Server for MindsDB REST API

**Problem:** MindsDB's built-in MCP server only exposes 2 tools (`query`, `list_databases`). The full REST API supports file upload, KB management, agent queries, and more.

**Approach:** Build a custom MCP server using Context Forge's server templates that wraps MindsDB's REST API.

**Proposed tools:**

| Tool | MindsDB API | Description |
|------|------------|-------------|
| `upload_file` | `PUT /api/files/{name}` | Upload PDF/CSV/JSON |
| `create_knowledge_base` | SQL via `POST /api/sql/query` | Create a new KB |
| `insert_into_kb` | `PUT /api/projects/{p}/knowledge_bases/{name}` | Add data to KB |
| `search_kb` | SQL via `POST /api/sql/query` | Scoped semantic search |
| `list_knowledge_bases` | SQL via `POST /api/sql/query` | List available KBs |
| `query_agent` | `POST /api/projects/{p}/agents/{name}/completions` | Query a MindsDB agent |

**Starting point:** Use `mcp-servers/templates/` cookiecutter template to scaffold the server.

**Files to create:** `mcp-servers/mindsdb-extended/` (new MCP server package)

---

## 8. A2A Agent Registration

**Problem:** MindsDB exposes an A2A endpoint at `/a2a/` since September 2025, but it is not registered in Context Forge.

**Approach:** Register MindsDB as both an MCP server (existing) and an A2A agent, enabling agent-to-agent communication patterns.

```bash
# Register MindsDB A2A endpoint (when A2A support is stable)
curl -X POST http://context-forge:8000/a2a/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MCPGATEWAY_BEARER_TOKEN}" \
  -d '{
    "name": "mindsdb-agent",
    "url": "http://mindsdb:47334/a2a/",
    "description": "MindsDB AI agent for data analysis and KB queries",
    "capabilities": ["text2sql", "knowledge-base", "data-analysis"]
  }'
```

**Dependencies:** Context Forge A2A support maturity, MindsDB A2A endpoint stability.

---

## 9. PGVector Upgrade

**Problem:** MindsDB uses ChromaDB as the default vector store for Knowledge Bases. ChromaDB is suitable for development but may not scale well for production workloads.

**Approach:** Configure MindsDB to use PGVector (PostgreSQL with vector extension) for Knowledge Base storage.

```sql
-- Create KB with PGVector backend
CREATE KNOWLEDGE_BASE legal_kb
USING
    vector_store = {
        "engine": "pgvector",
        "connection_data": {
            "host": "postgres",
            "port": 5432,
            "database": "mindsdb_vectors",
            "user": "mindsdb",
            "password": "<PASSWORD>"
        }
    },
    embedding_model = { ... };
```

**Benefits:** Shared PostgreSQL infrastructure, better query performance at scale, ACID guarantees, standard backup tools.

**Dependencies:** PostgreSQL with `pgvector` extension installed.

---

## 10. Backup Strategy

**Problem:** The `mindsdb_data/` volume contains all Knowledge Base data, models, and configuration. Loss of this data requires full re-ingestion.

**Approach:**

### Docker volume backup

```bash
# Backup mindsdb_data volume
tar -czf mindsdb_backup_$(date +%Y%m%d).tar.gz ./mindsdb_data/

# Restore
tar -xzf mindsdb_backup_YYYYMMDD.tar.gz
```

### Kubernetes persistent volume

For Helm deployments, use a `PersistentVolumeClaim` with the cluster's storage class and snapshot capability.

### Recommended schedule

| Data Type | Backup Frequency | Retention |
|-----------|-----------------|-----------|
| KB data (vectors + metadata) | Daily | 30 days |
| MindsDB config | On change | 90 days |
| Full volume snapshot | Weekly | 90 days |

---

## Implementation Roadmap

```
Phase 9a (Immediate — production hardening):
├── #1  KB Access Guard Plugin
├── #4  Resource Limits
├── #5  HTTPS/TLS Termination
└── #10 Backup Strategy

Phase 9b (Short-term — compliance and quality):
├── #2  String-Literal-Aware SQL Sanitizer
├── #3  Query Audit Logging
└── #6  Team Provisioning Automation

Phase 9c (Medium-term — advanced capabilities):
├── #7  Custom MCP Server for MindsDB REST API
├── #9  PGVector Upgrade
└── #8  A2A Agent Registration
```

---

## Related Documentation

- [MindsDB Team Provisioning](../tutorials/mindsdb-team-provisioning.md) — Repeatable process for adding new teams
- [Security Features](security-features.md) — Full security model documentation
- [Plugin Framework](plugins.md) — Plugin development guide
- [Roadmap](roadmap.md) — Overall project roadmap
