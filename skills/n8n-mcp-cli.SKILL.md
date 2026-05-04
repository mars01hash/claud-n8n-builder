---
name: n8n-mcp-cli
type: skill
version: 3.0.0
authority: Official n8n REST API (OpenAPI 3.0) + MCP Protocol Spec (2025-06-18)
description: >
  Production-grade reference for building, managing, and deploying n8n workflows.
  Covers the authoritative JSON schema (v1 execution order), complete node catalog
  with Resource Mapping logic, security-hardened credential handling, and Docker/VPS
  operational rules. Ground truth for all agents in this repository.
applies_to:
  - workflow-architect agent
  - n8n-enricher agent
  - query-navigator agent
  - all direct n8n JSON generation and API interaction tasks
---

# Skill: n8n-mcp-cli
## Grounded In
- n8n Public REST API — OpenAPI 3.0, base path `/api/v1`
- n8n Docs: docs.n8n.io/api/, docs.n8n.io/integrations/
- MCP Protocol Specification: modelcontextprotocol.io (2025-06-18)

---

## PART 1 — n8n REST API

### 1.1 Authentication

The n8n Public REST API authenticates exclusively via API key.

**Header (required on every request):**
```
X-N8N-API-KEY: <your-api-key>
```

**How to generate the key:**
n8n UI → Settings → n8n API → Create an API key

**Key Scope Rules:**
- Keys are scoped to the **user who created them** — not instance-wide by default
- Instance owners and admins can manage credentials and users
- Regular user keys can only manage their own workflows and executions
- Keys have no built-in expiry but should be rotated on a schedule (30–90 days)

**Base URL:**
```
https://<your-vps-domain>/api/v1
```

**Never** embed the API key in workflow JSON, node parameters, or committed files.
Store it as an environment variable: `N8N_API_KEY`

---

### 1.2 CRUD — Workflows

| Operation | Method | Path | Body / Params |
|---|---|---|---|
| List all | `GET` | `/workflows` | `?limit=25&cursor=<token>&active=true\|false` |
| Get one | `GET` | `/workflows/{id}` | — |
| Create | `POST` | `/workflows` | Full workflow JSON in body |
| Update | `PUT` | `/workflows/{id}` | Full workflow JSON in body |
| Delete | `DELETE` | `/workflows/{id}` | — |
| Activate | `POST` | `/workflows/{id}/activate` | — |
| Deactivate | `POST` | `/workflows/{id}/deactivate` | — |

**Pagination:** List endpoints return `{ data: [...], nextCursor: "..." }`. Pass `cursor` from `nextCursor` to fetch the next page. Loop until `nextCursor` is null.

**Create/Update body:** The complete workflow JSON object (see Part 2).

---

### 1.3 CRUD — Executions

| Operation | Method | Path | Params |
|---|---|---|---|
| List | `GET` | `/executions` | `?workflowId=&status=success\|error\|waiting&limit=20` |
| Get one | `GET` | `/executions/{id}` | `?includeData=true` for full node output |
| Delete | `DELETE` | `/executions/{id}` | — |
| Run workflow | `POST` | `/workflows/{id}/run` | `{ "startNodes": [], "destinationNode": "" }` |

---

### 1.4 CRUD — Credentials

| Operation | Method | Path | Notes |
|---|---|---|---|
| List | `GET` | `/credentials` | Secrets are **never** returned |
| Get schema | `GET` | `/credentials/schema/{type}` | Returns the JSON Schema for a credential type |
| Create | `POST` | `/credentials` | Body: `{ name, type, data: { ...fields } }` |
| Delete | `DELETE` | `/credentials/{id}` | — |

**Critical:** The `GET /credentials` response never exposes secret values. Credential IDs
returned here are what you embed in workflow JSON under `credentials`.

---

### 1.5 Bash Reference — Common API Calls

```bash
# List all workflows
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://$N8N_HOST/api/v1/workflows | jq '.data[] | {id, name, active}'

# Create workflow from file
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @workflow.json \
  https://$N8N_HOST/api/v1/workflows

# Activate a workflow
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://$N8N_HOST/api/v1/workflows/<id>/activate

# Trigger a manual run
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}' \
  https://$N8N_HOST/api/v1/workflows/<id>/run

# Get last 5 failed executions for a workflow
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "https://$N8N_HOST/api/v1/executions?workflowId=<id>&status=error&limit=5" \
  | jq '.data[] | {id, startedAt, stoppedAt}'

# Get credential schema for Slack OAuth2
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://$N8N_HOST/api/v1/credentials/schema/slackOAuth2Api | jq .
```

