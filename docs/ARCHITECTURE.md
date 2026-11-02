# VoiceGoat Architecture

This document describes VoiceGoat's system architecture, service responsibilities, and how components interact.

## System Overview

VoiceGoat is a modular platform where each service demonstrates a different OWASP LLM Top 10 vulnerability category. Services share a common library for configuration, LLM abstraction, and flag management.

```
                          ┌──────────────────────┐
                          │   Browser / Client    │
                          └──────────┬───────────┘
                                     │ HTTP
                          ┌──────────▼───────────┐
                          │  Nginx Gateway :8000  │
                          │  (routes by path)     │
                          └──┬─────┬─────┬────┬──┘
                 ┌───────────┘     │     │    └──────────┐
                 ▼                 ▼     ▼               ▼
          ┌────────────┐  ┌────────────┐ ┌──────────┐ ┌────────────┐
          │ Dashboard   │  │ VoiceBank  │ │VoiceAdmin│ │ VoiceRAG   │
          │ :4000       │  │ :8001      │ │ :8002    │ │ :8003      │
          │ (Next.js)   │  │ (LLM01)    │ │ (LLM06)  │ │ (LLM08)   │
          └────────────┘  └─────┬──────┘ └────┬─────┘ └─────┬──────┘
                                │              │             │
                                └──────┬───────┘─────────────┘
                                       │
                                ┌──────▼──────┐
                                │   Shared    │
                                │  Library    │
                                │  (common/)  │
                                └──┬──┬──┬────┘
                 ┌─────────────────┘  │  └──────────────┐
                 ▼                    ▼                  ▼
         ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
         │ LLM Provider │   │  LocalStack  │   │    Redis     │
         │ (Mock/OpenAI │   │  (DynamoDB,  │   │  (Session/   │
         │  /Bedrock)   │   │   S3, Secrets│   │   Cache)     │
         └──────────────┘   │   Manager)   │   └──────────────┘
                            └──────────────┘

  ┌──────────────┐           ┌──────────────┐     ┌──────────────┐
  │    Twilio     │ ────────▶│Voice Gateway │────▶│ VoiceBank/   │
  │  (Phone)     │  TwiML/  │   :8004      │HTTP │ Admin/RAG    │
  └──────────────┘  WebSocket└──────────────┘     └──────────────┘
```

## Services

### VoiceBank (LLM01: Prompt Injection)

A simulated banking assistant vulnerable to prompt injection attacks.

| Item | Detail |
|------|--------|
| Port | 8001 (host) / 8000 (container) |
| Source | `services/voicebank/app.py` |
| Endpoints | `/chat`, `/transfer`, `/conversation`, `/voice-memo`, `/accounts/{user_id}`, `/payees`, `/flags` |
| Flags | `FLAG{LLM01_DIRECT_001}`, `FLAG{LLM01_INDIRECT_001}`, `FLAG{LLM01_SPLIT_001}`, `FLAG{LLM01_OBFUSCATED_001}` |

### VoiceAdmin (LLM06: Excessive Agency)

A system administration assistant with intentionally overprivileged tools.

| Item | Detail |
|------|--------|
| Port | 8002 (host) / 8000 (container) |
| Source | `services/voiceadmin/app.py` |
| Endpoints | `/command`, `/tool`, `/tools`, `/users`, `/email`, `/emails`, `/query`, `/config`, `/flags` |
| Flags | `FLAG{LLM06_FUNC_001}`, `FLAG{LLM06_PERM_001}`, `FLAG{LLM06_AUTO_001}`, `FLAG{LLM06_LEGACY_001}` |

### VoiceRAG (LLM08: Vector & Embedding Weaknesses)

A knowledge base assistant with flawed tenant isolation and content validation.

| Item | Detail |
|------|--------|
| Port | 8003 (host) / 8000 (container) |
| Source | `services/voicerag/app.py` |
| Endpoints | `/chat`, `/search`, `/upload`, `/embedding`, `/embeddings/{doc_id}`, `/documents`, `/documents/{doc_id}`, `/tenants`, `/profile`, `/profile/{user_id}`, `/flags` |
| Flags | `FLAG{LLM08_TENANT_001}`, `FLAG{LLM08_POISON_001}`, `FLAG{LLM08_INVERT_001}`, `FLAG{LLM08_INTERNAL_ACCESS_001}`, `FLAG{LLM08_SECURITY_AUDIT_001}`, `FLAG{LLM08_ROOT_PASSWORD_001}` |

### Voice Gateway (Twilio Integration)

Bridges Twilio phone calls to the backend services via WebSocket and HTTP. Handles speech-to-text (OpenAI Whisper or AWS Transcribe) and text-to-speech (OpenAI TTS or AWS Polly).

| Item | Detail |
|------|--------|
| Port | 8004 (host) / 8000 (container) |
| Source | `services/voice_gateway/app.py`, `media_stream.py`, `audio_processor.py` |
| Endpoints | `/voice/incoming`, `/voice/status`, `/media-stream` (WebSocket), `/interact`, `/services`, `/health` |

### Dashboard (Next.js)

A CTF-style scoreboard and chat interface for interacting with the vulnerable services.

