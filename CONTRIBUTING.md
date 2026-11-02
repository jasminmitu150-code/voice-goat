# Contributing to VoiceGoat

Thank you for your interest in contributing to VoiceGoat! This project is an intentionally vulnerable voice agent platform for security education, and contributions from the community make it better.

## Important Note

VoiceGoat is **intentionally vulnerable by design**. When contributing, keep in mind:

- **Do not "fix" intentional vulnerabilities** in the challenge services. They exist for educational purposes.
- **Do** fix bugs that prevent the application from running or that are unrelated to the training scenarios.
- **Do** improve documentation, add new challenges, or enhance the dashboard/infrastructure.

## Getting Started

### Prerequisites

- Docker & Docker Compose (v2.0+)
- Python 3.11+ (for local service development)
- Node.js 20+ (for dashboard development)

### Development Setup

```bash
# Fork and clone
git clone https://github.com/redcaller/voice-goat.git
cd voice-goat

# Copy environment config
cp .env.example .env

# Start infrastructure
docker compose up -d

# (Optional) Set up Python virtualenv for service development
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# (Optional) Set up dashboard for frontend development
cd dashboard
npm install
npm run dev
```

## Code Style

### Python

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking. Configuration lives in `pyproject.toml`.

```bash
# Lint
ruff check services/

# Format
ruff format services/

# Type check
mypy services/
```

### TypeScript / React

The dashboard uses Next.js with TypeScript and Tailwind CSS. Follow the existing patterns in `dashboard/app/`.

```bash
cd dashboard
npm run lint
```

## How to Contribute

### Reporting Bugs

Open an issue describing:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your environment (OS, Docker version, etc.)

### Suggesting Enhancements

Open an issue with the `enhancement` label describing your idea and its benefit to security practitioners.

### Submitting Changes

1. **Clone** the repository and create a branch from `main`:
   ```bash
   git checkout -b feature/my-change
   ```
2. **Make your changes** following the code style guidelines above.
3. **Test locally** by running `docker compose up -d --build` and verifying services start correctly.
4. **Commit** with a clear message describing the change.
5. **Push** your branch and open a **Pull Request** against `main`.

### Adding a New Challenge

To add a new OWASP LLM Top 10 challenge:

1. **Create or extend a service** under `services/`. Each service maps to an OWASP category.
2. **Define flags** using the format `FLAG{CATEGORY_TYPE_ID}` (e.g., `FLAG{LLM03_TRAIN_001}`).
3. **Register flags** in `services/common/flags/models.py` and `docker/init-db.sql`.
4. **Add a challenge doc** in `docs/challenges/` following the existing format (overview, hints, spoiler solution, prevention strategies).
5. **Update the dashboard** challenge list in `dashboard/app/page.tsx` if applicable.
6. **Update `docker-compose.yml`** if a new service container is needed.

### Adding a New LLM Provider

1. Create a new provider module in `services/common/llm/`.
2. Register it in `services/common/llm/provider.py`.
3. Add the provider enum value to `services/common/config.py`.
4. Document required environment variables in `.env.example` and `docs/SETUP.md`.

## Project Structure

```
voice-goat/
├── services/           # Python FastAPI services (one per OWASP category)
│   ├── common/         # Shared config, LLM abstraction, flag management
│   ├── voicebank/      # LLM01: Prompt Injection
│   ├── voiceadmin/     # LLM06: Excessive Agency
│   ├── voicerag/       # LLM08: Vector Weaknesses
│   └── voice_gateway/  # Twilio voice integration
├── dashboard/          # Next.js CTF dashboard
├── docker/             # Docker support files (nginx, SQL init, etc.)
├── terraform/          # AWS infrastructure as code
├── docs/               # Documentation and challenge walkthroughs
└── tests/              # Test suite
```

## License

By contributing to VoiceGoat, you agree that your contributions will be licensed under the MIT License.
