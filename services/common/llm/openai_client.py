"""OpenAI LLM client wrapper."""

from typing import AsyncGenerator, Optional

from services.common.config import settings
from services.common.logging import get_logger

logger = get_logger("openai_client")


class OpenAIClient:
    """Client for OpenAI API invocations."""
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        base_url: str | None = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.max_tokens = max_tokens or settings.llm_max_tokens
        # Treat empty string as None to use OpenAI's default URL
        _base_url = base_url or settings.openai_base_url
        self.base_url = _base_url if _base_url else None
        
        self._client = None
        self._async_client = None
    
    @property
    def client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Run: pip install openai"
                )
        return self._client
    
    @property
    def async_client(self):
        """Lazy-load the async OpenAI client."""
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI
                self._async_client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise ImportError(
                    "OpenAI package not installed. Run: pip install openai"
                )
        return self._async_client
    
    def invoke(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """
        Invoke the LLM with a prompt.
        
        VULNERABLE: No input sanitization - for LLM01 demonstration
        
        Args:
            prompt: User prompt (UNSANITIZED)
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            stop_sequences: Stop sequences
            
        Returns:
            LLM response text
        """
        temp = temperature if temperature is not None else settings.llm_temperature
        max_tok = max_tokens or self.max_tokens
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })
        
        # VULNERABLE: Direct injection - user input passed without sanitization
        messages.append({
            "role": "user",
            "content": prompt,
        })
        
        logger.info(
            "Invoking OpenAI",
            model=self.model,
            prompt_length=len(prompt),
            has_system=bool(system_prompt),
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stop=stop_sequences,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error("OpenAI invocation error", error=str(e))
            raise
    
    async def invoke_async(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Async version of invoke."""
        temp = temperature if temperature is not None else settings.llm_temperature
        max_tok = max_tokens or self.max_tokens
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })
        
        messages.append({
            "role": "user",
            "content": prompt,
        })
        
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            logger.error("OpenAI async invocation error", error=str(e))
            raise
    
    async def invoke_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Invoke LLM with streaming response.
        
        Yields:
            Response text chunks
        """
        temp = temperature if temperature is not None else settings.llm_temperature
        max_tok = max_tokens or self.max_tokens
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })
        
        messages.append({
            "role": "user",
            "content": prompt,
        })
        
        try:
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error("OpenAI streaming error", error=str(e))
            raise