| Item | Detail |
|------|--------|
| Port | 4000 (host) / 3000 (container) |
| Source | `dashboard/app/` |
| Pages | `/` (challenge hub), `/chat` (VoiceBank/VoiceAdmin chat), `/rag` (VoiceRAG interface) |

### Nginx Gateway

Reverse proxy that provides a unified entry point on port 8000, routing by URL path to the appropriate backend.

| Path | Backend |
|------|---------|
| `/` | Dashboard |
| `/api/voicebank/`, `/voicebank/` | VoiceBank |
| `/api/voiceadmin/`, `/voiceadmin/` | VoiceAdmin |
| `/api/voicerag/`, `/voicerag/` | VoiceRAG |
| `/health` | Static 200 OK |

## Shared Library (`services/common/`)

All Python services import from `services.common`:

- **`config.py`** -- Pydantic `Settings` loaded from `.env`. Defines LLM provider, speech mode, AWS, OpenSearch, Redis, and security settings.
- **`logging.py`** -- Structured logging via `structlog`.
- **`flags/`** -- Flag definitions, `FlagService` (DynamoDB or in-memory), and the `@vulnerable` decorator for tagging endpoints.
- **`llm/`** -- LLM provider abstraction. `get_llm_client()` returns a `MockLLMClient`, `OpenAIClient`, or `BedrockClient` based on `LLM_PROVIDER`.
- **`speech/`** -- AWS Polly (TTS) and Transcribe (STT) helpers.

## LLM Provider Abstraction

```
┌──────────────────────────────────────┐
│           get_llm_client()           │
├──────────┬───────────┬───────────────┤
│   Mock   │  OpenAI   │   Bedrock     │
│ (default)│           │               │
│ Free, no │ GPT-4o,   │ Claude, Titan │
│ API call │ GPT-4o-   │ via AWS SDK   │
│          │ mini      │               │
└──────────┴───────────┴───────────────┘
```

- **Mock**: Returns canned responses that include flags. Zero cost, no external dependencies. Ideal for first-time setup and CI.
- **OpenAI**: Real LLM responses via the OpenAI API. Requires `OPENAI_API_KEY`. Recommended for realistic vulnerability testing.
- **Bedrock**: AWS-native LLM via boto3. Requires AWS credentials with Bedrock access.

## Infrastructure Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| Redis | `redis:7-alpine` | 6379 | Session/cache (configured, not yet wired into app logic) |
| Postgres | `postgres:16-alpine` | 5432 | Stores banking/admin/secrets schemas with intentionally vulnerable data |
| OpenSearch | `opensearchproject/opensearch:2.11.0` | 9200, 9600 | Vector DB (configured, VoiceRAG currently uses in-memory mock) |
| OpenSearch Dashboards | `opensearchproject/opensearch-dashboards:2.11.0` | 5601 | OpenSearch UI |
| LocalStack | `localstack/localstack:latest` | 4566 | Mocks DynamoDB (flags), S3 (documents), Secrets Manager |
| Grafana | `grafana/grafana:latest` | 4001 | Observability dashboards (optional) |

## Network & Port Map

All services join a `voicegoat` Docker bridge network and resolve each other by service name.

| Host Port | Service | Container Port |
|-----------|---------|----------------|
| 8000 | Nginx Gateway | 80 |
| 8001 | VoiceBank | 8000 |
| 8002 | VoiceAdmin | 8000 |
| 8003 | VoiceRAG | 8000 |
| 8004 | Voice Gateway | 8000 |
| 4000 | Dashboard | 3000 |
| 4001 | Grafana | 3000 |
| 5432 | Postgres | 5432 |
| 6379 | Redis | 6379 |
| 9200 | OpenSearch | 9200 |
| 5601 | OpenSearch Dashboards | 5601 |
| 4566 | LocalStack | 4566 |

## Data Flow: Text Chat

1. User opens Dashboard at `http://localhost:8000` (via gateway) or `http://localhost:4000` (direct).
2. Dashboard sends `POST /chat` (or `/command`, `/search`) to the appropriate service port.
3. The service builds a prompt with the user's input and any retrieved context.
4. `get_llm_client()` sends the prompt to the configured LLM provider (or returns a mock response).
5. `FlagService.check_response_for_flags()` scans the response for captured flags.
6. The response (with any captured flags) is returned to the dashboard.

## Data Flow: Voice Call (Twilio)

1. Caller dials the Twilio phone number.
2. Twilio sends a webhook to Voice Gateway at `/voice/incoming`.
3. Voice Gateway returns TwiML instructing Twilio to open a Media Stream WebSocket.
4. Audio frames arrive at `/media-stream`; `TwilioMediaStreamHandler` decodes ulaw audio.
5. Voice Activity Detection (VAD) detects speech end, then audio is sent to Whisper STT.
6. Transcribed text is forwarded via HTTP to the selected backend service (`/chat` or `/command`).
7. The text response is synthesized to audio via OpenAI TTS (or AWS Polly).
8. Audio is streamed back through the Twilio WebSocket to the caller.

## AWS Deployment (Terraform)

The `terraform/` directory contains modules for deploying VoiceGoat to AWS:

- **VPC** -- Private subnets, NAT gateway, optional Client VPN
- **ECS** -- Fargate cluster with ALB, task definitions for each service
- **OpenSearch** -- Managed domain in VPC
- **Monitoring** -- CloudWatch log groups and dashboards
