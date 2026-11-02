# VoiceGoat: Vulnerable Voice Agent for Security Training

## Project Vision
A purposely vulnerable voice agent application designed for security practitioners to practice exploiting voice-based AI systems. Covers all OWASP Top 10 LLM vulnerabilities with gamified flags for successful exploitation.

---

## Architecture Considerations

### Implementation Patterns to Include
| Pattern | Description | AWS Services |
|---------|-------------|--------------|
| **Speech-to-Text-to-LLM-to-Text-to-Speech** | Traditional pipeline with discrete components | Amazon Transcribe → Bedrock → Polly |
| **Speech-to-Speech (Native)** | End-to-end multimodal processing | Amazon Nova Sonic (when available) / OpenAI Realtime API |
| **Hybrid** | Mix of pipelines for different features | Combination |

### Cloud Deployment (AWS Primary)
- **Infrastructure as Code**: Terraform + CDK
- **Core Services**: Lambda, API Gateway, Bedrock, Transcribe, Polly, DynamoDB, OpenSearch (for RAG)
- **Observability**: CloudWatch, X-Ray
- **Optional**: Azure (Azure Speech + OpenAI) / GCP (Speech-to-Text + Vertex AI)

---

## OWASP LLM Top 10 Attack Scenarios & Proposed Features

### LLM01:2025 - Prompt Injection

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Direct Injection** | New instructions injected via main channel | Banking assistant that can be tricked to reveal account info | FLAG{DIRECT_INJECTION_001} in "secret" account |
| **Indirect Injection** | Instructions from external data sources | Calendar integration that reads malicious meeting descriptions | FLAG in hidden calendar event |
| **Unintentional Injection** | Common phrases trigger hidden prompts | Phrase "help me help you" triggers debug mode | FLAG in debug output |
| **Intentional Model Influence** | RAG data contains embedded instructions | FAQ documents with hidden instructions | FLAG in manipulated FAQ response |
| **Code Injection** | Exploit code vulnerabilities for prompt injection | Voice-triggered code execution feature | FLAG in environment variable |
| **Payload Splitting** | Malicious prompt split across conversation | Multi-turn conversation reconstructs attack | FLAG only visible after combining |
| **Multimodal Injection** | Hidden prompt in image metadata/audio watermarks | Profile picture with embedded instructions | FLAG{MULTIMODAL_001} |
| **Adversarial Suffix** | Meaningless characters bypass filters | Special voice patterns/noises that bypass | FLAG revealed on bypass |
| **Multilingual/Obfuscated** | Base64, emoji, multiple languages | Support for "encoded" commands | FLAG{OBFUSCATED_001} |

---

### LLM02:2025 - Sensitive Information Disclosure

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **PII Leakage** | Model reveals personal information | Customer service agent with access to user database | FLAG in leaked PII |
| **Proprietary Algorithm Exposure** | Internal business logic revealed | Pricing algorithm that can be extracted | FLAG{ALGORITHM_001} |
| **Training Data Extraction** | Extract memorized training data | Model trained on sensitive documents | FLAG in training data |
| **System Context Leakage** | Internal prompts/configs exposed | Verbose error messages reveal config | FLAG in error response |

---

### LLM03:2025 - Supply Chain

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Vulnerable Dependency** | Compromised package | Intentionally vulnerable PyPI package | FLAG when exploited |
| **Model Tampering (PoisonGPT-style)** | Backdoored fine-tuned model | Pre-trained model with hidden trigger | FLAG{TAMPERED_MODEL} |
| **Malicious LoRA Adapter** | Compromised fine-tuning adapter | Adapter that activates on keyword | FLAG in adapter response |
| **Hugging Face Model Swap** | Fake model on model hub | Model repo with similar name | FLAG when fake model used |
| **Pickle Deserialization** | Malicious serialized model | Model file with embedded code | FLAG{PICKLE_RCE} |

---

### LLM04:2025 - Data and Model Poisoning

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Training Data Poisoning** | Biased/malicious training data | Feedback system that accepts poisoned data | FLAG after bias injected |
| **RAG Poisoning** | Poisoned retrieval documents | Document upload feature (no validation) | FLAG{RAG_POISON_001} |
| **Backdoor Trigger** | Hidden activation trigger | Model responds differently to specific phrase | FLAG on trigger activation |
| **Split-View Poisoning** | Different data shown to users vs training | Admin panel showing "safe" data while training on malicious | FLAG in poisoned output |

