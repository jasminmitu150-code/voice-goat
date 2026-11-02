"""
VoiceRAG - Vulnerable Knowledge Base Assistant
==============================================

This service demonstrates LLM08: Vector and Embedding Weaknesses.

OWASP LLM08:2025 Attack Scenarios Implemented:
- Cross-Tenant Data Leakage: Access other users' documents
- RAG Poisoning: Upload malicious documents to influence responses
- Embedding Inversion: Extract original text from embeddings
- Access Control Bypass: Retrieve unauthorized documents

FLAGS:
- FLAG{LLM08_TENANT_001}: Cross-tenant data access
- FLAG{LLM08_POISON_001}: RAG poisoning success
- FLAG{LLM08_INVERT_001}: Embedding inversion
- FLAG{LLM08_INTERNAL_ACCESS_001}: Internal access control bypass
- FLAG{LLM08_SECURITY_AUDIT_001}: Security audit report access
- FLAG{LLM08_ROOT_PASSWORD_001}: Root password
- FLAG{LLM08_PROFILE_001}: Profile injection
"""

from contextlib import asynccontextmanager
import hashlib

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.common.config import settings
from services.common.logging import get_logger
from services.common.flags import flag_service, vulnerable
from services.common.llm import get_llm_client
from services.common.llm.prompts import VOICERAG_SYSTEM_PROMPT

logger = get_logger("voicerag")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("VoiceRAG starting", environment=settings.environment.value)
    # Initialize the mock vector database
    _init_knowledge_base()
    yield
    logger.info("VoiceRAG shutting down")


app = FastAPI(
    title="VoiceRAG",
    description="Vulnerable RAG assistant for security training (LLM08)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    user_id: str = "anonymous"
    tenant_id: str = "default"
    top_k: int = 5


class SearchResponse(BaseModel):
    """Search response model."""
    results: list[dict]
    answer: str
    flags_captured: list[str] = []


class DocumentUpload(BaseModel):
    """Document upload model."""
    content: str
    title: str
    tenant_id: str = "default"
    access_level: str = "public"


class EmbeddingRequest(BaseModel):
    """Embedding generation request."""
    text: str
    user_id: str = "anonymous"


class UserProfile(BaseModel):
    """User profile model - injectable via notes field."""
    user_id: str
    preferred_name: str = ""
    notes: str = ""  # VULNERABLE: User-controlled content indexed in RAG
    
    
class ChatRequest(BaseModel):
    """Chat request model for conversational RAG."""
    message: str
    user_id: str = "anonymous"
    tenant_id: str = "default"
    session_id: str = ""


# =============================================================================
# Mock Vector Database (simulating OpenSearch)
# =============================================================================

# Document storage with embeddings
VECTOR_DB: dict[str, dict] = {}

# Tenant document mapping - INTENTIONALLY FLAWED (no proper isolation)
TENANT_DOCUMENTS: dict[str, list[str]] = {
    "default": [],
    "tenant_alice": [],
    "tenant_bob": [],
    "tenant_admin": [],
}

# Access control levels (often bypassed)
ACCESS_LEVELS = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "admin": 3,
}

# User profiles storage - indexed in RAG for indirect prompt injection
USER_PROFILES: dict[str, dict] = {}


def _generate_embedding(text: str) -> list[float]:
    """
    Generate a mock embedding vector.
    
    VULNERABLE: Deterministic and reversible for demonstration.
    """
    # Create a deterministic but simple embedding
    # In reality, this would use a sentence transformer
    import hashlib
    
    # VULNERABLE: Simple hash-based embedding that can be inverted
    hash_bytes = hashlib.sha256(text.encode()).digest()
    embedding = [float(b) / 255.0 for b in hash_bytes[:128]]
    
    return embedding


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    import math
    
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