---

## PART 2 — Authoritative Workflow JSON Schema (Execution Order v1)

This is the canonical structure that n8n expects for import and API creation.
**Every generated workflow.json must conform to this exactly.**

### 2.1 Top-Level Object

```json
{
  "name": "string — workflow display name (required)",
  "nodes": "array<NodeObject> (required)",
  "connections": "ConnectionsMap (required)",
  "active": false,
  "settings": "WorkflowSettings",
  "staticData": null,
  "tags": [],
  "pinData": {},
  "versionId": "UUID v4 string",
  "meta": {
    "templateCredsSetupCompleted": false,
    "instanceId": ""
  }
}
```

**Field rules:**
- `active`: Always `false` on generation. User activates after import.
- `staticData`: Use `null` unless the workflow uses `$getWorkflowStaticData()`.
- `pinData`: Map of `{ "Node Name": [{ "json": {...} }] }` for dev-time data pinning.
- `versionId`: Generate a fresh UUID v4. n8n uses this for change tracking.
- `meta.instanceId`: Leave empty — n8n populates this on import.

### 2.2 WorkflowSettings Object

```json
{
  "settings": {
    "executionOrder": "v1",
    "saveManualExecutions": true,
    "saveDataErrorExecution": "all",
    "saveDataSuccessExecution": "none",
    "executionTimeout": -1,
    "timezone": "UTC",
    "callerPolicy": "workflowsFromSameOwner",
    "errorWorkflow": ""
  }
}
```

**Key settings:**
- `executionOrder`: Always `"v1"` — this is the stable execution model.
- `saveDataSuccessExecution`: Set to `"all"` only during debugging; use `"none"` in production to control storage.
- `errorWorkflow`: Optionally set to another workflow ID to catch failures.
- `timezone`: Must match container's `GENERIC_TIMEZONE` env var.

### 2.3 NodeObject — Complete Field Specification

```json
{
  "id": "UUID v4 — unique per node within this workflow",
  "name": "Human Readable Label — unique within workflow",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [480, 300],
  "parameters": {},
  "credentials": {
    "<credentialTypeName>": {
      "id": "REPLACE_WITH_CREDENTIAL_ID",
      "name": "Display name as stored in n8n"
    }
  },
  "disabled": false,
  "webhookId": "UUID v4 — only for webhook trigger nodes",
  "notes": "",
  "notesInFlow": false,
  "onError": "stopWorkflow",
  "retryOnFail": false,
  "maxTries": 3,
  "waitBetweenTries": 1000,
  "alwaysOutputData": false,
  "executeOnce": false,
  "continueOnFail": false
}
```

**Field rules:**
- `id`: Generate a fresh UUID v4 for each node. Never reuse across nodes.
- `name`: Must be unique within the workflow. Use descriptive names like `"Fetch User Record"` not `"Postgres1"`.
- `webhookId`: Only include on `n8n-nodes-base.webhook` and `n8n-nodes-base.executeWorkflowTrigger` nodes.
- `onError`: `"stopWorkflow"` | `"continueRegularOutput"` | `"continueErrorOutput"`. Use `"continueErrorOutput"` to route errors to a dedicated branch.
- `credentials`: Omit entirely if the node requires no credentials (e.g., Set, IF, Code nodes).

### 2.4 ConnectionsMap — Authoritative Format

The connections object defines directed edges between nodes.
Source node name → output port index → array of target edges.