---

### LLM05:2025 - Improper Output Handling

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Remote Code Execution** | LLM output executed as code | "Run this command" feature with eval() | FLAG in /tmp/flag.txt |
| **XSS via Markdown** | Unsanitized output rendered in browser | Web dashboard displaying LLM responses | FLAG{XSS_001} via alert() |
| **SQL Injection** | LLM-generated queries not parameterized | Natural language database queries | FLAG in hidden DB table |
| **SSRF** | LLM output used for URL fetching | "Summarize this website" feature | FLAG at internal endpoint |
| **Path Traversal** | File paths from LLM not sanitized | "Read this file" functionality | FLAG in /etc/voicegoat/flag |

---

### LLM06:2025 - Excessive Agency

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Excessive Functionality** | Too many tools available | Email agent with send/delete/forward | FLAG when email exfiltrated |
| **Excessive Permissions** | Over-privileged database access | DB connector with WRITE access (only needs READ) | FLAG{EXCESSIVE_WRITE} |
| **Excessive Autonomy** | No human approval for actions | Auto-transfer money feature | FLAG when unauthorized transfer |
| **Abandoned Plugin** | Old functionality still accessible | Deprecated admin commands still work | FLAG via deprecated command |
| **Open-Ended Shell** | Unrestricted command execution | "System administration" voice commands | FLAG{SHELL_001} |

---

### LLM07:2025 - System Prompt Leakage

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Direct Extraction** | "What is your system prompt?" | Weak system prompt protection | FLAG{SYSTEM_PROMPT} in prompt |
| **Indirect Extraction** | Inferring rules from behavior | Complex filtering rules in prompt | FLAG in hidden instructions |
| **Credential Exposure** | API keys in system prompt | Database connection string in prompt | FLAG{CREDS_LEAK} |
| **Role/Permission Disclosure** | Internal role structure revealed | Admin escalation instructions in prompt | FLAG when role extracted |

---

### LLM08:2025 - Vector and Embedding Weaknesses

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Cross-Tenant Leakage** | Multi-user vector DB leaks data | Shared RAG system without tenant isolation | FLAG from other user's data |
| **Embedding Inversion** | Reconstruct original text from vectors | API exposing raw embeddings | FLAG{EMBEDDING_INVERSION} |
| **RAG Poisoning** | Malicious documents in knowledge base | Public document upload to RAG | FLAG in poisoned response |
| **Access Control Bypass** | Retrieve unauthorized documents | Documents with different permission levels | FLAG{UNAUTHORIZED_DOC} |

---

### LLM09:2025 - Misinformation

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Hallucinated Packages** | Fake library recommendations | Coding assistant suggesting fake packages | FLAG when fake package installed |
| **Medical Misinformation** | Harmful health advice | Health assistant with no guardrails | FLAG{MEDICAL_MISINFO} |
| **Legal Hallucination** | Fabricated legal cases | Legal research assistant | FLAG in fake case citation |
| **Confidence Manipulation** | High confidence on wrong answers | Finance advisor with no fact-checking | FLAG{OVERCONFIDENT} |

---

### LLM10:2025 - Unbounded Consumption

| Attack Type | Description | Proposed VoiceGoat Feature | Flag Location |
|------------|-------------|---------------------------|---------------|
| **Denial of Service** | Resource exhaustion | No rate limiting on API | FLAG{DOS_001} when crashed |
| **Denial of Wallet** | Cost exploitation | Pay-per-use feature with no caps | FLAG{DOW_001} |
| **Model Extraction** | Steal model via API | Verbose API with logprobs exposed | FLAG when model replicated |
| **Context Overflow** | Exceed context window | Conversation with no length limits | FLAG{OVERFLOW_001} |
| **Recursive Queries** | Self-referential loops | Agent can call itself | FLAG when loop detected |

---

## Gamification Design

### Flag System
```
FLAG{CATEGORY_SUBCATEGORY_DIFFICULTY_UNIQUE}
Example: FLAG{LLM01_DIRECT_EASY_001}
```

