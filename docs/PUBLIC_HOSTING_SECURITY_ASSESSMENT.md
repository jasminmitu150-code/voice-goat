# VoiceGoat Public Hosting Security Assessment

> **Date:** February 24, 2026  
> **Purpose:** Security review for hosting VoiceGoat as a public instance  
> **Status:** Pre-deployment assessment

---

## Executive Summary

VoiceGoat is an **intentionally vulnerable** security training platform. Hosting it publicly requires significant additional safeguards beyond the existing infrastructure. The current codebase contains **security issues by design** that must be addressed before any public deployment, even for training purposes.

---

## Infrastructure Security Concerns

### 1. No Authentication Layer

**Severity: CRITICAL**

All API endpoints are completely unauthenticated:

| Service | Issue |
|---------|-------|
| VoiceBank | `/chat`, `/transfer`, `/accounts/{user_id}` - no auth |
| VoiceAdmin | `/command`, `/tool`, `/query` - no auth, direct DB access |
| VoiceRAG | `/upload`, `/search`, `/embedding` - no auth |
| Dashboard | No session management |

**Risk for Public Hosting:**
- Anyone can access any user's data by guessing `user_id`
- Direct database manipulation via VoiceAdmin endpoints
- Unlimited document uploads (RAG poisoning by any user)
- No audit trail for accountability

### 2. CORS Configured as Open

**Severity: HIGH**

```python
# services/common/config.py
cors_origins: list[str] = ["*"]

# services/voice_gateway/app.py  
allow_origins=["*"]
```

This allows any website to make API calls to your hosted instance.

### 3. Exposed Infrastructure Ports

**Severity: HIGH**

The `docker-compose.yml` exposes all backend services directly:

| Port | Service | Risk |
|------|---------|------|
| 5432 | PostgreSQL | Direct DB access with `admin:admin` |
| 6379 | Redis | No authentication, session hijacking |
| 9200 | OpenSearch | Security disabled, full index access |
| 4566 | LocalStack | Mock AWS services exposed |

### 4. Hardcoded Credentials

**Severity: HIGH**

Multiple hardcoded credentials throughout:

**docker-compose.yml:**
```yaml
- DB_CONNECTION_STRING=postgresql://admin:admin@postgres:5432/voicegoat
- POSTGRES_USER=admin
- POSTGRES_PASSWORD=admin
- GF_SECURITY_ADMIN_PASSWORD=admin
```

**docker/init-db.sql:**
```sql
CREATE ROLE voicegoat WITH LOGIN PASSWORD 'voicegoat';
```

### 5. Overprivileged IAM Policies

**Severity: HIGH**

The Terraform ECS task role has `"dynamodb:*"` and `Resource = "*"`:

```hcl
# terraform/modules/ecs/main.tf
{
  Effect = "Allow"
  Action = ["dynamodb:*"]  # Should be GetItem, PutItem only
  Resource = "*"
}
```

---

## Resource Abuse Risks

### 6. No Rate Limiting

**Severity: HIGH**

There is no rate limiting on any endpoint. Public users could:
- Make unlimited LLM API calls (OpenAI/Bedrock), exhausting your budget
- Launch denial-of-service attacks
- Spam the RAG system with unlimited uploads
- Generate massive compute/storage costs

### 7. No Cost Controls

**Severity: HIGH**

| Service | Cost Risk |
|---------|-----------|
| OpenAI | Unlimited `/chat` calls at ~$0.01-0.03 per request |
| AWS Bedrock | Unlimited model invocations |
| AWS Polly | Unlimited TTS generation |
| AWS Transcribe | Unlimited STT processing |
| OpenSearch | Unbounded document indexing |
| Twilio | Unlimited phone calls if webhooks exposed |

### 8. Webhook Security

**Severity: MEDIUM**

Twilio webhooks lack signature validation:

```python
# services/voice_gateway/app.py
@app.get("/voice/incoming")
async def voice_incoming(request: Request):
    # No signature validation!
```

Anyone can call your webhook endpoints to trigger voice interactions.

---

## Data Security Concerns

### 9. Secrets in System Prompts

**Severity: HIGH**

Database connection strings and sensitive data are embedded in LLM prompts (LLM07 vulnerability demo), which could be extracted even with prompt injection defenses.

### 10. No Data Isolation

**Severity: HIGH**

All users share the same database and OpenSearch indices. The intentional cross-tenant vulnerability (LLM08) means any user can access any other user's documents.

### 11. No Encryption

**Severity: MEDIUM**

- No TLS enforcement between services
- No encryption at rest for databases
- No encrypted connections to OpenSearch

---

## Recommendations for Public Hosting

### Tier 1: Essential (Must Have Before Launch)

| # | Recommendation | Effort |
|---|----------------|--------|
| 1 | **Add authentication gateway** (AWS Cognito, Auth0, or custom JWT) | Medium |
| 2 | **Implement rate limiting** (per-user: 50 requests/min, per-IP: 100/min) | Low |
| 3 | **Set API spending caps** (OpenAI: budget alerts, Bedrock: throttling) | Low |
| 4 | **Remove direct port exposure** (only expose nginx gateway on 443) | Low |
| 5 | **Enable HTTPS/TLS** everywhere | Medium |
| 6 | **Restrict CORS** to your dashboard domain only | Low |
| 7 | **Add Twilio webhook signature validation** | Low |