```json
{
  "connections": {
    "Source Node Name": {
      "main": [
        [
          {
            "node": "Target Node Name",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

**Structural rules:**
- The outer key is the **source node's exact `name` field**.
- `"main"` is the connection type. Always `"main"` for standard data flow.
  Other types: `"ai_tool"`, `"ai_memory"`, `"ai_languageModel"`, `"ai_document"`, `"ai_embedding"` (only for LangChain AI nodes).
- The outer array index = **output port number** (0-based).
  - IF node: index 0 = true branch, index 1 = false branch.
  - Switch node: index 0 = rule 1, index 1 = rule 2, etc.
  - splitInBatches: index 0 = loop body, index 1 = done.
- The inner array = **all targets from that port** (fanout/broadcast).

**Multi-branch example (IF node):**
```json
"Check Status": {
  "main": [
    [{ "node": "Handle Active",  "type": "main", "index": 0 }],
    [{ "node": "Handle Inactive","type": "main", "index": 0 }]
  ]
}
```

**Fan-out (one source → multiple targets):**
```json
"Webhook": {
  "main": [
    [
      { "node": "Log to DB",    "type": "main", "index": 0 },
      { "node": "Notify Slack", "type": "main", "index": 0 }
    ]
  ]
}
```

**Loop back (splitInBatches):**
```json
"Process Item": {
  "main": [
    [{ "node": "Loop Over Items", "type": "main", "index": 0 }]
  ]
}
```

### 2.5 Data Item Format (Inter-Node Data)

n8n passes data between nodes as an array of items:

```json
[
  {
    "json": {
      "fieldName": "value",
      "nested": { "key": "value" }
    },
    "binary": {
      "data": {
        "data": "base64string",
        "mimeType": "application/pdf",
        "fileName": "report.pdf",
        "fileSize": 12345
      }
    },
    "pairedItem": { "item": 0 }
  }
]
```

**Access in expressions:**
- Current item: `$json["fieldName"]` or `$json.fieldName`
- Binary data: `$binary["data"]`
- Specific node output: `$("Node Name").first().json["field"]`
- All items from node: `$("Node Name").all()`
- Item index: `$itemIndex`

---

## PART 3 — Resource Mapping: Natural Language → n8n Parameters

This section defines how Claude translates a user's plain-English request into
the exact n8n node type, operation, and parameter values.

### 3.1 Mapping Decision Table

| User Says | Node Type | Resource | Operation | Key Parameters |
|---|---|---|---|---|
| "when a POST arrives at /lead" | `n8n-nodes-base.webhook` | — | — | `httpMethod: POST`, `path: lead` |
| "every day at 9am" | `n8n-nodes-base.scheduleTrigger` | — | — | `cronExpression: 0 9 * * *` |
| "call the API at https://..." | `n8n-nodes-base.httpRequest` | — | — | `method`, `url`, `authentication` |
| "save to Postgres table X" | `n8n-nodes-base.postgres` | — | `insert` | `schema`, `table`, `columns` |
| "read from Postgres" | `n8n-nodes-base.postgres` | — | `select` | `table`, `where`, `limit` |
| "send a Slack message" | `n8n-nodes-base.slack` | `message` | `post` | `channel`, `text` |
| "send an email" | `n8n-nodes-base.emailSend` | — | — | `to`, `subject`, `text\|html` |
| "if field equals X" | `n8n-nodes-base.if` | — | — | `conditions`, `combinator` |
| "route based on status field" | `n8n-nodes-base.switch` | — | — | `mode: rules`, `rules` |
| "map / rename fields" | `n8n-nodes-base.set` | — | — | `mode: manual`, `fields.values` |
| "run JavaScript" | `n8n-nodes-base.code` | — | — | `language: javaScript`, `jsCode` |
| "loop over list" | `n8n-nodes-base.splitInBatches` | — | — | `batchSize` |
| "merge two branches" | `n8n-nodes-base.merge` | — | — | `mode` |
| "respond to webhook caller" | `n8n-nodes-base.respondToWebhook` | — | — | `respondWith`, `responseBody` |
| "pause / wait" | `n8n-nodes-base.wait` | — | — | `resume` |
| "read from Google Sheets" | `n8n-nodes-base.googleSheets` | `sheet` | `read` | `documentId`, `sheetName` |
| "write to Google Sheets" | `n8n-nodes-base.googleSheets` | `sheet` | `appendOrUpdate` | `documentId`, `sheetName`, `columns` |
| "do nothing / placeholder" | `n8n-nodes-base.noOp` | — | — | *(none)* |

### 3.2 HTTP Request — Auth Header Mapping

Translate user's authentication intent to the exact `httpRequest` parameters:

```
User says: "send bearer token"
→ authentication: "genericCredentialType"
  genericAuthType: "httpBearerAuth"
  credentials.httpBearerAuth: { id: "REPLACE_WITH_CREDENTIAL_ID", name: "..." }

