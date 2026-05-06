---
name: <node-slug>
type: skill
version: 1.0.0
authority: n8n Docs + Agentic Best Practices
description: >
  Specialized skill for the <Node Name> node. Contains optimized parameters,
  common expression patterns, security hardening, and troubleshooting tips.
---

# Skill: <node-slug>

## 1. Node Metadata
- **Type**: `n8n-nodes-base.<slug>`
- **Latest typeVersion**: <version>
- **Credential Type**: `<credential-key>`

## 2. Resource & Operation Mapping
| Intent | Resource | Operation | Key Parameters |
|---|---|---|---|
| "<user intent>" | <resource> | <operation> | `<param>: <value>` |

## 3. Optimized Expression Patterns
```javascript
// Accessing data from this node
$("<Node Name>").first().json["field"]

// Common transformation
DateTime.fromISO($json["date"]).toFormat('yyyy-MM-dd')
```

## 4. Agentic Tips & Best Practices
- **Tip 1**: <e.g., Use batching for more than 100 items>
- **Tip 2**: <e.g., Always handle the error branch for this node>

## 5. Common Error Fixes
| Error | Root Cause | Fix |
|---|---|---|
| "<error message>" | <cause> | <fix> |

## 6. Security Hardening
- <e.g., Never expose the API key in the URL>
- <e.g., Use the internal Docker network for DB connections>
