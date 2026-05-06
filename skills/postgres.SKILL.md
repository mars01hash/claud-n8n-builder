---
name: postgres
type: skill
version: 1.0.0
authority: n8n Docs + VPS Best Practices
description: >
  Specialized skill for the Postgres node. Covers insert, select, update,
  and custom query operations with a focus on Docker/VPS networking.
---

# Skill: postgres

## 1. Node Metadata
- **Type**: `n8n-nodes-base.postgres`
- **Latest typeVersion**: 2.5
- **Credential Type**: `postgres`

## 2. Resource & Operation Mapping
| Intent | Operation | Key Parameters |
|---|---|---|
| "save to table X" | insert | `schema`, `table`, `columns` |
| "read from table X" | select | `table`, `where`, `limit` |
| "update record" | update | `table`, `columns`, `where` |
| "run custom SQL" | executeQuery | `query`, `options.queryParams` |

## 3. Optimized Expression Patterns
```javascript
// Mapping columns to $json fields (n8n does this automatically for inserts)
// But for custom queries use placeholders:
// SELECT * FROM users WHERE email = $1
// options.queryParams: "={{ $json[\"email\"] }}"

// Casting for UUID columns (common Postgres requirement)
"={{ 'CAST(' + $json[\"id\"] + ' AS UUID)' }}"
```

## 4. Agentic Tips & Best Practices
- **Tip 1: Hostname**: NEVER use `localhost`. In a Docker Compose environment, use the service name (e.g., `postgres` or `db`).
- **Tip 2: Batching**: For inserts involving more than 100 items, set `options.queryBatching` to `multiple` to improve performance.
- **Tip 3: Case Sensitivity**: Postgres table and column names are case-sensitive if quoted. Prefer lowercase snake_case for all DB identifiers.

## 5. Common Error Fixes
| Error | Root Cause | Fix |
|---|---|---|
| "ECONNREFUSED 127.0.0.1:5432" | Host set to localhost in Docker | Change host to `postgres` (service name). |
| "invalid input syntax for type uuid" | Passing string to UUID column | Use explicit CAST in the query or Set node. |

## 6. Security Hardening
- Use a dedicated n8n user in Postgres with only the minimum required permissions (SELECT/INSERT/UPDATE).
- Ensure Postgres is NOT exposed on the public network; it should only be on the `internal` Docker network.