User says: "use Basic auth"
→ authentication: "genericCredentialType"
  genericAuthType: "httpBasicAuth"
  credentials.httpBasicAuth: { id: "REPLACE_WITH_CREDENTIAL_ID", name: "..." }

User says: "send API key in header X-API-Key"
→ authentication: "genericCredentialType"
  genericAuthType: "httpHeaderAuth"
  credentials.httpHeaderAuth: { id: "REPLACE_WITH_CREDENTIAL_ID", name: "..." }

User says: "use OAuth2"
→ authentication: "genericCredentialType"
  genericAuthType: "oAuth2Api"
  credentials.oAuth2Api: { id: "REPLACE_WITH_CREDENTIAL_ID", name: "..." }

User says: "no auth / public API"
→ authentication: "none"
  (no credentials field)
```

**HTTP Request — Body Type Mapping:**
```
User says "send JSON body"
→ sendBody: true, bodyContentType: "json"
  bodyParameters.parameters: [{ name: "key", value: "={{ $json[\"val\"] }}" }]

User says "send form data"
→ sendBody: true, bodyContentType: "form-urlencoded"

User says "send raw/text"
→ sendBody: true, bodyContentType: "raw"
  body: "raw string content"

User says "upload a file"
→ sendBody: true, bodyContentType: "binaryData"
  inputDataFieldName: "data"
```

### 3.3 Postgres — SQL Synthesis Rules

```
User says "get all users where active = true"
→ operation: "select"
  table: { value: "users", mode: "string" }
  where: { values: [{ column: "active", condition: "equal", value: true }] }
  options: { limit: 1000 }

User says "insert a new lead"
→ operation: "insert"
  schema: { value: "public", mode: "string" }
  table: { value: "leads", mode: "string" }
  columns: "email,name,source,created_at"
  (n8n maps columns to $json fields by name automatically)

User says "update status to 'processed' where id matches"
→ operation: "update"
  table: { value: "leads", mode: "string" }
  columns: "status"
  where: { values: [{ column: "id", condition: "equal", value: "={{ $json[\"id\"] }}" }] }

User says "run a custom SQL query"
→ operation: "executeQuery"
  query: "SELECT u.*, o.total FROM users u JOIN orders o ON u.id = o.user_id WHERE o.total > $1"
  options: { queryParams: "={{ $json[\"minTotal\"] }}" }
```

**Postgres credential type:** `"postgres"` (not `postgresApi` — that was a deprecated name)

### 3.4 Schedule Trigger — Cron Expression Mapping

```
"every minute"        → */1 * * * *
"every 15 minutes"    → */15 * * * *
"every hour"          → 0 * * * *
"every day at 9am"    → 0 9 * * *
"weekdays at 8:30am"  → 30 8 * * 1-5
"every Sunday at 2am" → 0 2 * * 0
"first day of month"  → 0 0 1 * *
```

Always use `field: "cronExpression"` in the `rule.interval` array, not `field: "hours"` or `field: "minutes"` — the cron form is more reliable for complex schedules.

### 3.5 IF / Switch — Condition Operator Mapping

```
User says "equals"           → operation: "equals"
User says "not equal"        → operation: "notEquals"
User says "contains"         → operation: "contains"        (string)
User says "starts with"      → operation: "startsWith"
User says "ends with"        → operation: "endsWith"
User says "is empty"         → operation: "isEmpty"
User says "exists / not null"→ operation: "isNotEmpty"
User says "greater than"     → operation: "gt"              (number)
User says "less than"        → operation: "lt"
User says "is in list"       → operation: "in"              (array)
User says "regex matches"    → operation: "regex"
```

Always set `operator.type` to match the data type:
`"string"` | `"number"` | `"boolean"` | `"dateTime"` | `"array"` | `"object"`

---

## PART 4 — Expression Reference

### 4.1 Syntax Rules
- Expressions are JavaScript, wrapped in `={{ }}` inside string values in JSON.
- Single expression per field (no template literals mixing text and `{{ }}`).
- Exception: static text + expression: `"={{ 'Hello ' + $json[\"name\"] }}"`

### 4.2 Canonical Expression Patterns

```javascript
// ── Current item ──────────────────────────────────────────────
$json["field"]                           // safe bracket notation
$json.field                              // dot notation (avoid for keys with spaces)
$json["nested"]["key"]                   // nested access
$json["arr"][0]                          // array index

