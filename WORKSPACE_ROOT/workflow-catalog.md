# Workflow Catalog

> Level 1 Index: keyword → workflow routing.
> Maintained automatically when new workflows are generated.
> Query with: `python hooks/catalog-check --query "your intent"`

## Usage

Each row maps a workflow to its trigger type, integrations, searchable keywords,
and the guide path. Add new rows every time a workflow is generated.

## Index

| Name | Trigger | Integrations | Keywords | Guide |
|---|---|---|---|---|
| _empty — add your first workflow_ | — | — | — | — |

---

## How to Add an Entry

When `workflow-architect` generates a new workflow, append a row:

```markdown
| Workflow Display Name | webhook/POST | Postgres, Slack | comma, separated, keywords | [guide](workflows/Workflow-Name/guide.md) |
```

## Naming Convention for Workflow Directories

Use PascalCase, hyphen-separated for multi-word names:
```
WORKSPACE_ROOT/workflows/
├── Lead-Ingestion-Pipeline/
├── Daily-Report-Generator/
└── Slack-Alert-On-Error/
```
