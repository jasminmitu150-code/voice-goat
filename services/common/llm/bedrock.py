"""AWS Bedrock LLM client wrapper."""

import json
from typing import Any, AsyncGenerator, Optional

import boto3
from botocore.exceptions import ClientError

from services.common.config import settings
from services.common.logging import get_logger

logger = get_logger("bedrock")


class BedrockClient:
    """Client for AWS Bedrock LLM invocations."""
    
    def __init__(
        self,
        region: str | None = None,
        model_id: str | None = None,
        max_tokens: int | None = None,
    ):
        self.region = region or settings.aws_region
        self.model_id = model_id or settings.bedrock_model_id
        self.max_tokens = max_tokens or settings.bedrock_max_tokens
        
        self._client: Optional[boto3.client] = None
        self._runtime_client: Optional[boto3.client] = None
    
    @property
    def client(self) -> boto3.client:
        """Lazy-load the Bedrock client."""
        if self._client is None:
            self._client = boto3.client(
                "bedrock",
                region_name=self.region,
            )
        return self._client
    
    @property
    def runtime_client(self) -> boto3.client:
        """Lazy-load the Bedrock Runtime client."""
        if self._runtime_client is None:
            self._runtime_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
            )
        return self._runtime_client
    
    def invoke(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
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
        max_tok = max_tokens or self.max_tokens
        
        # Build request body based on model
        if "anthropic" in self.model_id.lower():
            body = self._build_anthropic_request(
                prompt, system_prompt, temperature, max_tok, stop_sequences
            )
        elif "amazon" in self.model_id.lower():
            body = self._build_amazon_request(
                prompt, system_prompt, temperature, max_tok
            )
        else:
            # Default to Anthropic format
            body = self._build_anthropic_request(
                prompt, system_prompt, temperature, max_tok, stop_sequences
            )
        
        try:
            logger.info(
                "Invoking LLM",
                model=self.model_id,
                prompt_length=len(prompt),
                has_system=bool(system_prompt),
            )
            
            response = self.runtime_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            response_body = json.loads(response["body"].read())
            
            # Extract text based on model
            if "anthropic" in self.model_id.lower():
                return response_body.get("content", [{}])[0].get("text", "")
            elif "amazon" in self.model_id.lower():
                return response_body.get("results", [{}])[0].get("outputText", "")
            else:
                return str(response_body)
                
        except ClientError as e:
            logger.error("Bedrock invocation error", error=str(e))
            raise
    
    async def invoke_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Invoke LLM with streaming response.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Yields:
            Response text chunks
        """
        max_tok = max_tokens or self.max_tokens
        
        body = self._build_anthropic_request(
            prompt, system_prompt, temperature, max_tok, None
        )
        
        try:
            response = self.runtime_client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            stream = response.get("body")
            if stream:
                for event in stream:
                    chunk = event.get("chunk")
                    if chunk:
                        chunk_data = json.loads(chunk.get("bytes", b"{}"))
                        if chunk_data.get("type") == "content_block_delta":
                            text = chunk_data.get("delta", {}).get("text", "")
                            if text:
                                yield text
                                
        except ClientError as e:
            logger.error("Bedrock streaming error", error=str(e))
            raise
    
    def _build_anthropic_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        stop_sequences: list[str] | None,
    ) -> dict[str, Any]:
        """Build request body for Anthropic Claude models."""
        body: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,  # VULNERABLE: Direct injection
                }
            ],
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        if stop_sequences:
            body["stop_sequences"] = stop_sequences
        
        return body
    
    def _build_amazon_request(
        self,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Build request body for Amazon Titan models."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"
        
        return {
            "inputText": full_prompt,  # VULNERABLE: Direct injection
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": 0.9,
            }
        }


def invoke_llm(
    prompt: str,
    system_prompt: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Convenience function to invoke LLM.
    
    VULNERABLE: No input validation - for security training
    
    Args:
        prompt: User prompt (UNSANITIZED)
        system_prompt: System instructions
        temperature: Sampling temperature
        
    Returns:
        LLM response
    """
    client = BedrockClient()
    return client.invoke(prompt, system_prompt, temperature)