// ── Cross-node references ──────────────────────────────────────
$("Node Name").first().json["field"]     // first item from named node
$("Node Name").last().json["field"]      // last item
$("Node Name").all()                     // full array of items
$("Node Name").item.json["field"]        // paired item (use in runOnceForEachItem)

// ── Workflow / execution context ───────────────────────────────
$workflow.id
$workflow.name
$execution.id
$execution.mode                          // "manual" | "trigger"
$vars.myVariable                         // workflow-level variables (set in n8n UI)

// ── DateTime (Luxon) ───────────────────────────────────────────
$now.toISO()                             // "2025-01-15T09:30:00.000Z"
$now.toFormat('yyyy-MM-dd')             // "2025-01-15"  (Luxon uses lowercase y/d)
$today.toISO()                           // midnight UTC today
$now.plus({ days: 7 }).toISO()
$now.minus({ hours: 2 }).toISO()
$now.startOf('month').toISO()
DateTime.fromISO($json["dateStr"]).toFormat('yyyy-MM-dd')

// ── Utility ────────────────────────────────────────────────────
$if($json["active"], "yes", "no")
$isEmpty($json["field"])                 // true if null/undefined/empty string/[]
$isNotEmpty($json["field"])
$exists($json["field"])
$json["items"].length
JSON.stringify($json["obj"])
JSON.parse($json["jsonString"])

// ── Item position ─────────────────────────────────────────────
$itemIndex                               // 0-based position in current batch
$runIndex                                // how many times this node has run (for loops)
```

### 4.3 DateTime Format Tokens (Luxon — NOT moment.js)
```
yyyy  → 4-digit year       (NOT YYYY)
MM    → 2-digit month
dd    → 2-digit day         (NOT DD)
HH    → 24-hour hour
mm    → minutes
ss    → seconds
```
**Common mistake:** Using `YYYY-MM-DD` (moment.js) in n8n generates wrong output — always use `yyyy-MM-dd`.

---

## PART 5 — Security Protocol (Docker / VPS)

### 5.1 Credential Handling — Non-Negotiable Rules

1. **Never** put API keys, passwords, tokens, or connection strings in `parameters` or anywhere in workflow JSON.
2. **Always** use n8n's built-in credential store. Reference credentials by:
   ```json
   "credentials": {
     "credentialTypeName": {
       "id": "REPLACE_WITH_CREDENTIAL_ID",
       "name": "Human-readable name as stored in n8n"
     }
   }
   ```
3. Credential IDs are environment-specific. Use `REPLACE_WITH_CREDENTIAL_ID` as a placeholder in generated JSON — the user substitutes the real ID after import.
4. The `GET /credentials` API endpoint **never returns secret values** — only metadata.

### 5.2 Docker Secrets — Storage Hierarchy

```
MOST SECURE ──────────────────────────────────────────────── LEAST SECURE
Docker secrets   External vault   n8n credential store   Env vars   Workflow JSON
(docker secret)  (Vault/AWS SM)   (AES-256 encrypted)    (.env)     ← NEVER
```

**Recommended for VPS Docker deployment:**
```yaml
# docker-compose.yml — secrets via environment variables loaded from .env
services:
  n8n:
    env_file: .env   # ← lives outside the repo, in /opt/n8n/.env
    environment:
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}   # encrypts credential store
```

```bash
# /opt/n8n/.env (600 permissions, not in git)
N8N_ENCRYPTION_KEY=<32-char random string>
N8N_API_KEY=<your-api-key>
DB_POSTGRESDB_PASSWORD=<strong-password>
```

### 5.3 n8n Encryption Key

The `N8N_ENCRYPTION_KEY` environment variable is the master key that AES-256 encrypts all credentials stored in n8n's database.

**Critical rules:**
- Generate once: `openssl rand -hex 32`
- Back it up immediately — losing it means losing all stored credentials
- Never change it after credentials are stored (they become unreadable)
- Rotate only by: export all credentials → change key → re-enter all credentials

### 5.4 Network Security (Docker Compose)

```yaml
# Isolate n8n on an internal network; only expose the HTTPS port
networks:
  internal:
    driver: bridge
  web:
    external: true  # your reverse proxy network (Traefik/Nginx)

