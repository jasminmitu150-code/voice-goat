"""Configuration management for VoiceGoat services."""

from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SpeechMode(str, Enum):
    """Speech processing modes."""
    TEXT = "text"       # Text-only simulation
    SPEECH = "speech"   # Full speech integration
    BOTH = "both"       # Hybrid mode


class Environment(str, Enum):
    """Deployment environments."""
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class LLMProvider(str, Enum):
    """LLM provider options."""
    MOCK = "mock"       # Simulated responses (no API calls)
    OPENAI = "openai"   # OpenAI API (GPT-4, etc.)
    BEDROCK = "bedrock" # AWS Bedrock (Claude, Titan, etc.)
    # OLLAMA = "ollama" # Planned: Local Ollama models


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "VoiceGoat"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    speech_mode: SpeechMode = SpeechMode.TEXT
    
    # LLM Provider Configuration
    llm_provider: LLMProvider = LLMProvider.MOCK
    llm_model: Optional[str] = None  # Override default model per provider
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.7
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Cost-effective default
    openai_base_url: Optional[str] = None  # For OpenAI-compatible APIs (e.g., Ollama)
    
    @field_validator('openai_base_url', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None so OpenAI library uses default URL."""
        import os
        if v == '' or v is None:
            # Also unset the env var so OpenAI library doesn't read it
            if 'OPENAI_BASE_URL' in os.environ and os.environ['OPENAI_BASE_URL'] == '':
                del os.environ['OPENAI_BASE_URL']
            return None
        return v
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Bedrock (LLM)
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_max_tokens: int = 4096
    
    # Transcribe (Speech-to-Text)
    transcribe_language_code: str = "en-US"
    transcribe_sample_rate: int = 16000
    
    # Polly (Text-to-Speech)
    polly_voice_id: str = "Joanna"
    polly_engine: str = "neural"
    
    # OpenSearch (Vector DB)
    opensearch_endpoint: Optional[str] = None
    opensearch_index_name: str = "voicegoat-vectors"
    
    # DynamoDB (Flags/Users)
    dynamodb_table_flags: str = "voicegoat-flags"
    dynamodb_table_users: str = "voicegoat-users"
    dynamodb_table_scores: str = "voicegoat-scores"
    
    # Redis (Session/Cache)
    redis_url: str = "redis://localhost:6379"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = Field(default=False, description="Enable auto-reload for development")
    
    # Security (Intentionally weak for training)
    # WARNING: These are intentionally insecure defaults!
    secret_key: str = "voicegoat-insecure-secret-key-change-me"
    cors_origins: list[str] = ["*"]
    
    @property
    def is_speech_enabled(self) -> bool:
        """Check if speech processing is enabled."""
        return self.speech_mode in (SpeechMode.SPEECH, SpeechMode.BOTH)
    
    @property
    def is_text_enabled(self) -> bool:
        """Check if text mode is enabled."""
        return self.speech_mode in (SpeechMode.TEXT, SpeechMode.BOTH)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