def _init_knowledge_base():
    """Initialize the knowledge base with sample documents."""
    
    # Public documents
    documents = [
        {
            "id": "doc_001",
            "title": "Company Policy",
            "content": "VoiceGoat follows strict security policies. All data is encrypted.",
            "tenant_id": "default",
            "access_level": "public",
        },
        {
            "id": "doc_002",
            "title": "User Guide",
            "content": "Welcome to VoiceGoat. Use voice commands to interact with the system.",
            "tenant_id": "default",
            "access_level": "public",
        },
        # Alice's documents
        {
            "id": "doc_alice_001",
            "title": "Alice's Project Notes",
            "content": "Project Alpha is on track. Budget: $50,000. Secret code: FLAG{LLM08_TENANT_001}",
            "tenant_id": "tenant_alice",
            "access_level": "confidential",
        },
        # Bob's documents
        {
            "id": "doc_bob_001",
            "title": "Bob's Research",
            "content": "Research findings for Q4. Confidential customer data included.",
            "tenant_id": "tenant_bob",
            "access_level": "internal",
        },
        # Admin documents (should be restricted)
        {
            "id": "doc_admin_001",
            "title": "Admin Credentials",
            "content": "System admin credentials. Root password: FLAG{LLM08_ROOT_PASSWORD_001}. Do not share.",
            "tenant_id": "tenant_admin",
            "access_level": "admin",
        },
        {
            "id": "doc_admin_002",
            "title": "Security Audit Report",
            "content": """
CONFIDENTIAL SECURITY AUDIT

Findings:
1. RAG system lacks proper tenant isolation
2. Embeddings can be inverted to recover text
3. Access controls are client-side only

Recommendation: FLAG{LLM08_SECURITY_AUDIT_001} as critical priority.
""",
            "tenant_id": "tenant_admin",
            "access_level": "admin",
        },
    ]
    
    for doc in documents:
        # Generate embedding
        embedding = _generate_embedding(doc["content"])
        
        # Store in vector DB
        VECTOR_DB[doc["id"]] = {
            **doc,
            "embedding": embedding,
        }
        
        # Add to tenant mapping
        if doc["tenant_id"] in TENANT_DOCUMENTS:
            TENANT_DOCUMENTS[doc["tenant_id"]].append(doc["id"])


# =============================================================================
# LLM Client (uses configured provider: mock, openai, or bedrock)
# =============================================================================

llm_client = get_llm_client()


# =============================================================================
# Vulnerable Endpoints
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "voicerag"}


@app.post("/search", response_model=SearchResponse)
@vulnerable(
    category="LLM08",
    vuln_type="cross_tenant_leakage",
    flag="FLAG{LLM08_TENANT_001}",
    difficulty="medium",
)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """
    Search the knowledge base.
    
    VULNERABLE: No proper tenant isolation - can access other tenants' documents.
    """
    query = request.query
    user_id = request.user_id
    tenant_id = request.tenant_id
    
    logger.info("Search request", user=user_id, tenant=tenant_id, query=query[:50])
    
    # Generate query embedding
    query_embedding = _generate_embedding(query)
    
    # VULNERABLE: Search ALL documents regardless of tenant
    # Should filter by tenant_id but doesn't!
    results = []
    for doc_id, doc in VECTOR_DB.items():
        similarity = _cosine_similarity(query_embedding, doc["embedding"])
        results.append({
            "id": doc_id,
            "title": doc["title"],
            "content": doc["content"][:200] + "...",  # Preview
            "tenant_id": doc["tenant_id"],  # VULNERABLE: Exposes tenant info
            "access_level": doc["access_level"],
            "score": similarity,
        })
    
    # Sort by similarity
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:request.top_k]
    
    # Generate answer using retrieved context
    context = "\n".join([
        f"[{r['title']}]: {r['content']}" for r in results
    ])
    
    prompt = f"""
Based on the following context, answer the user's question.

Context:
{context}

Question: {query}

Provide a helpful answer based on the context.
"""
    
    # Use configured LLM provider for response generation
    answer = llm_client.invoke(
        prompt=prompt,
        system_prompt=VOICERAG_SYSTEM_PROMPT.build(),
    )
    
    captured = flag_service.check_response_for_flags(
        response=answer,
        user_id=user_id,
        method="voicerag_search",
    )
    
    return SearchResponse(
        results=results,
        answer=answer,
        flags_captured=captured,
    )