services:
  n8n:
    networks: [internal, web]
  postgres:
    networks: [internal]   # postgres is NEVER on the web network
```

**Reverse proxy rules for n8n:**
- Always terminate TLS at the proxy (Traefik/Nginx Proxy Manager)
- n8n runs on port 5678 internally — never expose 5678 directly
- Set `N8N_PROTOCOL=https` and `N8N_HOST=yourdomain.com` so webhook URLs generate correctly

### 5.5 API Key Rotation Protocol

```bash
# 1. Generate new key in n8n UI: Settings → API → Create API Key
# 2. Update .env on VPS
sed -i "s/^N8N_API_KEY=.*/N8N_API_KEY=<new-key>/" /opt/n8n/.env
# 3. Restart n8n
docker compose -f /opt/n8n/docker-compose.yml up -d n8n
# 4. Revoke old key in n8n UI
# 5. Update any scripts/CI that reference the old key
```

### 5.6 Webhook Security

For production webhooks:
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "ingest-lead",
    "authentication": "headerAuth",
    "responseMode": "responseNode",
    "options": {
      "allowedOrigins": "https://yourdomain.com",
      "ignoreBots": true,
      "rawBody": false
    }
  },
  "credentials": {
    "httpHeaderAuth": {
      "id": "REPLACE_WITH_CREDENTIAL_ID",
      "name": "Webhook HMAC Secret"
    }
  }
}
```
- Use header authentication (HMAC signature preferred) on all public-facing webhooks
- Never use `path: test` or predictable paths in production
- Set `allowedOrigins` to the specific calling domain if known

---

## PART 6 — TypeVersion Reference (Current as of n8n ≥ 1.40)

| Node Type | Latest typeVersion | Notes |
|---|---|---|
| `n8n-nodes-base.manualTrigger` | 1 | |
| `n8n-nodes-base.scheduleTrigger` | 1.2 | |
| `n8n-nodes-base.webhook` | 2 | Adds `webhookId` field |
| `n8n-nodes-base.executeWorkflowTrigger` | 1.1 | |
| `n8n-nodes-base.httpRequest` | 4.2 | v4+ required for pagination |
| `n8n-nodes-base.set` | 3.4 | v3+ uses `fields.values` array |
| `n8n-nodes-base.if` | 2.2 | v2+ uses `conditions.conditions` array |
| `n8n-nodes-base.switch` | 3.2 | v3+ uses `rules.values` array |
| `n8n-nodes-base.code` | 2 | v2 = multi-mode JS/Python |
| `n8n-nodes-base.merge` | 3 | |
| `n8n-nodes-base.splitInBatches` | 3 | |
| `n8n-nodes-base.postgres` | 2.5 | v2+ uses new schema object format |
| `n8n-nodes-base.mysql` | 2.4 | |
| `n8n-nodes-base.googleSheets` | 4.5 | |
| `n8n-nodes-base.slack` | 2.2 | |
| `n8n-nodes-base.emailSend` | 2.1 | |
| `n8n-nodes-base.respondToWebhook` | 1.1 | |
| `n8n-nodes-base.wait` | 1.1 | |
| `n8n-nodes-base.noOp` | 1 | |
| `n8n-nodes-base.executeWorkflow` | 1.1 | |
| `n8n-nodes-base.stickyNote` | 1 | UI annotation only |

**Rule:** When in doubt about the typeVersion for a lesser-known node, use `1` and flag it for the user to verify in their n8n instance.

---

## PART 7 — Node Parameter Templates (Production-Ready)

### 7.1 Webhook Trigger
```json
{
  "id": "REPLACE_UUID",
  "name": "Receive Webhook",
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 2,
  "position": [240, 300],
  "webhookId": "REPLACE_UUID",
  "parameters": {
    "httpMethod": "POST",
    "path": "REPLACE_PATH",
    "responseMode": "responseNode",
    "options": {
      "allowedOrigins": "*",
      "ignoreBots": true
    }
  }
}
```

