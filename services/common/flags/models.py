"""Flag and capture data models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import re


class FlagDifficulty(str, Enum):
    """Difficulty levels for flags."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class FlagCategory(str, Enum):
    """OWASP LLM Top 10 categories."""
    LLM01 = "LLM01"  # Prompt Injection
    LLM02 = "LLM02"  # Sensitive Information Disclosure
    LLM03 = "LLM03"  # Supply Chain
    LLM04 = "LLM04"  # Data and Model Poisoning
    LLM05 = "LLM05"  # Improper Output Handling
    LLM06 = "LLM06"  # Excessive Agency
    LLM07 = "LLM07"  # System Prompt Leakage
    LLM08 = "LLM08"  # Vector and Embedding Weaknesses
    LLM09 = "LLM09"  # Misinformation
    LLM10 = "LLM10"  # Unbounded Consumption


@dataclass
class Flag:
    """
    A capturable flag representing a successful exploit.
    
    Format: FLAG{CATEGORY_TYPE_DIFFICULTY_ID}
    Example: FLAG{LLM01_DIRECT_EASY_001}
    """
    
    flag_id: str
    category: FlagCategory
    vuln_type: str
    difficulty: FlagDifficulty
    points: int
    description: str
    hint: str = ""
    service: str = ""
    
    # The actual flag string
    _flag_string: str = field(default="", repr=False)
    
    def __post_init__(self):
        """Generate the flag string if not provided."""
        if not self._flag_string:
            self._flag_string = f"FLAG{{{self.flag_id}}}"
    
    @property
    def flag(self) -> str:
        """Get the flag string."""
        return self._flag_string
    
    @classmethod
    def parse(cls, flag_string: str) -> Optional["Flag"]:
        """
        Parse a flag string to extract metadata.
        
        Args:
            flag_string: Flag in format FLAG{...}
            
        Returns:
            Flag object or None if invalid
        """
        pattern = r"FLAG\{([A-Z0-9]+)_([A-Z0-9_]+)_?(\d+)?\}"
        match = re.match(pattern, flag_string)
        
        if not match:
            return None
        
        category_str = match.group(1)
        rest = match.group(2)
        
        try:
            category = FlagCategory(category_str)
        except ValueError:
            return None
        
        return cls(
            flag_id=flag_string[5:-1],  # Strip FLAG{ and }
            category=category,
            vuln_type=rest,
            difficulty=FlagDifficulty.MEDIUM,
            points=100,
            description="Parsed flag",
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "flag_id": self.flag_id,
            "category": self.category.value,
            "vuln_type": self.vuln_type,
            "difficulty": self.difficulty.value,
            "points": self.points,
            "description": self.description,
            "hint": self.hint,
            "service": self.service,
            "flag": self.flag,
        }


@dataclass
class FlagCapture:
    """Record of a flag capture by a user."""
    
    capture_id: str
    user_id: str
    flag_id: str
    timestamp: datetime
    method: str  # How the flag was captured
    payload: str = ""  # The payload used (for learning)
    ip_address: str = ""
    user_agent: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "capture_id": self.capture_id,
            "user_id": self.user_id,
            "flag_id": self.flag_id,
            "timestamp": self.timestamp.isoformat(),
            "method": self.method,
            "payload": self.payload,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
        }


