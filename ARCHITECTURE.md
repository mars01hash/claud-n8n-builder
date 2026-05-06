# n8n MCP Skill Repository — Complete Architecture

> **Purpose of this document:** A single reference that explains every component
> in this repository — what it does, why it exists, how it connects to the others,
> and how to operate or extend it. Read this before touching any file.

---

## Table of Contents

1. [What This System Is](#1-what-this-system-is)
2. [Design Philosophy](#2-design-philosophy)
3. [Repository Map](#3-repository-map)
4. [The Three-Layer Architecture](#4-the-three-layer-architecture)
5. [Layer 1 — The Skill: Ground Truth](#5-layer-1--the-skill-ground-truth)
6. [Layer 2 — The Agents: Intelligence](#6-layer-2--the-agents-intelligence)
   - 6.1 [query-navigator (ROUTE)](#61-query-navigator--route-agent)
   - 6.2 [n8n-enricher (ENRICH)](#62-n8n-enricher--enrich-agent)
   - 6.3 [workflow-architect (EXECUTE)](#63-workflow-architect--execute-agent)
7. [Layer 3 — The Toolchain: Automation](#7-layer-3--the-toolchain-automation)
   - 7.1 [block-invalid-nodes Hook](#71-block-invalid-nodes-hook)
   - 7.2 [catalog-check Hook](#72-catalog-check-hook)
   - 7.3 [extract_workflow.py Script](#73-extract_workflowpy-script)
8. [Templates — Scaffolding Patterns](#8-templates--scaffolding-patterns)
9. [WORKSPACE_ROOT — The Living Output](#9-workspace_root--the-living-output)
10. [Complete Data Flow: Request to Import](#10-complete-data-flow-request-to-import)
11. [MCP Protocol Integration](#11-mcp-protocol-integration)
12. [Cursor IDE Integration](#12-cursor-ide-integration)
13. [Docker / VPS Environment Model](#13-docker--vps-environment-model)
14. [Security Architecture](#14-security-architecture)
15. [How Agents Communicate](#15-how-agents-communicate)
16. [Extending the System](#16-extending-the-system)
17. [Troubleshooting Guide](#17-troubleshooting-guide)
18. [Quick-Start Cheatsheet](#18-quick-start-cheatsheet)

---

## 1. What This System Is

This repository is a **Model Context Protocol (MCP) Skill Repository** — a
structured collection of Markdown "skills" and "agent rules" that give Claude
deep, persistent knowledge about n8n automation. It operates as the cognitive
layer between:

- **Your intent** (natural language automation requests)
- **n8n's requirements** (precise JSON schema, node parameters, Docker environment)

Without this system, Claude must guess n8n's JSON format each time. With it,
Claude follows a deterministic pipeline that always produces valid, importable
workflow files.

### What it produces for every automation request:

```
WORKSPACE_ROOT/workflows/My-Workflow-Name/
├── workflow.json          ← Drop directly into n8n (File → Import)
├── guide.md               ← Human-readable explanation of the workflow
└── nodes/
    ├── receive_webhook.json           ← Each node extracted standalone
    ├── receive_webhook.guide.md       ← Per-node documentation
    ├── insert_lead_to_postgres.json
    └── insert_lead_to_postgres.guide.md
```

### Target environment:
- **n8n:** Self-hosted on a VPS, running in Docker Compose
- **Editor:** Cursor IDE with Claude integration (via MCP or `.cursorrules`)
- **Claude:** Reads the skill/agent files as persistent context before any n8n task

---

## 2. Design Philosophy

### Principle 1: Separation of Concerns
Each component has one job. Agents do not generate JSON. Scripts do not make
decisions. Skills do not route requests. This makes the system debuggable —
if something is wrong, exactly one file is responsible.

### Principle 2: Ground Truth Over Hallucination
Every node type, typeVersion, parameter name, and connection format in this
system is sourced from the official n8n documentation and OpenAPI spec. Claude
is explicitly instructed to never invent parameters. When a node is unknown,
the Enricher fetches the live docs before proceeding.

### Principle 3: Fail Loud, Fail Early
The validation hook (block-invalid-nodes) runs before any file is written.
It checks 23 structural rules, 6 warning conditions, and 9 secret-detection
patterns. An invalid workflow is blocked before it reaches n8n.

### Principle 4: The Catalog Prevents Duplication
Before any new workflow is built, the catalog-check hook looks for semantically
similar existing workflows. This prevents building redundant automations.

### Principle 5: Security by Default
Credentials are never embedded in workflow JSON. Placeholders are used.
The Docker network isolates services. The encryption key is rotated on a
defined schedule. These are not guidelines — they are enforced by the hook.

---

## 3. Repository Map

```
g:\Proj_ClaudSkills\
│
│  CLAUDE.md                  ← Project root: auto-loaded by Claude Code as context
│  ARCHITECTURE.md            ← This document
│
├── skills/
│   └── n8n-mcp-cli.SKILL.md  ← The ground truth: API, schema, node catalog, security
│
├── agents/
│   ├── query-navigator.agent.md    ← ROUTE: intent classification and dispatch
│   ├── n8n-enricher.agent.md       ← ENRICH: doc retrieval and spec building
│   └── workflow-architect.agent.md ← EXECUTE: JSON generation pipeline
│
├── hooks/
│   ├── block-invalid-nodes   ← Python: pre-save JSON validator (23 rules)
│   └── catalog-check         ← Python: semantic duplicate detector
│
├── scripts/
│   └── extract_workflow.py   ← Python: decompose workflow.json into node files
│
├── templates/
│   └── scaffolding/
│       ├── webhook-workflow.json       ← Pattern: POST → process → respond
│       ├── http-request-workflow.json  ← Pattern: schedule → fetch → filter
│       └── loop-workflow.json          ← Pattern: batch → loop → done
│
└── WORKSPACE_ROOT/
    ├── workflow-catalog.md             ← Level 1: master keyword index
    └── workflows/
        └── {Workflow-Name}/
            ├── workflow.json           ← Level 2: importable n8n JSON
            ├── guide.md               ← Level 2: human documentation
            └── nodes/
                ├── {slug}.json        ← Level 3: individual node objects
                └── {slug}.guide.md    ← Level 3: per-node documentation
```

### File Ownership Matrix

| File | Written By | Read By | Modified By |
|---|---|---|---|
| `n8n-mcp-cli.SKILL.md` | Human (you) | All agents | Human only |
| `query-navigator.agent.md` | Human (you) | Claude | Human only |
| `n8n-enricher.agent.md` | Human (you) | Claude | Human only |
| `workflow-architect.agent.md` | Human (you) | Claude | Human only |
| `block-invalid-nodes` | Human (you) | CI / pre-save | Human only |
| `catalog-check` | Human (you) | Navigator, CI | Human only |
| `extract_workflow.py` | Human (you) | Post-generation step | Human only |
| `templates/scaffolding/*.json` | Human (you) | Architect (reference) | **Never** |
| `workflow-catalog.md` | workflow-architect | query-navigator, catalog-check | workflow-architect |
| `workflows/*/workflow.json` | workflow-architect | n8n import, extract_workflow.py | Human (post-import) |
| `workflows/*/guide.md` | workflow-architect | Human | workflow-architect |
| `workflows/*/nodes/*.json` | extract_workflow.py | Human | extract_workflow.py |
| `workflows/*/nodes/*.guide.md` | extract_workflow.py | Human | extract_workflow.py |

---

## 4. The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DYNAMIC SKILL LIBRARY                                         │
│  skills/core-system.SKILL.md  +  skills/*.SKILL.md                      │
│  The authoritative ground truth. API spec, JSON schema, and specialized  │
│  node knowledge.                                                        │
│  ↑ Agents read AND WRITE to this layer.                                 │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ consulted / created by
┌───────────────────────────────▼─────────────────────────────────────────┐
│  LAYER 2: AGENTS                                                        │
│                                                                         │
│  ┌──────────────┐ routes ┌──────────────┐ spec  ┌────────────┐          │
│  │ navigator    │───────▶│ enricher     │──────▶│ architect  │          │
│  │ (ROUTE)       │       │ (ENRICH)     │       │ (EXECUTE)  │          │
│  └──────────────┘       └──────────────┘       └────────────┘          │
│  Intent class.           Skill Lookup           JSON generation         │
│  Catalog lookup          Skill Creation         Assembly pipeline       │
│  Skill lookup            Doc retrieval          File output             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ uses
┌───────────────────────────────▼─────────────────────────────────────────┐
│  LAYER 3: TOOLCHAIN                                                     │
│                                                                         │
│  block-invalid-nodes    catalog-check    extract_workflow.py            │
│  (23-rule validator)    (dup detector)   (node decomposer)              │
│                                                                         │
│  Templates: webhook | http-request | loop | node-template (SKILL)       │
│                                                                         │
│  OUTPUT → WORKSPACE_ROOT/workflows/{Name}/                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Responsibility Separation

| Layer | Knows About | Does NOT Know About |
|---|---|---|
| Skill | API endpoints, JSON schema, node params, security rules | User intent, routing, file I/O |
| Agents | User intent, spec format, pipeline steps | File paths, Python execution, git |
| Toolchain | File paths, JSON parsing, regex patterns | User intent, n8n semantics |

---

## 5. Layer 1 — The Dynamic Skill Library

**Core Skill:** [skills/core-system.SKILL.md](skills/core-system.SKILL.md)
**Node Skills:** `skills/*.SKILL.md`

### Why "Dynamic"?

In this architecture, "Skills" are not static documentation. They are **active knowledge units** that the system manages.
1. **Core System Skill**: Fixed reference for API, schema, and security.
2. **Specialized Skills**: Modular files for specific integrations. If an agent needs a node it hasn't seen, it fetches the docs and **creates a new Skill file**.

### What a Skill contains (Node-Specific)

| Section | Content | Purpose |
|---|---|---|
| Metadata | Type, Latest Version, Credential Type | Absolute identification |
| Mapping | NL → n8n parameters | Translation intelligence |
| Patterns | Optimized expressions | Ready-to-use JS logic |
| Tips | Agentic Best Practices | Performance and reliability |
| Errors | Common fixes | Proactive troubleshooting |
| Security | Node-specific hardening | Production safety |

### Why it is a "Skill" and not just "Docs"

### Pre-loaded Specialized Skills

The system comes pre-loaded with high-value skills for common integrations:
- `skills/postgres.SKILL.md`: Docker-optimized networking and SQL mapping.
- `skills/slack.SKILL.md`: Block Kit patterns and channel management.
- `skills/http-request.SKILL.md`: Complete auth and pagination logic.
- `skills/google-sheets.SKILL.md`: Sheet mapping and scope verification.
- `skills/airtable.SKILL.md`: Base/Table mapping and Token auth.

---

## 6. Layer 2 — The Agents: Intelligence

The three agents implement the **ROUTE → ENRICH → EXECUTE** lifecycle.
They are Markdown files that Claude reads as behavioral instructions.

### Agent Communication Protocol

Agents do not call each other like functions. Claude reads all three agent
files as context and simulates their interaction by switching "roles" as
the request progresses through the pipeline. The output of one agent's phase
is the structured input to the next phase's instructions.

```
Phase 1 output: NAVIGATOR MEMO (routing decision)
        ↓
Phase 2 output: ENRICHMENT SPEC YAML (node/connection specification)
        ↓
Phase 3 output: workflow.json + guide.md + nodes/* (files on disk)
```

---

### 6.1 query-navigator — ROUTE Agent

**File:** [agents/query-navigator.agent.md](agents/query-navigator.agent.md)

```
Receives:  Raw user message (natural language)
Produces:  A NAVIGATOR MEMO with intent + routing decision
Does NOT:  Look up node types, generate JSON, write files
```

#### Decision tree

```
User message arrives
        │
        ▼
  ┌─────────────────────────────────┐
  │ Classify into one of 6 intents  │
  └─────────────────────────────────┘
        │
        ├── BUILD_NEW ──────────────────────────────────────────────────────┐
        │   "create", "build", "automate"                                   │
        │   Step 1: Check workflow-catalog.md for similar workflow           │
        │   Step 2: If match → ask user "extend or new?"                   │
        │   Step 3: Route to n8n-enricher                                   │
        │                                                                   │
        ├── LOOKUP_EXISTING ──────────────────────────────────────────────┐ │
        │   "show me", "find", "do we have"                               │ │
        │   → Read workflow-catalog.md → return top 3 matches             │ │
        │                                                                 │ │
        ├── MODIFY_WORKFLOW ──────────────────────────────────────────────┤ │
        │   "update", "add a step", "fix node"                            │ │
        │   → Identify workflow path → delegate to extract_workflow.py    │ │
        │                                                                 │ │
        ├── EXPLAIN_CONCEPT ──────────────────────────────────────────────┤ │
        │   "how does", "what is", "explain"                              │ │
        │   → Answer inline (no delegation needed)                        │ │
        │                                                                 │ │
        ├── DEBUG_WORKFLOW ───────────────────────────────────────────────┤ │
        │   "failing", "error", "not working"                             │ │
        │   → Route to n8n-enricher in diagnostic mode                   │ │
        │                                                                 │ │
        └── IMPORT_EXPORT ────────────────────────────────────────────────┘ │
            "export JSON", "import this"                                     │
            → Route to extract_workflow.py                                   │
                                                                             │
                                                              BUILD_NEW path ▼
                                                         n8n-enricher → workflow-architect
```

#### Why catalog-first matters

Every `BUILD_NEW` request checks the catalog before starting enrichment.
This prevents building a "Notify Slack on Postgres Insert" workflow when
one already exists as "Lead Alert Workflow." Duplication wastes storage
and creates competing sources of truth for the same automation.

#### Navigator Memo format

Every request produces this internal memo before any action:

```
NAVIGATOR MEMO
──────────────
Input       : "build a workflow that sends a Slack alert when a new row is
               inserted into the orders table"
Intent      : BUILD_NEW
Confidence  : 92%
Target      : Order Insert Slack Alert
Catalog Hit : NO
Next Agent  : n8n-enricher
──────────────
```

---

### 6.2 n8n-enricher — ENRICH Agent

**File:** [agents/n8n-enricher.agent.md](agents/n8n-enricher.agent.md)

```
Receives:  Routing decision from query-navigator
Produces:  A structured ENRICHMENT SPEC YAML
Does NOT:  Generate workflow JSON, write files
```

#### Core capability: Live MCP retrieval

The Enricher knows the core node catalog from the Skill file. For any node
**not** in the core catalog, it uses MCP tools to fetch live documentation:

```
MCP tools/call → fetch → https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.{name}/
                                        ↓
                               Extract: typeVersion, parameters, credential type
                                        ↓
                               Include in enrichment spec
```

This means the system always has current node parameters, even for nodes
added after the Skill file was last updated.

#### The 5-step retrieval pipeline

```
Step 1: SEARCH
  MCP search tool → "n8n {service} node site:docs.n8n.io"
  → Confirms canonical node type name and URL

Step 2: FETCH
  MCP fetch tool → docs.n8n.io URL
  → Extracts: typeVersion, all parameters, credential type

Step 3: FETCH (credential page)
  MCP fetch tool → docs.n8n.io/integrations/builtin/credentials/{service}/
  → Extracts: credential type name (the exact JSON key)

Step 4: VALIDATE
  Cross-references against n8n-mcp-cli.SKILL.md
  → Confirms typeVersion exists, connection type is correct

Step 5: OUTPUT
  Emits enrichment spec YAML
```

#### The Enrichment Spec — the bridge between Phase 2 and Phase 3

This YAML is the precise hand-off from Enricher to Architect:

```yaml
workflow_name: "Order Insert Slack Alert"
workflow_description: "Sends a Slack message whenever a new row is inserted in the orders table"
retrieval_status: OK

trigger:
  node_type: "n8n-nodes-base.postgresTrigger"
  type_version: 1
  params:
    tableName: orders
    triggerOn: insert

steps:
  - step: 1
    intent: "Format alert message"
    node_type: "n8n-nodes-base.set"
    type_version: 3.4
    credential: null
    params:
      mode: manual
      fields:
        - name: message
          value: "={{ 'New order #' + $json[\"id\"] + ' — $' + $json[\"total\"] }}"

  - step: 2
    intent: "Send Slack notification"
    node_type: "n8n-nodes-base.slack"
    type_version: 2.2
    credential:
      type: "slackOAuth2Api"
      placeholder_name: "Slack Bot"
    params:
      resource: message
      operation: post
      channel: "#orders"
      text: "={{ $json[\"message\"] }}"

connections:
  - from: "Postgres Trigger"
    to: "Format Alert Message"
    port: 0
  - from: "Format Alert Message"
    to: "Send Slack Alert"
    port: 0
```

#### Diagnostic Mode

When the query-navigator routes a `DEBUG_WORKFLOW` intent, the Enricher
switches to diagnostic mode. It classifies the error message, identifies
the root cause node, and produces a fix specification:

```yaml
diagnostic:
  reported_error: "ECONNREFUSED 127.0.0.1:5432"
  classified_as: "Docker network misconfiguration"
  suspected_node: "Insert Lead to Postgres"
  root_cause: "Postgres host is 'localhost' — in Docker, use the service name"
  fix:
    node: "Insert Lead to Postgres"
    parameter: "host"
    from: "localhost"
    to: "postgres"
```

---

### 6.3 workflow-architect — EXECUTE Agent

**File:** [agents/workflow-architect.agent.md](agents/workflow-architect.agent.md)

```
Receives:  Enrichment spec YAML from n8n-enricher
Produces:  workflow.json, guide.md, nodes/*.json, nodes/*.guide.md
Does NOT:  Fetch documentation, classify intent, route requests
```

#### The Assembly Pipeline — 4 mandatory steps

```
┌──────────────────────────────────────────────────────────┐
│  STEP A: Receive & Validate Spec                         │
│  • Parse enrichment spec                                 │
│  • Gate check: reject if UNKNOWN node types or no trigger│
│  • Assign final node names (Verb + Object + Service)     │
│  • Build the Node Roster (ordered name list)             │
└──────────────────────────────┬───────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────┐
│  STEP B: Build Nodes Array + Map Connections             │
│                                                          │
│  B.1: Generate UUID v4 for every node id + webhookId    │
│  B.2: Position nodes on 240-unit grid                   │
│  B.3: Assemble each NodeObject (all 15 fields)          │
│  B.4: Wire connections using the Connection Algorithm   │
│  B.5: Translate YAML params → exact n8n JSON format     │
└──────────────────────────────┬───────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────┐
│  STEP C: Pre-Save Schema Validation                      │
│  • Run all 12 checks from SKILL.md Part 8                │
│  • Run 12 structural integrity checks (pseudocode)       │
│  • API-level pre-validation                              │
│  • Emit validation report (pass / fail)                  │
│  • Block file write on any FAIL                          │
└──────────────────────────────┬───────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────┐
│  STEP D: Write Output Files                              │
│  • workflow.json (import-ready)                          │
│  • guide.md (human documentation)                        │
│  • nodes/{slug}.json (per-node extraction)               │
│  • nodes/{slug}.guide.md (per-node guide)                │
│  • Update WORKSPACE_ROOT/workflow-catalog.md             │
└──────────────────────────────────────────────────────────┘
```

#### Node Positioning Algorithm

Nodes are placed on a grid. This ensures the imported workflow renders
cleanly in the n8n canvas without node overlap:

```
Linear flow:
  Trigger [240, 300] → Step1 [480, 300] → Step2 [720, 300] → Step3 [960, 300]

Branch flow (IF node at Step2):
  Trigger [240, 300] → Step1 [480, 300] → IF [720, 300]
                                               ↓ port 0 (true)
                                         True-Handler [960, 120]
                                               ↓ port 1 (false)
                                         False-Handler [960, 480]

Loop flow (splitInBatches):
  Source [480, 300] → BatchNode [720, 300] ← ← ← ← ← ← ← ← ─┐
                            ↓ port 0 (body)                      │
                      Process [960, 220] ──────────────────────── ┘  (loop-back)
                            ↓ port 1 (done)
                      PostLoop [960, 400]
```

#### Connection Wiring Algorithm

```python
# Pseudocode for the connection wiring step

connections = {}

for C in enrichment_spec.connections:
    source = C.from    # exact node name from roster
    target = C.to      # exact node name from roster
    port   = 0 if C.port in (0, "main") else 1

    if source not in connections:
        connections[source] = {"main": []}

    # Extend the main array to the needed port index
    while len(connections[source]["main"]) <= port:
        connections[source]["main"].append([])

    connections[source]["main"][port].append({
        "node": target,
        "type": "main",
        "index": 0
    })
```

#### The 4 output files explained

```
workflow.json
│  The complete n8n workflow ready for File → Import.
│  active: false always. Credential IDs are placeholders.
│  This is the primary deliverable.

guide.md
│  Human-readable documentation:
│  • Purpose statement
│  • Trigger description
│  • Step-by-step node explanation
│  • Credentials table
│  • Docker environment variables
│  • Post-import checklist

nodes/{slug}.json
│  Each node extracted as a standalone object.
│  Used for: inspecting a single node, copying to another workflow,
│  referencing when debugging a specific step.

nodes/{slug}.guide.md
│  Per-node documentation:
│  • Parameters table
│  • Input / output $json shape
│  • All {{ expressions }} and what they resolve to
│  • Incoming / outgoing connections
```

---

## 7. Layer 3 — The Toolchain: Automation

### 7.1 block-invalid-nodes Hook

**File:** [hooks/block-invalid-nodes](hooks/block-invalid-nodes)
**Language:** Python 3.10+
**Trigger:** Before any workflow.json is written to WORKSPACE_ROOT

This is a 684-line validator with 23 hard rules, 6 warnings, and 9 secret-
detection patterns. It is the final quality gate before a workflow touches
the file system.

#### Rule reference

| Rule | Category | Description |
|---|---|---|
| R01 | Structure | `name` field must be present and non-empty |
| R02 | Structure | `nodes` must be a JSON array |
| R03 | Structure | `nodes` must not be empty |
| R04 | Structure | `connections` must be a JSON object |
| R05 | Safety | `active` must be `false` |
| R06 | Node | Every node `id` must be a valid UUID v4 |
| R07 | Node | All node `id` values must be unique |
| R08 | Node | Every node `name` must be present and unique |
| R09 | Node | `type` must match `n8n-nodes-base.X` or `@n8n/scope.X` format |
| R10 | Node | `typeVersion` must be in the supported versions list |
| R11 | Node | Deprecated node types flagged (function, functionItem) |
| R12 | Node | `position` must be `[x, y]` array of numbers |
| R13 | Node | Webhook nodes must have a `webhookId` field |
| R15 | Connection | Source node names must exist in `nodes` |
| R16 | Connection | Connection value must be an object with `main` array |
| R17 | Connection | Each port must be an array of edge objects |
| R18 | Connection | Target `node` names must exist in `nodes` |
| R19 | Connection | Edge `type` must be `"main"` or a valid `"ai_*"` type |
| R20 | Connection | Trigger nodes must never be connection targets |
| R21 | Connection | Non-trigger nodes must have at least one incoming connection |
| R22 | Security | No hardcoded secrets anywhere in the workflow JSON |
| R23 | Logic | splitInBatches nodes must have loop-back + done-branch |
| — | Info | All `REPLACE_WITH_CREDENTIAL_ID` placeholders listed for user |

#### Exit codes

```
0 = Valid — safe to write workflow.json
1 = Invalid — hard errors found — do not write
2 = Warnings only — write but review before importing
```

#### Usage

```bash
# Basic validation
python hooks/block-invalid-nodes --file WORKSPACE_ROOT/workflows/My-Flow/workflow.json

# Strict mode (warnings = errors)
python hooks/block-invalid-nodes --file workflow.json --strict

# CI/CD machine-readable output
python hooks/block-invalid-nodes --file workflow.json --json | jq '.passed'

# Pipe from generator
cat workflow.json | python hooks/block-invalid-nodes
```

---

### 7.2 catalog-check Hook

**File:** [hooks/catalog-check](hooks/catalog-check)
**Language:** Python 3.10+
**Trigger:** Before `BUILD_NEW` intent is dispatched to the enricher

Scans `WORKSPACE_ROOT/workflow-catalog.md` for workflows that are semantically
similar to the user's request. Uses Jaccard similarity on tokenized keywords.

#### How similarity scoring works

```python
# Tokenize both the user query and each catalog entry
query_tokens  = {"slack", "alert", "postgres", "order", "insert"}
entry_tokens  = {"slack", "notification", "postgres", "new", "row"}

intersection  = {"slack", "postgres"}  → 2 tokens in common
union         = {"slack", "alert", "postgres", "order", "insert",
                 "notification", "new", "row"}  → 8 tokens total

similarity    = 2 / 8 = 0.25  → 25% — above the 0.20 default threshold → MATCH
```

#### Exit codes

```
0 = No similar workflows found — proceed with build
2 = Matches found — user should review before building
```

#### Usage

```bash
# Basic check before building
python hooks/catalog-check --query "send slack when postgres row inserted"

# Custom threshold (0.0 = show everything, 1.0 = exact match only)
python hooks/catalog-check --query "..." --threshold 0.35

# Machine-readable (for scripting)
python hooks/catalog-check --query "..." --json | jq '.matches[].name'

# Point at a non-default catalog
python hooks/catalog-check --query "..." --catalog /path/to/workflow-catalog.md
```

---

### 7.3 extract_workflow.py Script

**File:** [scripts/extract_workflow.py](scripts/extract_workflow.py)
**Language:** Python 3.10+
**Trigger:** After workflow-architect writes workflow.json

Decomposes a complete workflow.json into:
- One `.json` file per node (the raw node object)
- One `.guide.md` file per node (auto-documented)
- A workflow-level summary

This enables three use cases:
1. **Inspect** a single node without opening the full workflow JSON
2. **Copy** a node configuration into another workflow
3. **Debug** by reading the per-node $json shape documentation

#### Usage

```bash
# Full extraction to nodes/ directory
python scripts/extract_workflow.py \
  --input WORKSPACE_ROOT/workflows/My-Flow/workflow.json \
  --output-dir WORKSPACE_ROOT/workflows/My-Flow/nodes/ \
  --summary-file WORKSPACE_ROOT/workflows/My-Flow/guide.md

# List all nodes (no extraction)
python scripts/extract_workflow.py \
  --input workflow.json \
  --list-nodes

# Extract a single node to stdout
python scripts/extract_workflow.py \
  --input workflow.json \
  --get-node "Insert Lead to Postgres"
```

---

## 8. Templates — Scaffolding Patterns

**Directory:** [templates/scaffolding/](templates/scaffolding/)
**Access:** Read-only. Never modify. Copy and customize.

Templates are valid n8n JSON structures that demonstrate correct patterns.
They use `REPLACE_*` placeholders for all variable values.

### Available templates

| File | Pattern | Nodes | Use When |
|---|---|---|---|
| `webhook-workflow.json` | POST → process → respond | Webhook, Set, Code, RespondToWebhook | Building an API endpoint |
| `http-request-workflow.json` | Schedule → fetch → filter → transform | ScheduleTrigger, HTTPRequest, IF, Set, NoOp | Polling an external API |
| `loop-workflow.json` | Trigger → list → batch → process → done | ManualTrigger, HTTPRequest, SplitInBatches, Code, Set | Processing lists in batches |

### Template anatomy

```json
{
  "_template": "webhook-workflow",
  "_description": "Receives a POST request...",
  "name": "PLACEHOLDER: Workflow Name",
  "nodes": [
    {
      "id": "REPLACE_WITH_UUID_V4",     ← always replace
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [240, 300],           ← pre-positioned on grid
      "webhookId": "REPLACE_WITH_UUID_V4",
      "parameters": {
        "path": "REPLACE_WITH_PATH"     ← replace placeholders
      }
    }
  ]
}
```

---

## 9. WORKSPACE_ROOT — The Living Output

**Directory:** [WORKSPACE_ROOT/](WORKSPACE_ROOT/)

This is the production artifact store. Every workflow built by the system
lands here. It is the only directory that grows over time.

### Catalog structure

**File:** [WORKSPACE_ROOT/workflow-catalog.md](WORKSPACE_ROOT/workflow-catalog.md)

```markdown
| Name | Trigger | Integrations | Keywords | Guide |
|---|---|---|---|---|
| Lead Ingestion Pipeline | webhook/POST | Postgres, Slack | lead, ingest, crm | [guide](workflows/Lead-Ingestion-Pipeline/guide.md) |
| Daily Report Generator  | cron/0 9 * * 1-5 | GoogleSheets, emailSend | report, daily, email | [guide](workflows/Daily-Report-Generator/guide.md) |
```

The catalog is the system's memory of what has been built. The query-navigator
reads it at the start of every `BUILD_NEW` request.

### Three-level documentation hierarchy

```
Level 1: workflow-catalog.md
  → keyword search → which workflow?

Level 2: workflows/{Name}/guide.md
  → full workflow documentation → which node does what?

Level 3: workflows/{Name}/nodes/{slug}.guide.md
  → per-node detail → what does this specific node do?
```

---

## 10. Complete Data Flow: Request to Import

This is the full trace of a `BUILD_NEW` request through the entire system.

```
┌──────────────────────────────────────────────────────────────────────┐
│  USER:  "Build a workflow that receives a webhook POST, saves the     │
│          payload to Postgres, and sends a Slack alert"                │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 1: query-navigator (ROUTE)                                      │
│                                                                       │
│  • Classify intent → BUILD_NEW (95% confidence)                       │
│  • Query workflow-catalog.md → keyword match: "webhook", "postgres",  │
│    "slack" → No catalog hit                                           │
│  • Emit NAVIGATOR MEMO                                                │
│  • Route to n8n-enricher                                              │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 2: n8n-enricher (ENRICH)                                        │
│                                                                       │
│  • Skill Lookup → Check `skills/` for specialized knowledge           │
│  • If Skill found → Use mapping logic and tips from Skill file        │
│  • If Skill NOT found:                                                │
│    1. Live MCP retrieval (fetch docs.n8n.io)                          │
│    2. **CREATE NEW SKILL FILE** (e.g., `airtable.SKILL.md`)           │
│  • Map trigger and steps using Skill/Doc metadata                     │
│  • Emit ENRICHMENT SPEC YAML                                          │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 3: workflow-architect (EXECUTE)                                  │
│                                                                       │
│  Step A: Validate spec, assign names:                                 │
│    0: "Receive Webhook"                                               │
│    1: "Insert Payload to Postgres"                                    │
│    2: "Notify Team on Slack"                                          │
│                                                                       │
│  Step B: Build JSON                                                   │
│    • Generate 3 UUIDs (node ids) + 1 UUID (webhookId) + 1 (versionId)│
│    • Position: [240,300] [480,300] [720,300]                         │
│    • Assemble NodeObjects with all parameters                         │
│    • Wire connections map                                             │
│                                                                       │
│  Step C: Validate                                                     │
│    • Run 23 rules → all pass                                          │
│    • Flag 2 credential placeholders → INFO level                      │
│    • Emit validation report: PASS                                     │
│                                                                       │
│  Step D: Write files                                                  │
│    • workflow.json ✓                                                  │
│    • guide.md ✓                                                       │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 4: block-invalid-nodes (VALIDATE)                               │
│                                                                       │
│  python hooks/block-invalid-nodes --file workflow.json                │
│  → 23 rules checked → 0 errors → 0 warnings → exit 0                 │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 5: extract_workflow.py (DECOMPOSE)                              │
│                                                                       │
│  python scripts/extract_workflow.py \                                 │
│    --input workflow.json \                                            │
│    --output-dir WORKSPACE_ROOT/workflows/Webhook-Postgres-Slack/nodes/│
│                                                                       │
│  Writes:                                                              │
│    nodes/receive_webhook.json + nodes/receive_webhook.guide.md       │
│    nodes/insert_payload_to_postgres.json + *.guide.md                 │
│    nodes/notify_team_on_slack.json + *.guide.md                       │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 6: catalog-check + catalog update                               │
│                                                                       │
│  python hooks/catalog-check --query "webhook postgres slack"          │
│  → No hit (this is the first run) → proceed                           │
│                                                                       │
│  Append to workflow-catalog.md:                                       │
│  | Webhook Postgres Slack Alert | webhook/POST | Postgres, Slack |    │
│  | webhook, postgres, slack, alert | [guide](...) |                  │
└──────────────────────────────────┬───────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│  STEP 7: USER IMPORTS INTO n8n                                        │
│                                                                       │
│  n8n UI → Workflows → Import from File                                │
│         → Select: WORKSPACE_ROOT/workflows/.../workflow.json          │
│         → Replace credential IDs in both nodes                        │
│         → Run manual test execution                                   │
│         → Activate                                                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 11. MCP Protocol Integration

The Model Context Protocol (MCP) is an open standard (2025-06-18 spec) that
lets Claude interact with external systems through a defined tool interface.

### How the Enricher uses MCP tools

The MCP `tools/call` protocol is used by the n8n-enricher for live doc retrieval:

```json
// 1. Discover available tools
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}

// 2. Response includes fetch and search
{
  "result": {
    "tools": [
      {
        "name": "fetch",
        "description": "Fetch a URL and return its content",
        "inputSchema": {
          "type": "object",
          "properties": {
            "url": { "type": "string" },
            "max_length": { "type": "integer" }
          },
          "required": ["url"]
        }
      },
      {
        "name": "search",
        "description": "Search the web",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": { "type": "string" },
            "allowed_domains": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    ]
  }
}

// 3. Enricher invokes fetch for an unknown node
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "fetch",
    "arguments": {
      "url": "https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.notion/",
      "max_length": 8000
    }
  }
}

// 4. Response contains node documentation
{
  "result": {
    "content": [{ "type": "text", "text": "# Notion Node\n## Parameters\n..." }],
    "isError": false
  }
}
```

### MCP server configuration for n8n API access

Add this to your MCP server configuration (`.cursor/mcp.json` or `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "n8n-api": {
      "command": "npx",
      "args": ["-y", "mcp-server-fetch"],
      "env": {}
    },
    "n8n-docs": {
      "command": "npx",
      "args": ["-y", "mcp-server-fetch"],
      "description": "Used by n8n-enricher for live doc retrieval"
    }
  }
}
```

For direct n8n API interaction (create/activate workflows programmatically):

```json
{
  "mcpServers": {
    "n8n-rest": {
      "command": "npx",
      "args": ["-y", "@your-org/n8n-mcp-server"],
      "env": {
        "N8N_API_URL": "https://your-vps-domain.com/api/v1",
        "N8N_API_KEY": "${N8N_API_KEY}"
      }
    }
  }
}
```

---

## 12. Cursor IDE Integration

Cursor reads agent/skill context through three mechanisms, in order of
recommendation:

### Option A: `.cursorrules` (Simplest — supported in all Cursor versions)

Create this file in your project root:

```
# .cursorrules (in your n8n project directory)

You are working in an n8n automation project.
Before any n8n task, load and follow these files as behavioral rules:

SKILL (ground truth — always active):
  g:/Proj_ClaudSkills/skills/n8n-mcp-cli.SKILL.md

AGENTS (role-play these in sequence for every automation request):
  1. g:/Proj_ClaudSkills/agents/query-navigator.agent.md  → ROUTE phase
  2. g:/Proj_ClaudSkills/agents/n8n-enricher.agent.md    → ENRICH phase
  3. g:/Proj_ClaudSkills/agents/workflow-architect.agent.md → EXECUTE phase

PIPELINE RULES:
  1. Always output a NAVIGATOR MEMO before any work
  2. Always produce an ENRICHMENT SPEC before generating JSON
  3. Always run block-invalid-nodes before writing workflow.json
  4. Never set active: true in generated JSON
  5. Never embed credentials — use REPLACE_WITH_CREDENTIAL_ID
  6. Always update workflow-catalog.md after generating a workflow

OUTPUT DIRECTORY: g:/Proj_ClaudSkills/WORKSPACE_ROOT/workflows/
```

### Option B: Cursor MDC Rules (Recommended for Cursor ≥ 0.43)

Create individual `.mdc` files in `.cursor/rules/`:

```
.cursor/rules/
├── 00-n8n-skill.mdc          ← alwaysApply: true, references SKILL.md
├── 01-query-navigator.mdc    ← alwaysApply: true, references agent file
├── 02-n8n-enricher.mdc       ← alwaysApply: true, references agent file
└── 03-workflow-architect.mdc ← alwaysApply: true, references agent file
```

Each `.mdc` file:

```markdown
---
description: n8n workflow architect — JSON generation pipeline
alwaysApply: true
globs: ["**/*.json", "**/*.md"]
---

@file g:/Proj_ClaudSkills/agents/workflow-architect.agent.md
```

### Option C: CLAUDE.md (for Claude Code CLI users)

The `CLAUDE.md` at the repository root is already configured and is
automatically loaded by Claude Code when the working directory is
`g:\Proj_ClaudSkills`. No additional configuration needed.

---

## 13. Docker / VPS Environment Model

```
VPS (Ubuntu/Debian)
│
├── /opt/n8n/
│   ├── docker-compose.yml      ← service definitions
│   ├── .env                    ← secrets (chmod 600, not in git)
│   └── files/                  ← mounted into container
│
└── Docker containers:
    │
    ├── n8n (port 5678, internal only)
    │   ├── Image: n8nio/n8n:latest
    │   ├── Network: [internal, web]
    │   ├── Volumes: n8n_data:/home/node/.n8n
    │   └── Env:
    │       N8N_ENCRYPTION_KEY=<32-char random>
    │       WEBHOOK_URL=https://yourdomain.com/
    │       N8N_WEBHOOK_URL=https://yourdomain.com/
    │       GENERIC_TIMEZONE=UTC
    │       DB_TYPE=postgresdb
    │       DB_POSTGRESDB_HOST=postgres     ← service name, not localhost
    │
    ├── postgres (internal network only)
    │   ├── Image: postgres:15-alpine
    │   └── Network: [internal]             ← NOT exposed to web
    │
    └── reverse-proxy (Nginx/Traefik)
        ├── Handles TLS termination
        ├── Forwards HTTPS:443 → n8n:5678
        └── Network: [web]
```

### Why `localhost` is always wrong in Docker workflows

```
Your local machine → localhost → your machine
n8n container     → localhost → the n8n container itself
n8n container     → "postgres" → the postgres container ✓
```

The Skill file, Enricher, and Architect all enforce this rule. The validation
hook (R22) does not currently catch localhost in URLs, but the SKILL.md
Docker rules section explicitly prohibits it.

---

## 14. Security Architecture

### Credential flow (what never touches workflow JSON)

```
Real credential value
        │
        ▼
n8n UI → Settings → Credentials → [type form]
        │
        ▼
Stored encrypted in n8n database (AES-256, key = N8N_ENCRYPTION_KEY)
        │
        ▼
n8n assigns credential ID (e.g., "47")
        │
        ▼
workflow.json references: { "id": "47", "name": "Postgres VPS" }
        │
        ▼
At runtime, n8n decrypts and injects the value — never exposed in JSON
```

### The five security layers

```
Layer 1: N8N_ENCRYPTION_KEY
  Encrypts all stored credentials in the database.
  If this key is lost, all credentials are unrecoverable.
  Backup: encrypted, offline, separate from the key itself.

Layer 2: Docker network isolation
  Postgres and Redis run on internal-only networks.
  n8n is also on the internal network, exposed only via reverse proxy.
  Nothing in the database is directly reachable from the internet.

Layer 3: TLS at the reverse proxy
  All traffic to n8n goes through HTTPS.
  n8n itself runs HTTP internally (the proxy handles TLS).
  Webhook URLs generate correctly because N8N_WEBHOOK_URL is set.

Layer 4: block-invalid-nodes secret detection
  Nine regex patterns scan every generated workflow.json for
  credential values that should not be there.
  Fails with exit code 1 if any pattern matches.

Layer 5: Credential placeholder discipline
  All generated workflow JSON uses REPLACE_WITH_CREDENTIAL_ID.
  This is enforced in the Architect's Step D and validated by the hook.
  Real credential IDs are only substituted by the human post-import.
```

---

## 15. How Agents Communicate

Agents do not call each other programmatically. Claude simulates the agent
pipeline by loading all three agent files as context and switching behavioral
modes as the request progresses.

### The structured handoff pattern

```
Phase 1 → Phase 2 handoff:

  query-navigator emits:
  ┌────────────────────────────────────────┐
  │ NAVIGATOR MEMO                         │
  │ Intent: BUILD_NEW                      │
  │ Next Agent: n8n-enricher               │
  │ Target: "Webhook Postgres Slack Alert" │
  └────────────────────────────────────────┘

  n8n-enricher receives the memo and begins enrichment.

Phase 2 → Phase 3 handoff:

  n8n-enricher emits:
  ┌────────────────────────────────────────┐
  │ ENRICHMENT SPEC YAML                   │
  │ workflow_name: "..."                   │
  │ trigger: { ... }                       │
  │ steps: [ ... ]                         │
  │ connections: [ ... ]                   │
  └────────────────────────────────────────┘

  workflow-architect receives the spec and begins Step A.
```

### Why YAML for the enrichment spec

YAML is human-readable and easier to review in a chat interface than JSON.
The Architect translates it to JSON. If the spec has errors, they are easier
to spot and fix in YAML before JSON generation begins.

---

## 16. Extending the System

### Adding a new core node to the Skill

When a new n8n node becomes available that you use frequently:

1. Add its typeVersion to `n8n-mcp-cli.SKILL.md` Part 6 table
2. Add its parameter template to Part 7
3. Add it to the Resource Mapping table in Part 3
4. Add it to `SUPPORTED_VERSIONS` in `hooks/block-invalid-nodes`

### Adding a new agent

Create a new agent file in `agents/`:

```markdown
---
name: my-new-agent
role: Description
lifecycle_stage: MY_STAGE
version: 1.0.0
---
# Agent: my-new-agent
...
```

Then update `CLAUDE.md` and `.cursorrules` to reference it.

### Adding a new template

Create a new JSON file in `templates/scaffolding/`:

1. Copy the closest existing template
2. Replace all values with `PLACEHOLDER_` or `REPLACE_` prefixes
3. Test it through `block-invalid-nodes` (it should pass with warnings about placeholders)
4. Add the template to the Templates section in `CLAUDE.md`

### Adding validation rules to block-invalid-nodes

Add a new check function and call it from `validate()`:

```python
def check_my_rule(nodes: list, result: ValidationResult) -> None:
    for node in nodes:
        if <condition>:
            result.errors.append(ValidationIssue(
                "ERROR", "R24", node.get("name", ""),
                "Description of the problem",
                "How to fix it"
            ))

# In validate():
check_my_rule(nodes, result)
```

### Adding a new catalog entry manually

Edit `WORKSPACE_ROOT/workflow-catalog.md`:

```markdown
| My New Workflow | webhook/POST | Postgres, Slack | keyword1, keyword2 | [guide](workflows/My-New-Workflow/guide.md) |
```

---

## 17. Troubleshooting Guide

### "Workflow imports but nodes show no connections"

**Cause:** Connection source/target names don't match the node `name` fields exactly.
n8n uses the `name` field as the connection key.

**Fix:** Run `block-invalid-nodes --strict`. It catches R15 (source not in nodes)
and R18 (target not in nodes). Compare the connection keys with the node name values exactly — n8n is case-sensitive.

---

### "Webhook URL doesn't appear after import"

**Cause:** The webhook node is missing the `webhookId` field, or
`N8N_WEBHOOK_URL` is not set on the Docker container.

**Fix 1:** Check the webhook node in workflow.json has `"webhookId": "<uuid>"`.
The block-invalid-nodes hook catches this as R13.

**Fix 2:** On the VPS, verify:
```bash
docker compose exec n8n printenv WEBHOOK_URL
docker compose exec n8n printenv N8N_WEBHOOK_URL
```
Both should be `https://yourdomain.com/`.

---

### "Credential not found after import"

**Cause:** The workflow JSON has `REPLACE_WITH_CREDENTIAL_ID` which must be
replaced with the actual n8n credential ID.

**Fix:**
1. In n8n: Settings → Credentials → find your credential → copy the ID from the URL
2. In workflow.json: find `"REPLACE_WITH_CREDENTIAL_ID"` and replace with the copied ID
3. Re-import the workflow

**Better fix:** After import, open the node in n8n UI and select the credential
from the dropdown — this updates the credential reference in n8n's database
without needing to edit the JSON.

---

### "block-invalid-nodes fails with R21 orphan node"

**Cause:** A node exists in the `nodes` array but no connection points to it.

**Fix:** Check the `connections` object. The orphan node's name must appear
as a `node` value in at least one edge. If the node is intentional (e.g., a
debug note), connect it or remove it.

---

### "catalog-check returns false positives"

**Cause:** The Jaccard similarity threshold (default 0.20) is too low for your catalog.

**Fix:** Increase the threshold:
```bash
python hooks/catalog-check --query "..." --threshold 0.40
```
Or adjust the `STOP_WORDS` set in the hook to remove domain-specific common words.

---

### "enricher says node type UNKNOWN"

**Cause:** The node requested is a community node or very new official node
not in the core catalog, and the MCP fetch failed or returned no content.

**Fix:** Manually look up the node:
1. Search `docs.n8n.io` for the node
2. Find the `type` string (shown in node JSON examples on the docs page)
3. Find the `typeVersion` (shown in the parameters section)
4. Add the params manually to the enrichment spec and proceed

---

## 18. Quick-Start Cheatsheet

### Building a new workflow

```bash
# 1. Ask Claude (with Cursor/skill context loaded):
"Build a workflow that [your automation in plain English]"

# 2. Claude runs the pipeline (ROUTE → ENRICH → EXECUTE)
# 3. Review the generated workflow.json
# 4. Validate it
python hooks/block-invalid-nodes --file WORKSPACE_ROOT/workflows/<Name>/workflow.json

# 5. Check for duplicates
python hooks/catalog-check --query "[your description]"

# 6. Extract nodes
python scripts/extract_workflow.py \
  --input WORKSPACE_ROOT/workflows/<Name>/workflow.json \
  --output-dir WORKSPACE_ROOT/workflows/<Name>/nodes/

# 7. Import into n8n
#    n8n UI → Workflows → ⋮ → Import from File → select workflow.json

# 8. Replace credential IDs in the imported workflow
# 9. Run a manual test execution
# 10. Activate
```

### Checking what workflows exist

```bash
# Via hook
python hooks/catalog-check --query "slack notification"

# Via catalog file
grep -i "slack" WORKSPACE_ROOT/workflow-catalog.md
```

### Deploying a workflow via API

```bash
# Create (returns workflow with assigned ID)
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @WORKSPACE_ROOT/workflows/<Name>/workflow.json \
  https://$N8N_HOST/api/v1/workflows | jq '{id, name, active}'

# Activate
curl -s -X POST \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  https://$N8N_HOST/api/v1/workflows/<id>/activate

# List all active workflows
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "https://$N8N_HOST/api/v1/workflows?active=true" | jq '.data[] | {id, name}'
```

### Regenerating node documentation

```bash
# If you modify workflow.json, re-run extraction
python scripts/extract_workflow.py \
  --input WORKSPACE_ROOT/workflows/<Name>/workflow.json \
  --output-dir WORKSPACE_ROOT/workflows/<Name>/nodes/ \
  --summary-file WORKSPACE_ROOT/workflows/<Name>/guide.md
```

---

*Architecture version 1.0 — reflects repository state as of initial build.*
*Update this document when adding new agents, rules, or toolchain components.*
