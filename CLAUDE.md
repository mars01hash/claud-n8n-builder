# n8n MCP Skill Repository

This repository gives Claude a complete, structured skill set for building,
validating, and managing n8n workflows in a Dockerized VPS environment.

## Agent Lifecycle

Every automation request flows through three agents in sequence:

```
User Request
    │
    ▼
query-navigator          (ROUTE)   → classifies intent, checks catalog, dispatches
    │
    ▼
n8n-enricher             (ENRICH)  → resolves node types, credentials, expressions
    │
    ▼
workflow-architect        (EXECUTE) → generates workflow.json + guide.md + node files
```

## Active Skills

Load this skill before any n8n work:
- `skills/n8n-mcp-cli.SKILL.md` — full n8n API, schema, node catalog, Docker rules

## Active Agents

These agents are always available in this project:
- `agents/query-navigator.agent.md`
- `agents/n8n-enricher.agent.md`
- `agents/workflow-architect.agent.md`

## Validation & Quality Gates

Before any workflow.json is finalized:
1. Run `python hooks/block-invalid-nodes --file workflow.json`
2. Run `python hooks/catalog-check --query "<description>"`
3. If validation passes, run `python scripts/extract_workflow.py --input workflow.json --output-dir WORKSPACE_ROOT/workflows/<Name>/nodes/`

## Output Directory

All generated workflows go to:
```
WORKSPACE_ROOT/workflows/<Workflow-Name>/
├── workflow.json
├── guide.md
└── nodes/
    ├── {node_slug}.json
    └── {node_slug}.guide.md
```

## Templates (Read-Only)

Do not modify files in `templates/scaffolding/` — they are reference patterns only.
Copy and customize for new workflows:
- `webhook-workflow.json` — POST endpoint → process → respond
- `http-request-workflow.json` — scheduled API fetch → filter → transform
- `loop-workflow.json` — batch processing with splitInBatches

## Rules

1. Never set `"active": true` in generated JSON
2. Never embed credentials — always use `REPLACE_WITH_CREDENTIAL_ID` placeholders
3. Always run both hooks before writing to WORKSPACE_ROOT
4. Always update `WORKSPACE_ROOT/workflow-catalog.md` after generating a workflow
5. Use node names from `n8n-nodes-base.*` catalog only — no invented types