### 7.2 HTTP Request (with JSON body + Bearer auth)
```json
{
  "id": "REPLACE_UUID",
  "name": "Call External API",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [480, 300],
  "parameters": {
    "method": "POST",
    "url": "https://api.example.com/endpoint",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpBearerAuth",
    "sendBody": true,
    "bodyContentType": "json",
    "bodyParameters": {
      "parameters": [
        { "name": "email",  "value": "={{ $json[\"email\"] }}" },
        { "name": "source", "value": "n8n-automation" }
      ]
    },
    "options": {
      "timeout": 10000,
      "response": {
        "response": { "fullResponse": false, "neverError": false }
      }
    }
  },
  "credentials": {
    "httpBearerAuth": { "id": "REPLACE_WITH_CREDENTIAL_ID", "name": "API Bearer Token" }
  },
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 2000,
  "onError": "continueErrorOutput"
}
```

### 7.3 Set Fields (v3.4)
```json
{
  "id": "REPLACE_UUID",
  "name": "Map Output Fields",
  "type": "n8n-nodes-base.set",
  "typeVersion": 3.4,
  "position": [720, 300],
  "parameters": {
    "mode": "manual",
    "duplicateItem": false,
    "fields": {
      "values": [
        { "name": "email",      "value": "={{ $json[\"body\"][\"email\"] }}" },
        { "name": "source",     "value": "webhook" },
        { "name": "created_at", "value": "={{ $now.toISO() }}" }
      ]
    },
    "options": { "dotNotation": true }
  }
}
```

### 7.4 IF Condition (v2.2)
```json
{
  "id": "REPLACE_UUID",
  "name": "Check Status",
  "type": "n8n-nodes-base.if",
  "typeVersion": 2.2,
  "position": [960, 300],
  "parameters": {
    "conditions": {
      "options": { "caseSensitive": false, "typeValidation": "strict" },
      "conditions": [
        {
          "id": "REPLACE_UUID",
          "leftValue": "={{ $json[\"status\"] }}",
          "rightValue": "active",
          "operator": { "type": "string", "operation": "equals" }
        }
      ],
      "combinator": "and"
    },
    "options": {}
  }
}
```

### 7.5 Postgres Insert (v2.5)
```json
{
  "id": "REPLACE_UUID",
  "name": "Insert Lead to Postgres",
  "type": "n8n-nodes-base.postgres",
  "typeVersion": 2.5,
  "position": [1200, 300],
  "parameters": {
    "operation": "insert",
    "schema": { "value": "public", "mode": "string" },
    "table":  { "value": "leads",  "mode": "string" },
    "columns": "email,source,created_at",
    "options": {
      "queryBatching": "multiple",
      "outputLargeNumbers": "numbers"
    }
  },
  "credentials": {
    "postgres": { "id": "REPLACE_WITH_CREDENTIAL_ID", "name": "Postgres VPS" }
  },
  "continueOnFail": false,
  "onError": "continueErrorOutput"
}
```

### 7.6 Respond to Webhook
```json
{
  "id": "REPLACE_UUID",
  "name": "Send Response",
  "type": "n8n-nodes-base.respondToWebhook",
  "typeVersion": 1.1,
  "position": [1440, 300],
  "parameters": {
    "respondWith": "json",
    "responseBody": "={{ JSON.stringify({ success: true, id: $json[\"id\"] }) }}",
    "options": {
      "responseCode": 201,
      "responseHeaders": {
        "entries": [{ "name": "Content-Type", "value": "application/json" }]
      }
    }
  }
}
```

---

## PART 8 — Pre-Import Checklist

Before any workflow.json is finalized or submitted to the n8n API:

| # | Check | Expected |
|---|---|---|
| 1 | `active` field | `false` |
| 2 | All node `id` values | Unique UUID v4s |
| 3 | All node `name` values | Unique within workflow |
| 4 | All connection source keys | Match a `name` in `nodes` |
| 5 | All connection target `node` values | Match a `name` in `nodes` |
| 6 | Every non-trigger node | Has at least one incoming connection |
| 7 | Trigger node(s) | Zero incoming connections |
| 8 | No credentials contain | Real secret values |
| 9 | All `typeVersion` values | Match the TypeVersion Reference |
| 10 | `executionOrder` | `"v1"` |
| 11 | Webhook nodes | Have a `webhookId` UUID |
| 12 | DateTime expressions | Use Luxon format tokens (lowercase `yyyy`) |
