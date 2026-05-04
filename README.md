# claud-n8n-builder

A structured MCP Skill Repository that gives Claude a deterministic pipeline for building, validating, and managing [n8n](https://n8n.io) workflows on a self-hosted Docker VPS.

Without this system, Claude guesses n8n's JSON format on every request. With it, every automation request flows through a three-agent pipeline that always produces valid, importable workflow files.

---

## How It Works

Every automation request flows through three agents in sequence:

```
User Request
    │
    ▼
query-navigator     (ROUTE)    → classifies intent, checks catalog, dispatches
    │
    ▼
n8n-enricher        (ENRICH)   → resolves node types, credentials, expressions
    │
    ▼
workflow-architect  (EXECUTE)  → generates workflow.json + guide.md + node files
```

Each request produces a ready-to-import workflow package:

```
WORKSPACE_ROOT/workflows/My-Workflow-Name/
├── workflow.json          ← Drop directly into n8n (File → Import)
├── guide.md               ← Human-readable explanation
└── nodes/
    ├── receive_webhook.json
    ├── receive_webhook.guide.md
    ├── insert_lead_to_postgres.json
    └── insert_lead_to_postgres.guide.md
```

---

## Repository Structure

```
claud-n8n-builder/
│
├── CLAUDE.md                        ← Auto-loaded by Claude Code as context
├── ARCHITECTURE.md                  ← Full system design reference
│
├── skills/
│   └── n8n-mcp-cli.SKILL.md         ← Ground truth: API, schema, node catalog, security
│
├── agents/
│   ├── query-navigator.agent.md     ← ROUTE: intent classification and dispatch
│   ├── n8n-enricher.agent.md        ← ENRICH: doc retrieval and spec building
│   └── workflow-architect.agent.md  ← EXECUTE: JSON generation pipeline
│
├── hooks/
│   ├── block-invalid-nodes          ← Python: pre-save JSON validator (23 rules)
│   └── catalog-check                ← Python: semantic duplicate detector
│
├── scripts/
│   └── extract_workflow.py          ← Python: decompose workflow.json into node files
│
├── templates/
│   └── scaffolding/
│       ├── webhook-workflow.json    ← Pattern: POST → process → respond
│       ├── http-request-workflow.json ← Pattern: schedule → fetch → filter
│       └── loop-workflow.json       ← Pattern: batch → loop → done
│
└── WORKSPACE_ROOT/
    ├── workflow-catalog.md          ← Master keyword index of all built workflows
    └── workflows/                   ← All generated workflow packages land here
```

---

## Three-Layer Architecture

| Layer | Files | Responsibility |
|---|---|---|
| **Skill** | `skills/n8n-mcp-cli.SKILL.md` | API spec, JSON schema, node catalog, security rules — ground truth read by all agents |
| **Agents** | `agents/*.agent.md` | Intent classification, doc retrieval, JSON generation — the intelligence layer |
| **Toolchain** | `hooks/`, `scripts/` | Validation, duplicate detection, node extraction — automation layer |

---

## Agents

### query-navigator (ROUTE)

Receives a natural language request, classifies it into one of six intents, checks the workflow catalog for duplicates, and routes to the correct next step.

| Intent | Trigger words | Action |
|---|---|---|
| `BUILD_NEW` | "create", "build", "automate" | Catalog check → route to enricher |
| `LOOKUP_EXISTING` | "show me", "find", "do we have" | Read catalog → return top matches |
| `MODIFY_WORKFLOW` | "update", "add a step", "fix node" | Identify workflow → delegate to extract script |
| `EXPLAIN_CONCEPT` | "how does", "what is", "explain" | Answer inline |
| `DEBUG_WORKFLOW` | "failing", "error", "not working" | Route to enricher in diagnostic mode |
| `IMPORT_EXPORT` | "export JSON", "import this" | Route to extract script |

Produces a **Navigator Memo** before any action:

```
NAVIGATOR MEMO
──────────────
Input       : "build a workflow that sends a Slack alert when a new row is inserted into orders"
Intent      : BUILD_NEW
Confidence  : 92%
Target      : Order Insert Slack Alert
Catalog Hit : NO
Next Agent  : n8n-enricher
──────────────
```

### n8n-enricher (ENRICH)

Resolves every node type, typeVersion, credential type, and parameter mapping needed to build the workflow. For nodes not in the core catalog, it fetches live documentation from `docs.n8n.io` via MCP tools.

Produces a structured **Enrichment Spec YAML** that is the precise hand-off to the Architect:

```yaml
workflow_name: "Order Insert Slack Alert"
trigger:
  node_type: "n8n-nodes-base.postgresTrigger"
  type_version: 1
  params:
    tableName: orders
    triggerOn: insert
steps:
  - step: 1
    node_type: "n8n-nodes-base.slack"
    type_version: 2.2
    credential:
      type: "slackOAuth2Api"
      placeholder_name: "Slack Bot"
    params:
      resource: message
      operation: post
      channel: "#orders"
connections:
  - from: "Postgres Trigger"
    to: "Send Slack Alert"
    port: 0
```

### workflow-architect (EXECUTE)

Takes the Enrichment Spec and runs a four-step assembly pipeline:

1. **Validate spec** — reject unknown node types or missing triggers
2. **Build JSON** — generate UUIDs, position nodes on a 240-unit grid, wire connections
3. **Pre-save validation** — run 23 structural checks; block on any failure
4. **Write files** — `workflow.json`, `guide.md`, `nodes/*`, update catalog

---

## Toolchain

### `hooks/block-invalid-nodes`

A 23-rule JSON validator that runs before any workflow is written to disk.

```bash
# Validate a workflow
python hooks/block-invalid-nodes --file WORKSPACE_ROOT/workflows/My-Flow/workflow.json

# Strict mode (warnings treated as errors)
python hooks/block-invalid-nodes --file workflow.json --strict

# Machine-readable JSON output
python hooks/block-invalid-nodes --file workflow.json --json | jq '.passed'
```

**Exit codes:** `0` = valid, `1` = errors found (do not write), `2` = warnings only

Key rules enforced:

- `active` must be `false`
- All node IDs must be valid UUID v4 and unique
- Node types must match `n8n-nodes-base.*` or `@n8n/scope.*` format
- Webhook nodes must have a `webhookId` field
- No hardcoded secrets anywhere in the workflow JSON
- All connection source/target names must match actual node names
- `splitInBatches` nodes must have a loop-back and a done-branch

### `hooks/catalog-check`

Scans the workflow catalog for semantically similar existing workflows before building a new one. Uses Jaccard similarity on tokenized keywords.

```bash
# Check before building
python hooks/catalog-check --query "send slack when postgres row inserted"

# Custom similarity threshold
python hooks/catalog-check --query "..." --threshold 0.35

# Machine-readable output
python hooks/catalog-check --query "..." --json | jq '.matches[].name'
```

**Exit codes:** `0` = no similar workflows, `2` = matches found

### `scripts/extract_workflow.py`

Decomposes a complete `workflow.json` into individual node files for inspection, copying, and debugging.

```bash
# Full extraction
python scripts/extract_workflow.py \
  --input WORKSPACE_ROOT/workflows/My-Flow/workflow.json \
  --output-dir WORKSPACE_ROOT/workflows/My-Flow/nodes/

# List all nodes without extracting
python scripts/extract_workflow.py --input workflow.json --list-nodes

# Extract a single node to stdout
python scripts/extract_workflow.py --input workflow.json --get-node "Insert Lead to Postgres"
```

---

## Templates

Read-only scaffolding patterns in `templates/scaffolding/`. Copy and customize — never modify the originals.

| Template | Pattern | Use When |
|---|---|---|
| `webhook-workflow.json` | POST → process → respond | Building an API endpoint |
| `http-request-workflow.json` | Schedule → fetch → filter → transform | Polling an external API on a cron |
| `loop-workflow.json` | Trigger → list → batch → process → done | Processing large lists in batches |

---

## Quick Start

### Build a new workflow

```bash
# 1. Ask Claude (with skill context loaded):
"Build a workflow that [your automation in plain English]"

# 2. Claude runs the ROUTE → ENRICH → EXECUTE pipeline automatically

# 3. Validate the output
python hooks/block-invalid-nodes --file WORKSPACE_ROOT/workflows/<Name>/workflow.json

# 4. Check for duplicates
python hooks/catalog-check --query "[your description]"

# 5. Extract nodes
python scripts/extract_workflow.py \
  --input WORKSPACE_ROOT/workflows/<Name>/workflow.json \
  --output-dir WORKSPACE_ROOT/workflows/<Name>/nodes/

# 6. Import into n8n
#    n8n UI → Workflows → ⋮ → Import from File → select workflow.json

# 7. Replace REPLACE_WITH_CREDENTIAL_ID placeholders with real credential IDs
# 8. Run a manual test execution, then activate
```

### Find an existing workflow

```bash
python hooks/catalog-check --query "slack notification"
# or
grep -i "slack" WORKSPACE_ROOT/workflow-catalog.md
```

### Deploy via API

```bash
# Create workflow
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @WORKSPACE_ROOT/workflows/<Name>/workflow.json \
  https://$N8N_HOST/api/v1/workflows | jq '{id, name, active}'

# Activate
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://$N8N_HOST/api/v1/workflows/<id>/activate
```

---

## IDE Integration

### Claude Code (recommended)

`CLAUDE.md` at the repo root is automatically loaded when you open this directory in Claude Code. No additional setup needed.

### Cursor IDE

**Option A — `.cursorrules`** (all Cursor versions):

```
# .cursorrules
Before any n8n task, load and follow:
SKILL:  g:/claud-n8n-builder/skills/n8n-mcp-cli.SKILL.md
AGENTS:
  1. g:/claud-n8n-builder/agents/query-navigator.agent.md
  2. g:/claud-n8n-builder/agents/n8n-enricher.agent.md
  3. g:/claud-n8n-builder/agents/workflow-architect.agent.md
```

**Option B — MDC Rules** (Cursor ≥ 0.43): Create `.cursor/rules/*.mdc` files that reference each agent file with `alwaysApply: true`.

---

## Docker / VPS Environment

This system targets n8n self-hosted on a VPS via Docker Compose. Key points:

- **Never use `localhost`** in workflow node parameters — use Docker service names (e.g., `postgres`, `redis`)
- n8n runs on the `internal` Docker network, exposed only via a reverse proxy (Nginx/Traefik)
- Postgres runs on `internal` only — never exposed to the internet
- `N8N_ENCRYPTION_KEY` encrypts all stored credentials — back it up offline

---

## Security Rules

These are enforced by both the agents and the `block-invalid-nodes` hook:

1. Never set `"active": true` in generated JSON
2. Never embed credentials — always use `REPLACE_WITH_CREDENTIAL_ID` placeholders
3. Always run `block-invalid-nodes` before writing to `WORKSPACE_ROOT`
4. Always use node types from `n8n-nodes-base.*` only — no invented types
5. Always update `WORKSPACE_ROOT/workflow-catalog.md` after generating a workflow

---

## Requirements

- Python 3.10+
- n8n self-hosted (Docker Compose recommended)
- Claude Code CLI or Cursor IDE with Claude integration

---

## License

MIT
