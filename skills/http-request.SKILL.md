---
name: http-request
type: skill
version: 1.0.0
authority: n8n Docs + Web Standards
description: >
  Specialized skill for the HTTP Request node. Covers REST API calls,
  authentication mapping, and pagination.
---

# Skill: http-request

## 1. Node Metadata
- **Type**: `n8n-nodes-base.httpRequest`
- **Latest typeVersion**: 4.2
- **Credential Type**: `httpBearerAuth` | `httpHeaderAuth` | `httpBasicAuth` | `oAuth2Api`

## 2. Resource & Operation Mapping
| Intent | Operation | Key Parameters |
|---|---|---|
| "call API" | — | `method`, `url`, `authentication` |
| "fetch JSON" | — | `method: GET`, `url` |
| "POST JSON" | — | `method: POST`, `sendBody: true`, `bodyContentType: 'json'` |

## 3. Optimized Expression Patterns
```javascript
// Dynamic URL with query params
"={{ 'https://api.example.com/v1/users/' + $json[\"id\"] }}"

// Setting a dynamic Header
// (in parameters.headerParameters.parameters)
{ "name": "X-Transaction-ID", "value": "={{ $execution.id }}" }
```

## 4. Agentic Tips & Best Practices
- **Tip 1: Pagination**: For typeVersion 4+, use the built-in pagination section instead of manual loops.
- **Tip 2: Error Handling**: Set `options.response.fullResponse: true` if you need to see headers or status codes for debugging.
- **Tip 3: Body Format**: Always use `bodyContentType: 'json'` for modern APIs unless specified otherwise.

## 5. Common Error Fixes
| Error | Root Cause | Fix |
|---|---|---|
| "401 Unauthorized" | Missing/Wrong Credential | Verify `authentication` type and linked credential. |
| "400 Bad Request" | Malformed JSON Body | Check for missing required fields or invalid types. |

## 6. Security Hardening
- Never hardcode API keys in the URL or Body — always use the `credentials` section.
- Use `REPLACE_WITH_CREDENTIAL_ID` for all sensitive auth fields.
