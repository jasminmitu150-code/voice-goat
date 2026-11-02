# Changelog

## v0.1.0 - Initial Open-Source Release

### Vulnerability Services
- **VoiceBank** (LLM01: Prompt Injection) -- direct, indirect, payload splitting, and obfuscated injection challenges
- **VoiceAdmin** (LLM06: Excessive Agency) -- excessive functionality, permissions, autonomy, and abandoned plugin challenges
- **VoiceRAG** (LLM08: Vector & Embedding Weaknesses) -- cross-tenant leakage, RAG poisoning, embedding inversion, and access control bypass challenges

### Platform
- CTF-style dashboard with challenge hub, chat interface, and flag tracking
- Voice Gateway for Twilio phone call integration (WebSocket + HTTP)
- Nginx reverse proxy as unified entry point
- Docker Compose stack with all supporting infrastructure (Postgres, Redis, OpenSearch, LocalStack, Grafana)
- Terraform modules for AWS deployment (VPC, ECS Fargate, OpenSearch, monitoring)

### LLM Providers
- **Mock** provider (default) -- free, no API keys required
- **OpenAI** provider -- GPT-4o, GPT-4o-mini via OpenAI API
- **Bedrock** provider -- Claude, Titan via AWS Bedrock
- OpenAI-compatible base URL support (e.g., Ollama)

### Documentation
- Setup guide with local and AWS deployment instructions
- Architecture overview with service topology and data flows
- Challenge walkthroughs with hints, solutions, and prevention strategies
- Twilio voice integration guide
- Model considerations for LLM provider selection
- Public hosting security assessment
- Contributing guide and Code of Conduct
