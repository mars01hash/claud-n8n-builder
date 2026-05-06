---
name: google-sheets
type: skill
version: 1.0.0
authority: n8n Docs + Google Workspace Best Practices
description: >
  Specialized skill for the Google Sheets node. Covers appending,
  reading, and updating rows.
---

# Skill: google-sheets

## 1. Node Metadata
- **Type**: `n8n-nodes-base.googleSheets`
- **Latest typeVersion**: 4.5
- **Credential Type**: `googleSheetsOAuth2Api`

## 2. Resource & Operation Mapping
| Intent | Resource | Operation | Key Parameters |
|---|---|---|---|
| "add row" | sheet | append | `documentId`, `sheetName`, `columns` |
| "find row" | sheet | read | `documentId`, `sheetName`, `filters` |
| "update row" | sheet | update | `documentId`, `sheetName`, `rowNumber` |

## 3. Optimized Expression Patterns
```javascript
// Mapping data to Sheet columns
{
  "mappingMode": "defineBelow",
  "value": {
    "Email": "={{ $json[\"email\"] }}",
    "Status": "active"
  }
}
```

## 4. Agentic Tips & Best Practices
- **Tip 1: Document ID**: The Document ID is the long string in the Sheet URL: `https://docs.google.com/spreadsheets/d/<ID>/edit`.
- **Tip 2: Header Row**: Ensure the Sheet has a header row (first row). n8n uses these names for mapping.
- **Tip 3: Ranges**: For reading specific blocks, use the `Range` option in the parameters.

## 5. Common Error Fixes
| Error | Root Cause | Fix |
|---|---|---|
| "Sheet not found" | Wrong sheetName | Check for trailing spaces or case differences in the sheet tab name. |
| "Insufficient permissions" | Scopes missing | Ensure the OAuth2 credential was created with `https://www.googleapis.com/auth/spreadsheets` scope. |

## 6. Security Hardening
- Share the Sheet with only the specific service account or user linked to the n8n credential.
- Avoid using "Anyone with the link can edit" for production sheets.
