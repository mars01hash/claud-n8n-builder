---
name: slack
type: skill
version: 1.0.0
authority: n8n Docs + Slack API Best Practices
description: >
  Specialized skill for the Slack node. Covers message posting, blocks,
  and channel management.
---

# Skill: slack

## 1. Node Metadata
- **Type**: `n8n-nodes-base.slack`
- **Latest typeVersion**: 2.2
- **Credential Type**: `slackOAuth2Api`

## 2. Resource & Operation Mapping
| Intent | Resource | Operation | Key Parameters |
|---|---|---|---|
| "send message" | message | post | `channel`, `text` |
| "upload file" | file | upload | `channel`, `binaryPropertyName` |
| "add reaction" | reaction | add | `channel`, `timestamp`, `name` |

## 3. Optimized Expression Patterns
```javascript
// Mentioning a user by ID
"={{ 'Hello <@' + $json[\"slackId\"] + '>' }}"

// Simple Slack notification text
"={{ '✅ New lead: ' + $json[\"name\"] + ' (' + $json[\"email\"] + ')' }}"
```

## 4. Agentic Tips & Best Practices
- **Tip 1: Bot Scopes**: Ensure the Slack App has `chat:write`, `channels:read`, and `files:write` scopes.
- **Tip 2: Block Kit**: For rich messages, use the `blocks` parameter with Slack's Block Kit JSON.
- **Tip 3: Rate Limits**: Slack has strict rate limits (Tier 3 for chat.postMessage). Avoid sending more than 1 message per second in loops.

## 5. Common Error Fixes
| Error | Root Cause | Fix |
|---|---|---|
| "channel_not_found" | Bot not in channel | Invite the bot to the channel (`/invite @BotName`). |
| "invalid_auth" | Expired token | Re-authenticate the Slack OAuth2 credential in n8n. |

## 6. Security Hardening
- Use Bot Tokens instead of User Tokens whenever possible.
- Rotate the Client Secret if the VPS environment is compromised.