### Difficulty Levels
- 🟢 **Easy**: Obvious vulnerabilities, minimal obfuscation
- 🟡 **Medium**: Requires understanding of the vulnerability
- 🔴 **Hard**: Needs chaining, custom payloads, or deep knowledge

### Scoreboard
- Track progress per OWASP category
- Time-based challenges
- Hints system (costs points)

---

## Voice-Specific Attack Vectors

### Unique to Voice Agents
| Attack | Description | Implementation |
|--------|-------------|----------------|
| **Acoustic Injection** | Inaudible/ultrasonic commands | Hidden audio frequencies in media |
| **Voice Cloning Attack** | Impersonate authorized user | Weak voice biometric authentication |
| **Homophone Exploitation** | "Bye bye" vs "Buy buy" | Transaction triggered by similar sounds |
| **Accent/Dialect Bypass** | Filters trained on specific accents | Commands in different accents bypass |
| **Background Audio Injection** | TV/Radio triggers actions | Agent processes ambient audio |
| **Speech Rate Manipulation** | Very fast/slow speech bypass | Timing-based filter evasion |

---

## Proposed Application Personas

### 1. VoiceBank Assistant
- Banking operations via voice
- Account info, transfers, bill pay
- **Vulnerabilities**: LLM01, LLM02, LLM05, LLM06

### 2. VoiceMed Advisor
- Health information assistant
- Symptom checking, appointment scheduling
- **Vulnerabilities**: LLM02, LLM09

### 3. VoiceCode Assistant
- Coding help via voice
- Package recommendations, code generation
- **Vulnerabilities**: LLM03, LLM05, LLM09

### 4. VoiceAdmin Console
- System administration via voice
- Server management, user provisioning
- **Vulnerabilities**: LLM05, LLM06, LLM07

### 5. VoiceRAG Knowledge Base
- Company knowledge base queries
- Document retrieval and summarization
- **Vulnerabilities**: LLM04, LLM08

### 6. VoiceShop Assistant
- E-commerce via voice
- Product search, purchases
- **Vulnerabilities**: LLM01, LLM06, LLM10

---

## Open Questions for Discussion

### Architecture
1. **Single unified agent vs. multiple specialized agents?**
   - Unified: Simpler deployment, harder to isolate vulnerabilities
   - Multiple: More realistic, easier to target specific OWASP categories

2. **How to handle real speech processing?**
   - Full speech integration (Transcribe + Polly) vs. text simulation mode
   - Cost considerations for AWS services

3. **Local development mode?**
   - Docker Compose for local testing
   - Mock services vs. real AWS integration

### Gamification
4. **Hint system design?**
   - Progressive hints (cost increases)
   - Time-based unlocks
   - Community hints

5. **Multiplayer/competitive mode?**
   - Leaderboards
   - Team competitions
   - CTF-style events

### Safety
6. **Guardrails for the vulnerable app?**
   - Network isolation
   - No real data
   - Disclaimer/terms of use

7. **Deployment restrictions?**
   - Private subnet only?
   - VPN-gated access?
   - Time-limited instances?

---

## Next Steps

1. **Finalize attack scenarios** - Confirm which attacks to prioritize
2. **Design architecture** - AWS-first with IaC
3. **Create MVP** - Start with 2-3 personas covering different OWASP categories
4. **Add gamification** - Flag system and scoreboard
5. **Documentation** - Attack guides and solutions

---

## Planned Features

### Ollama Integration (Local LLM)
Add support for running VoiceGoat with local LLMs via Ollama for completely free testing:
- No API costs
- Fully offline operation
- Support for models like Llama 3, Mistral, Phi-3
- Configuration: `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=llama3`

### Additional Voice Agent Personas
- **VoiceMed** (LLM02/LLM09) - Healthcare assistant with sensitive data
- **VoiceCode** (LLM03/LLM05) - Code assistant with supply chain risks
- **VoiceShop** (LLM04/LLM10) - E-commerce with data poisoning

### Speech-to-Speech Mode
- Real-time voice interaction using AWS Transcribe + Polly
- Multimodal injection testing (audio-based attacks)

---

## References

- [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/)
- [AWS LLM Security Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-security/owasp-top-ten.html)
- [MITRE ATLAS](https://atlas.mitre.org/)
- [OWASP WebGoat](https://owasp.org/www-project-webgoat/) (Inspiration)