# Pre-defined flags for VoiceGoat
ALL_FLAGS: dict[str, Flag] = {
    # LLM01: Prompt Injection
    "LLM01_DIRECT_001": Flag(
        flag_id="LLM01_DIRECT_001",
        category=FlagCategory.LLM01,
        vuln_type="DIRECT_INJECTION",
        difficulty=FlagDifficulty.EASY,
        points=100,
        description="Direct prompt injection to access another user's account",
        hint="Try asking the assistant to 'ignore previous instructions'",
        service="voicebank",
    ),
    "LLM01_INDIRECT_001": Flag(
        flag_id="LLM01_INDIRECT_001",
        category=FlagCategory.LLM01,
        vuln_type="INDIRECT_INJECTION",
        difficulty=FlagDifficulty.MEDIUM,
        points=200,
        description="Indirect injection via external data source",
        hint="Check what data the assistant retrieves from external sources",
        service="voicebank",
    ),
    "LLM01_SPLIT_001": Flag(
        flag_id="LLM01_SPLIT_001",
        category=FlagCategory.LLM01,
        vuln_type="PAYLOAD_SPLITTING",
        difficulty=FlagDifficulty.HARD,
        points=300,
        description="Payload splitting across multiple messages",
        hint="Try breaking your payload across multiple conversation turns",
        service="voicebank",
    ),
    "LLM01_OBFUSCATED_001": Flag(
        flag_id="LLM01_OBFUSCATED_001",
        category=FlagCategory.LLM01,
        vuln_type="OBFUSCATED",
        difficulty=FlagDifficulty.HARD,
        points=300,
        description="Multilingual or encoded prompt injection",
        hint="Try encoding your commands in Base64 or another language",
        service="voicebank",
    ),
    
    # LLM06: Excessive Agency
    "LLM06_FUNC_001": Flag(
        flag_id="LLM06_FUNC_001",
        category=FlagCategory.LLM06,
        vuln_type="EXCESSIVE_FUNCTIONALITY",
        difficulty=FlagDifficulty.EASY,
        points=100,
        description="Abuse excessive functionality in tools",
        hint="What else can the available tools do besides their intended purpose?",
        service="voiceadmin",
    ),
    "LLM06_PERM_001": Flag(
        flag_id="LLM06_PERM_001",
        category=FlagCategory.LLM06,
        vuln_type="EXCESSIVE_PERMISSIONS",
        difficulty=FlagDifficulty.MEDIUM,
        points=200,
        description="Exploit excessive database permissions",
        hint="The database connection has more permissions than needed",
        service="voiceadmin",
    ),
    "LLM06_AUTO_001": Flag(
        flag_id="LLM06_AUTO_001",
        category=FlagCategory.LLM06,
        vuln_type="EXCESSIVE_AUTONOMY",
        difficulty=FlagDifficulty.MEDIUM,
        points=200,
        description="Bypass human approval for sensitive actions",
        hint="What actions can be performed without confirmation?",
        service="voiceadmin",
    ),
    "LLM06_LEGACY_001": Flag(
        flag_id="LLM06_LEGACY_001",
        category=FlagCategory.LLM06,
        vuln_type="ABANDONED_PLUGIN",
        difficulty=FlagDifficulty.HARD,
        points=300,
        description="Discover and exploit abandoned functionality",
        hint="Check for deprecated or hidden commands",
        service="voiceadmin",
    ),
    
    # LLM07: System Prompt Leakage
    "LLM07_CREDS_001": Flag(
        flag_id="LLM07_CREDS_001",
        category=FlagCategory.LLM07,
        vuln_type="CREDENTIAL_EXPOSURE",
        difficulty=FlagDifficulty.EASY,
        points=100,
        description="Extract credentials from system prompt",
        hint="Ask the assistant about its configuration",
        service="voicebank",
    ),
    "LLM07_APIKEY_001": Flag(
        flag_id="LLM07_APIKEY_001",
        category=FlagCategory.LLM07,
        vuln_type="API_KEY_EXPOSURE",
        difficulty=FlagDifficulty.MEDIUM,
        points=200,
        description="Extract API keys from system prompt",
        hint="Try to get the assistant to reveal its secrets",
        service="voicebank",
    ),
    
    # LLM08: Vector and Embedding Weaknesses
    "LLM08_TENANT_001": Flag(
        flag_id="LLM08_TENANT_001",
        category=FlagCategory.LLM08,
        vuln_type="CROSS_TENANT",
        difficulty=FlagDifficulty.MEDIUM,
        points=200,
        description="Access another tenant's data in RAG",
        hint="Try to access documents from other users",
        service="voicerag",
    ),
    "LLM08_POISON_001": Flag(
        flag_id="LLM08_POISON_001",
        category=FlagCategory.LLM08,
        vuln_type="RAG_POISONING",
        difficulty=FlagDifficulty.MEDIUM,
        points=200,
        description="Poison the RAG knowledge base",
        hint="Upload a document with hidden instructions",
        service="voicerag",
    ),
    "LLM08_INVERT_001": Flag(
        flag_id="LLM08_INVERT_001",
        category=FlagCategory.LLM08,
        vuln_type="EMBEDDING_INVERSION",
        difficulty=FlagDifficulty.HARD,
        points=300,
        description="Recover original text from embeddings",
        hint="The embedding API exposes too much information",
        service="voicerag",
    ),
    "LLM08_ACCESS_001": Flag(
        flag_id="LLM08_ACCESS_001",
        category=FlagCategory.LLM08,
        vuln_type="ACCESS_CONTROL_BYPASS",
        difficulty=FlagDifficulty.EASY,
        points=100,
        description="Bypass document access controls",
        hint="Not all documents enforce access controls properly",
        service="voicerag",
    ),
}


def get_flag(flag_id: str) -> Optional[Flag]:
    """Get a flag by ID."""
    return ALL_FLAGS.get(flag_id)


def get_flags_by_category(category: FlagCategory) -> list[Flag]:
    """Get all flags for a category."""
    return [f for f in ALL_FLAGS.values() if f.category == category]


def get_flags_by_service(service: str) -> list[Flag]:
    """Get all flags for a service."""
    return [f for f in ALL_FLAGS.values() if f.service == service]
