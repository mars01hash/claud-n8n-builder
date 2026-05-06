---
name: airtable
type: skill
version: 1.0.0
authority: n8n Docs + Agentic Best Practices
description: >
  Specialized skill for the Airtable node. Handles base/table operations
  with token-based authentication.
---

# Skill: airtable

## 1. Node Metadata
- **Type**: `n8n-nodes-base.airtable`
- **Latest typeVersion**: 1
- **Credential Type**: `airtableTokenApi`

## 2. Resource & Operation Mapping
| Intent | Resource | Operation | Key Parameters |
|---|---|---|---|
| "append a row" | sheet | append | `base`, `table`, `dataMode: 'mapping'` |
| "read a row" | sheet | read | `base`, `table`, `id` |

## 3. Optimized Expression Patterns
```javascript
// Accessing Airtable row ID
$node["Airtable"].json["id"]

// Mapping incoming webhook body to Airtable fields
{
  "Email": "={{ $json[\"body\"][\"email\"] }}",
  "Name": "={{ $json[\"body\"][\"name\"] }}"
}
```

## 4. Agentic Tips & Best Practices
- **Tip 1**: Use `dataMode: 'mapping'` when you want to explicitly map fields from previous nodes.
- **Tip 2**: Ensure the column names in Airtable match the keys in your mapping exactly (case-sensitive).

## 5. Common Error Fixes
| Error | Root Cause | Fix |
|---|---|---|
| "Base not found" | Incorrect Base ID or Token scope | Verify Base ID in Airtable URL and ensure token has `data.records:write` scope. |

## 6. Security Hardening
- Use Airtable Personal Access Tokens (PAT) instead of deprecated API keys.
- Limit PAT scope to only the specific base and operations required.