### Tier 2: Strongly Recommended

| # | Recommendation | Effort |
|---|----------------|--------|
| 8 | **User isolation** - each user gets a separate namespace/tenant | High |
| 9 | **Secrets manager** (AWS Secrets Manager, not env vars) | Medium |
| 10 | **WAF (Web Application Firewall)** - AWS WAF with rate rules | Medium |
| 11 | **VPN-only access** (keep ALB internal, require VPN) | Medium |
| 12 | **Request logging and alerting** (CloudWatch, anomaly detection) | Medium |
| 13 | **Container image scanning** (ECR scanning, Trivy) | Low |
| 14 | **Database credential rotation** | Medium |

### Tier 3: Additional Hardening

| # | Recommendation | Effort |
|---|----------------|--------|
| 15 | **Network segmentation** (separate VPCs for data layer) | High |
| 16 | **Session timeout and token expiration** | Medium |
| 17 | **DDoS protection** (AWS Shield) | Medium |
| 18 | **Bug bounty scope definition** (legal safe harbor) | Low |
| 19 | **Terms of Service and acceptable use policy** | Low |

---

## Recommended Architecture for Public Hosting

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Public Internet                              │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                        ┌───────▼───────┐
                        │  AWS WAF      │  Rate limiting, SQL injection
                        │  + Shield     │  DDoS protection
                        └───────┬───────┘
                                │
                        ┌───────▼───────┐
                        │  CloudFront   │  CDN, HTTPS termination
                        │  (HTTPS only) │  
                        └───────┬───────┘
                                │
                        ┌───────▼───────┐
                        │  API Gateway  │  Auth, throttling, logging
                        │  + Cognito    │  User registration/login
                        └───────┬───────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
      ┌───────▼───────┐ ┌───────▼───────┐ ┌───────▼───────┐
      │  VoiceBank    │ │  VoiceAdmin   │ │  VoiceRAG     │
      │  (Private)    │ │  (Private)    │ │  (Private)    │
      └───────────────┘ └───────────────┘ └───────────────┘
              │                 │                 │
      ┌───────▼─────────────────▼─────────────────▼───────┐
      │         Private Data Layer (VPC Isolated)         │
      │   RDS (encrypted) │ OpenSearch │ ElastiCache     │
      └───────────────────────────────────────────────────┘
```

---

## Cost Estimation for Public Hosting Safeguards

| Service | Monthly Estimate | Notes |
|---------|-----------------|-------|
| AWS WAF | $5 + $1/M requests | Essential |
| API Gateway | $3.50/M requests | With throttling |
| Cognito | Free tier (50K MAU) | Authentication |
| CloudFront | ~$10-50 | Based on traffic |
| ALB + ECS | ~$50-200 | Current estimate |
| OpenAI API | **Variable** | Set hard budget |

**Budget Alert:** Set a hard cap on OpenAI spending (e.g., $100/month) to prevent runaway costs from abuse.

---

## Legal Considerations

Since this is an intentionally vulnerable application:

1. **Terms of Service**: Clearly state this is for educational use only
2. **Disclaimer**: Users must acknowledge they're accessing a vulnerable system
3. **Safe Harbor**: Define acceptable testing boundaries
4. **Data Privacy**: Don't allow real PII - provide test accounts
5. **Abuse Policy**: Define consequences for attacking infrastructure vs. intended vulnerabilities

---

## Summary

| Category | Current State | Required for Public |
|----------|--------------|---------------------|
| Authentication | ❌ None | ✅ Required |
| Rate Limiting | ❌ None | ✅ Required |
| HTTPS/TLS | ❌ None | ✅ Required |
| Cost Controls | ❌ None | ✅ Required |
| Secret Management | ❌ Hardcoded defaults | ✅ Required |
| Network Isolation | ❌ All ports exposed | ✅ Required |
| WAF/DDoS | ❌ None | ⚠️ Recommended |
| Audit Logging | ⚠️ Minimal | ⚠️ Recommended |

---

## Next Steps

1. [ ] **Week 1:** Implement authentication gateway
2. [ ] **Week 1:** Add rate limiting to all endpoints
3. [ ] **Week 2:** Configure HTTPS/TLS and restrict CORS
4. [ ] **Week 2:** Remove direct port exposure, only expose via gateway
5. [ ] **Week 3:** Set up cost alerts and spending caps
6. [ ] **Week 3:** Add Twilio webhook signature validation
7. [ ] **Week 4:** Deploy WAF rules
8. [ ] **Ongoing:** Security monitoring and alerting

---

**Bottom Line:** The project is well-designed for its intended purpose (security training in a controlled environment), but it requires substantial additional infrastructure to be safely hosted for public access. The most critical action is to **implement an authentication layer** before any public deployment.