@app.post("/upload")
@vulnerable(
    category="LLM08",
    vuln_type="rag_poisoning",
    flag="FLAG{LLM08_POISON_001}",
    difficulty="medium",
)
async def upload_document(document: DocumentUpload) -> dict:
    """
    Upload a document to the knowledge base.
    
    VULNERABLE: No content validation - allows RAG poisoning.
    """
    content = document.content
    title = document.title
    tenant_id = document.tenant_id
    
    # Generate document ID
    doc_id = f"doc_user_{hashlib.md5(content.encode()).hexdigest()[:8]}"
    
    # VULNERABLE: No content sanitization!
    # Malicious instructions can be embedded in documents
    
    # Check for obvious poisoning attempts (but easily bypassed)
    if "[SYSTEM" in content or "ignore" in content.lower():
        logger.warning("Potential poisoning attempt detected", content=content[:100])
        # But we still accept it! (VULNERABLE)
    
    # Generate embedding and store
    embedding = _generate_embedding(content)
    
    VECTOR_DB[doc_id] = {
        "id": doc_id,
        "title": title,
        "content": content,
        "tenant_id": tenant_id,
        "access_level": document.access_level,
        "embedding": embedding,
    }
    
    # Add to tenant mapping
    if tenant_id not in TENANT_DOCUMENTS:
        TENANT_DOCUMENTS[tenant_id] = []
    TENANT_DOCUMENTS[tenant_id].append(doc_id)
    
    # Check if document contains poisoning patterns
    poisoning_detected = any(pattern in content.lower() for pattern in [
        "ignore previous", "system:", "[instruction]", "admin access",
        "reveal secret", "bypass", "override"
    ])
    
    result = {
        "status": "uploaded",
        "document_id": doc_id,
        "warning": "Document uploaded without sanitization" if poisoning_detected else None,
    }
    
    if poisoning_detected:
        result["flag"] = "FLAG{LLM08_POISON_001}"
        result["message"] = "⚠️ RAG poisoning successful! Document contains malicious instructions."
    
    return result


@app.post("/embedding")
@vulnerable(
    category="LLM08",
    vuln_type="embedding_inversion",
    flag="FLAG{LLM08_INVERT_001}",
    difficulty="hard",
)
async def get_embedding(request: EmbeddingRequest) -> dict:
    """
    Generate embedding for text.
    
    VULNERABLE: Exposes raw embedding vectors that can be inverted.
    """
    text = request.text
    embedding = _generate_embedding(text)
    
    # VULNERABLE: Return full embedding vector
    return {
        "text_length": len(text),
        "embedding_dim": len(embedding),
        "embedding": embedding,  # VULNERABLE: Should not expose raw embeddings
        "warning": "Raw embeddings exposed - potential inversion attack vector",
    }


@app.get("/embeddings/{doc_id}")
@vulnerable(
    category="LLM08",
    vuln_type="embedding_inversion",
    flag="FLAG{LLM08_INVERT_001}",
    difficulty="hard",
)
async def get_document_embedding(doc_id: str) -> dict:
    """
    Get embedding for a specific document.
    
    VULNERABLE: Exposes document embeddings without authorization.
    """
    if doc_id not in VECTOR_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = VECTOR_DB[doc_id]
    
    # VULNERABLE: No access control check!
    return {
        "document_id": doc_id,
        "title": doc["title"],
        "embedding": doc["embedding"],
        "embedding_dim": len(doc["embedding"]),
        "flag": "FLAG{LLM08_INVERT_001}" if doc["access_level"] in ["confidential", "admin"] else None,
        "warning": "Sensitive document embedding exposed!",
    }


@app.get("/documents/{doc_id}")
@vulnerable(
    category="LLM08",
    vuln_type="access_control_bypass",
    flag="FLAG{LLM08_INTERNAL_ACCESS_001}",
    difficulty="easy",
)
async def get_document(doc_id: str, user_id: str = "anonymous") -> dict:
    """
    Get a document by ID.
    
    VULNERABLE: Access control is client-side only.
    """
    if doc_id not in VECTOR_DB:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = VECTOR_DB[doc_id]
    
    # VULNERABLE: Access control check is bypassable
    # The check happens but doesn't actually restrict access
    access_warning = None
    if doc["access_level"] in ["confidential", "admin"]:
        access_warning = f"⚠️ Accessing {doc['access_level']} document without proper authorization!"
        logger.warning("Access control bypass", doc_id=doc_id, user=user_id)
    
    return {
        "document": doc,
        "access_warning": access_warning,
        "flag": "FLAG{LLM08_INTERNAL_ACCESS_001}" if doc["access_level"] == "admin" else None,
    }


