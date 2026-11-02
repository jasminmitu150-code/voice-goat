# VoiceGoat

> A purposely vulnerable voice agent application for security practitioners to practice exploiting voice-based AI systems.

[![OWASP LLM Top 10](https://img.shields.io/badge/OWASP-LLM%20Top%2010-orange)](https://genai.owasp.org/llm-top-10/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Disclaimer

**This application is intentionally vulnerable.** It is designed for educational and security training purposes only. Do NOT deploy this in production or expose it to the public internet without proper safeguards. See [Public Hosting Security Assessment](docs/PUBLIC_HOSTING_SECURITY_ASSESSMENT.md) for details.

## Demo

> **Warning:** This video contains **spoilers** including challenge solutions and flag captures.

[![VoiceGoat Demo](https://img.youtube.com/vi/mnf5IpNUHg8/maxresdefault.jpg)](https://www.youtube.com/watch?v=mnf5IpNUHg8)

## Overview

VoiceGoat is a modular vulnerable voice agent platform that covers the [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/). Security practitioners can use this platform to:

- Learn about LLM vulnerabilities in a safe environment
- Practice red team techniques against voice agents
- Understand real-world attack vectors
- Capture flags (CTF-style) for successful exploits

## Vulnerability Coverage

| Service | OWASP Category | Vulnerabilities |
|---------|----------------|-----------------|
| **VoiceBank** | LLM01: Prompt Injection | Direct, Indirect, Payload Splitting, Obfuscated |
| **VoiceAdmin** | LLM06: Excessive Agency | Excessive Functionality, Permissions, Autonomy |
| **VoiceRAG** | LLM08: Vector/Embedding | Cross-tenant leakage, RAG Poisoning, Access Bypass |

## Prerequisites

- **Docker** & **Docker Compose** v2.0+ (required)
- **Python 3.11+** (optional, for local service development without Docker)
- **Node.js 20+** (optional, for dashboard development without Docker)
- **OpenAI API key** (optional, only needed when using `LLM_PROVIDER=openai`)

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/redcaller/voice-goat.git
cd voice-goat

# 2. Create your environment file
cp .env.example .env
# Edit .env if you want to use a real LLM provider (default is mock)

# 3. Start all services
docker compose up -d

# 4. Verify services are healthy
curl http://localhost:8001/health   # VoiceBank
curl http://localhost:8002/health   # VoiceAdmin
curl http://localhost:8003/health   # VoiceRAG

# 5. Open the dashboard
open http://localhost:8000          # Via Nginx gateway (recommended)
# or  http://localhost:4000          # Direct to Next.js
```

> **Tip:** The default `LLM_PROVIDER=mock` requires no API keys and is completely free.
> Switch to `openai` for realistic LLM behavior when you're ready.

### Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 8000 | Nginx Gateway | Unified entry point (dashboard + API routes) |
| 8001 | VoiceBank | LLM01 challenges |
| 8002 | VoiceAdmin | LLM06 challenges |
| 8003 | VoiceRAG | LLM08 challenges |
| 8004 | Voice Gateway | Twilio voice integration |
| 4000 | Dashboard | Next.js CTF interface (direct) |
| 4001 | Grafana | Monitoring dashboards |
| 5432 | Postgres | Database |
| 6379 | Redis | Cache |
| 9200 | OpenSearch | Vector DB |
| 5601 | OpenSearch Dashboards | OpenSearch UI |
| 4566 | LocalStack | AWS service mocks |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ VoiceBank   │  │ VoiceAdmin  │  │ VoiceRAG    │         │
│  │ (LLM01)     │  │ (LLM06)     │  │ (LLM08)     │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         └────────────────┼─────────────────┘               │
│                   ┌──────┴──────┐                           │
│                   │   Shared    │                           │
│                   │   Library   │                           │
│                   └──────┬──────┘                           │
│              ┌───────────┼───────────┐                      │
│         ┌────┴────┐ ┌────┴────┐ ┌───┴─────┐               │
│         │LLM (Mock│ │LocalStack│ │  Redis  │               │
│         │/OpenAI/ │ │(DynamoDB │ │         │               │
│         │Bedrock) │ │ S3, SM)  │ │         │               │
│         └─────────┘ └─────────┘ └─────────┘               │
└─────────────────────────────────────────────────────────────┘
```

See [Architecture Deep Dive](docs/ARCHITECTURE.md) for full details including data flows, network topology, and Terraform deployment.

## Project Structure

```
voice-goat/
├── services/               # Python FastAPI services
│   ├── common/             # Shared config, LLM, flags, logging
│   ├── voicebank/          # LLM01: Prompt Injection
│   ├── voiceadmin/         # LLM06: Excessive Agency
│   ├── voicerag/           # LLM08: Vector Weaknesses
│   └── voice_gateway/      # Twilio voice integration
├── dashboard/              # Next.js CTF scoreboard & chat UI
├── docker/                 # Nginx, Postgres init, LocalStack init
├── terraform/              # AWS infrastructure as code
├── docs/                   # Documentation & challenge walkthroughs
├── docker-compose.yml      # Local development stack
├── pyproject.toml          # Python dependencies & tool config
└── .env.example            # Environment variable template
```

## Gamification

Each vulnerability has an associated flag:

```
FLAG{CATEGORY_TYPE_ID}
Example: FLAG{LLM01_DIRECT_001}
```

### Difficulty Levels

- **Easy**: Obvious vulnerabilities, minimal obfuscation
- **Medium**: Requires understanding of the vulnerability
- **Hard**: Needs chaining, custom payloads, or deep knowledge

## LLM Providers

VoiceGoat supports multiple LLM backends:

| Provider | Description | Cost |
|----------|-------------|------|
| `mock` | Simulated responses (default) | Free |
| `openai` | OpenAI API (GPT-4o, GPT-4o-mini) | Pay-per-use |
| `bedrock` | AWS Bedrock (Claude, Titan) | Pay-per-use |

Configure via `.env`:

```bash
# Mock mode (default) -- free, no API keys needed
LLM_PROVIDER=mock

# OpenAI -- real LLM responses
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# AWS Bedrock -- requires AWS credentials
LLM_PROVIDER=bedrock
```

> You can also point `OPENAI_BASE_URL` at an [Ollama](https://ollama.com/) instance or any OpenAI-compatible API for free local inference. See [Model Considerations](docs/MODEL_CONSIDERATIONS.md).

## Voice Integration (Twilio)

VoiceGoat supports real phone calls via Twilio Media Streams.

```bash
# 1. Set OpenAI provider (required for speech processing)
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key
docker compose up -d

# 2. Expose voice gateway with ngrok
ngrok http 8004

# 3. Configure Twilio webhook to your ngrok URL
# 4. Call your Twilio number!
```

See [Twilio Setup Guide](docs/TWILIO_SETUP.md) for detailed instructions.

## Speech Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `text` | Text-only simulation (default) | Local development, free |
| `speech` | Full speech integration | Realistic testing with Twilio |
| `both` | Hybrid mode | Best of both worlds |

Set via environment variable: `SPEECH_MODE=text`

## Troubleshooting

<details>
<summary><strong>Services fail to start / connection refused</strong></summary>

```bash
# Check service logs
docker compose logs voicebank

# Rebuild and restart
docker compose down
docker compose up -d --build
```
</details>

<details>
<summary><strong>Postgres init fails</strong></summary>

If you've previously run VoiceGoat and the Postgres data volume already exists, the init script won't re-run. Reset with:

```bash
docker compose down -v   # removes volumes
docker compose up -d
```
</details>

<details>
<summary><strong>"OPENAI_API_KEY not set" errors</strong></summary>

Make sure your `.env` file has `LLM_PROVIDER=mock` (the default) if you don't have an OpenAI key. Mock mode requires no API keys.
</details>

<details>
<summary><strong>Dashboard shows "Error connecting"</strong></summary>

The dashboard talks directly to service ports (8001-8003). Ensure those containers are running:

```bash
docker compose ps
```

Services may take 10-20 seconds to become healthy after starting.
</details>

<details>
<summary><strong>Port conflicts</strong></summary>

If ports 8000-8004, 4000-4001, 5432, 6379, or 9200 are already in use, stop the conflicting process or edit `docker-compose.yml` to remap ports.
</details>

<details>
<summary><strong>Apple Silicon / ARM issues</strong></summary>

All images used are multi-arch or have ARM variants. If you encounter issues, try `docker compose build --no-cache`.
</details>

## Documentation

- [Setup Guide](docs/SETUP.md) -- detailed installation and configuration
- [Architecture](docs/ARCHITECTURE.md) -- system design and data flows
- [Challenge Walkthroughs](docs/challenges/) -- hints and solutions for each flag
- [Twilio Setup](docs/TWILIO_SETUP.md) -- voice call integration
- [Model Considerations](docs/MODEL_CONSIDERATIONS.md) -- choosing an LLM provider
- [Contributing](CONTRIBUTING.md) -- how to contribute
- [Code of Conduct](CODE_OF_CONDUCT.md)

## Security Considerations

- Deploy only in isolated environments (local Docker or private VPCs)
- Use VPN access for AWS deployments
- Do not use real data or production credentials
- Monitor for unintended exposure
- See [Public Hosting Security Assessment](docs/PUBLIC_HOSTING_SECURITY_ASSESSMENT.md)

## References

- [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/)
- [AWS LLM Security Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-security/)
- [MITRE ATLAS](https://atlas.mitre.org/)

## License

MIT License - See [LICENSE](LICENSE) for details.