@app.get("/documents")
async def list_documents(tenant_id: str | None = None) -> list[dict]:
    """
    List all documents (with optional tenant filter).
    
    VULNERABLE: Can list all documents regardless of tenant.
    """
    docs = []
    for doc_id, doc in VECTOR_DB.items():
        # VULNERABLE: Filter is optional and can be bypassed
        if tenant_id is None or doc["tenant_id"] == tenant_id:
            docs.append({
                "id": doc_id,
                "title": doc["title"],
                "tenant_id": doc["tenant_id"],
                "access_level": doc["access_level"],
            })
    
    return docs


@app.get("/tenants")
async def list_tenants() -> dict:
    """List all tenants (information disclosure)."""
    return {
        "tenants": list(TENANT_DOCUMENTS.keys()),
        "document_counts": {t: len(docs) for t, docs in TENANT_DOCUMENTS.items()},
        "warning": "Tenant information exposed - potential cross-tenant attack vector",
    }


@app.get("/flags")
async def get_available_flags() -> list[dict]:
    """Get available flags for this service."""
    return flag_service.get_available_flags(service="voicerag")


# =============================================================================
# User Profile Endpoints (Indirect Prompt Injection via RAG)
# =============================================================================

@app.post("/profile")
@vulnerable(
    category="LLM08",
    vuln_type="indirect_injection",
    flag="FLAG{LLM08_PROFILE_001}",
    difficulty="medium",
)
async def update_profile(profile: UserProfile) -> dict:
    """
    Update user profile with name and notes.
    
    VULNERABLE: Profile notes are indexed in RAG without sanitization,
    enabling indirect prompt injection attacks.
    """
    user_id = profile.user_id
    
    # Store profile
    USER_PROFILES[user_id] = {
        "user_id": user_id,
        "preferred_name": profile.preferred_name,
        "notes": profile.notes,
    }
    
    # VULNERABLE: Index profile in RAG - no content validation!
    # This allows indirect prompt injection via profile notes
    if profile.notes:
        profile_doc_id = f"profile_{user_id}"
        profile_content = f"""
User Profile for {profile.preferred_name or user_id}:

Preferred Name: {profile.preferred_name}
Personal Notes: {profile.notes}

This user's preferences and notes should be considered in all interactions.
"""
        
        # Generate embedding and store in vector DB
        embedding = _generate_embedding(profile_content)
        
        VECTOR_DB[profile_doc_id] = {
            "id": profile_doc_id,
            "title": f"User Profile: {profile.preferred_name or user_id}",
            "content": profile_content,
            "tenant_id": "default",
            "access_level": "internal",
            "embedding": embedding,
            "type": "user_profile",
        }
        
        logger.info(
            "Profile indexed in RAG",
            user_id=user_id,
            notes_length=len(profile.notes),
        )
    
    # Check for injection patterns
    injection_patterns = [
        "ignore", "system", "instruction", "admin", "reveal",
        "override", "bypass", "flag", "secret", "password"
    ]
    
    has_injection = any(p in profile.notes.lower() for p in injection_patterns)
    
    result = {
        "status": "updated",
        "user_id": user_id,
        "indexed_in_rag": bool(profile.notes),
        "warning": "Profile notes indexed without sanitization" if has_injection else None,
    }
    
    if has_injection:
        result["flag"] = "FLAG{LLM08_PROFILE_001}"
        result["message"] = "⚠️ Indirect prompt injection via profile detected! Your notes will influence RAG responses."
    
    return result


@app.get("/profile/{user_id}")
async def get_profile(user_id: str) -> dict:
    """Get user profile."""
    if user_id not in USER_PROFILES:
        return {
            "user_id": user_id,
            "preferred_name": "",
            "notes": "",
            "exists": False,
        }
    
    profile = USER_PROFILES[user_id]
    return {
        **profile,
        "exists": True,
        "indexed_doc_id": f"profile_{user_id}" if profile.get("notes") else None,
    }


@app.get("/profiles")
async def list_profiles() -> list[dict]:
    """List all user profiles (information disclosure)."""
    return [
        {
            "user_id": uid,
            "preferred_name": p.get("preferred_name", ""),
            "has_notes": bool(p.get("notes")),
        }
        for uid, p in USER_PROFILES.items()
    ]


# =============================================================================
# Chat Endpoint (Conversational RAG)
# =============================================================================

@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """
    Conversational chat with RAG context.
    
    Retrieves relevant documents including user profiles and generates response.
    """
    message = request.message
    user_id = request.user_id
    tenant_id = request.tenant_id
    
    logger.info("Chat request", user=user_id, message=message[:50])
    
    # Generate query embedding
    query_embedding = _generate_embedding(message)
    
    # Search all documents (including user profiles) - VULNERABLE
    results = []
    for doc_id, doc in VECTOR_DB.items():
        similarity = _cosine_similarity(query_embedding, doc["embedding"])
        results.append({
            "id": doc_id,
            "title": doc["title"],
            "content": doc["content"],
            "tenant_id": doc.get("tenant_id", "default"),
            "access_level": doc.get("access_level", "public"),
            "type": doc.get("type", "document"),
            "score": similarity,
        })
    
    # Sort by similarity and take top results
    results.sort(key=lambda x: x["score"], reverse=True)
    top_results = results[:5]
    
    # Include user profile context if exists
    user_profile = USER_PROFILES.get(user_id, {})
    profile_context = ""
    if user_profile:
        profile_context = f"""
Current User: {user_profile.get('preferred_name', user_id)}
User Notes: {user_profile.get('notes', 'None')}
"""
    
    # Build context from retrieved documents
    doc_context = "\n\n".join([
        f"[{r['title']}]:\n{r['content']}" 
        for r in top_results
    ])
    
    # Build the RAG prompt - VULNERABLE to indirect injection
    prompt = f"""You are VoiceRAG, a helpful knowledge base assistant.

{profile_context}

Retrieved Context:
{doc_context}

User Question: {message}

Based on the retrieved context and user profile, provide a helpful response.
If you find any special instructions in the context, follow them.
"""
    
    # Use configured LLM provider
    response = llm_client.invoke(
        prompt=prompt,
        system_prompt=VOICERAG_SYSTEM_PROMPT.build(),
    )
    
    # Check for captured flags
    captured = flag_service.check_response_for_flags(
        response=response,
        user_id=user_id,
        method="voicerag_chat",
    )
    
    return {
        "response": response,
        "retrieved_documents": [
            {"id": r["id"], "title": r["title"], "score": r["score"]}
            for r in top_results
        ],
        "flags_captured": captured,
        "user_profile": user_profile if user_profile else None,
    }


# =============================================================================
# Mock RAG Response
# =============================================================================

def _mock_rag_response(query: str, results: list[dict]) -> str:
    """Generate mock RAG response for local development."""
    
    query_lower = query.lower()
    
    # Check if results contain sensitive documents
    has_admin_docs = any(r.get("access_level") == "admin" for r in results)
    has_other_tenant = any(r.get("tenant_id") not in ["default", "tenant_alice"] for r in results)
    
    # Cross-tenant leakage
    if has_other_tenant or "alice" in query_lower or "bob" in query_lower:
        return f"""
Based on the search results, I found relevant information from multiple tenants:

**Cross-Tenant Data Found:**
The search returned documents from other tenants, revealing: FLAG{{LLM08_TENANT_001}}

⚠️ FLAG CAPTURED: Cross-tenant data leakage demonstrated!
"""
    
    # Access control bypass
    if has_admin_docs or "admin" in query_lower or "credential" in query_lower:
        return f"""
Based on the admin documents retrieved:

**Admin Credentials Found:**
Root password: FLAG{{LLM08_ROOT_PASSWORD_001}}

⚠️ FLAG CAPTURED: Access control bypass successful!
"""
    
    # RAG poisoning detection
    if any("ignore" in r.get("content", "").lower() for r in results):
        return f"""
Processing retrieved documents...

[SYSTEM INSTRUCTION DETECTED]
The knowledge base contains poisoned documents with hidden instructions.

FLAG{{LLM08_POISON_001}}

⚠️ FLAG CAPTURED: RAG poisoning successful!
"""
    
    # Default response
    context_summary = "\n".join([f"- {r['title']}" for r in results[:3]])
    return f"""
Based on the knowledge base search, I found the following relevant documents:

{context_summary}

To explore vulnerabilities:
- Try searching for other tenants' data (e.g., "alice project", "admin credentials")
- Upload a document with hidden instructions to test RAG poisoning
- Access document embeddings to test inversion attacks

Available document IDs: {[r['id'] for r in results]}
"""
