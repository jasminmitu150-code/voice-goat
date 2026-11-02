"""AWS Polly wrapper for Text-to-Speech."""

from typing import Optional
import io

import boto3
from botocore.exceptions import ClientError

from services.common.config import settings
from services.common.logging import get_logger

logger = get_logger("polly")


class PollyClient:
    """Client for AWS Polly text-to-speech service."""
    
    def __init__(
        self,
        region: str | None = None,
        voice_id: str | None = None,
        engine: str | None = None,
    ):
        self.region = region or settings.aws_region
        self.voice_id = voice_id or settings.polly_voice_id
        self.engine = engine or settings.polly_engine
        
        self._client: Optional[boto3.client] = None
    
    @property
    def client(self) -> boto3.client:
        """Lazy-load the Polly client."""
        if self._client is None:
            self._client = boto3.client(
                "polly",
                region_name=self.region,
            )
        return self._client
    
    def synthesize(
        self,
        text: str,
        output_format: str = "mp3",
        voice_id: str | None = None,
        engine: str | None = None,
    ) -> bytes:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            output_format: Audio format (mp3, ogg_vorbis, pcm)
            voice_id: Override default voice
            engine: Override default engine (standard, neural)
            
        Returns:
            Audio bytes
        """
        if not settings.is_speech_enabled:
            logger.warning("Speech mode disabled, returning empty audio")
            return b""
        
        voice = voice_id or self.voice_id
        eng = engine or self.engine
        
        try:
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice,
                Engine=eng,
            )
            
            # Read audio stream
            audio_stream = response.get("AudioStream")
            if audio_stream:
                return audio_stream.read()
            return b""
            
        except ClientError as e:
            logger.error("Polly synthesis error", error=str(e))
            raise
    
    def synthesize_ssml(
        self,
        ssml: str,
        output_format: str = "mp3",
    ) -> bytes:
        """
        Synthesize speech from SSML markup.
        
        Args:
            ssml: SSML-formatted text
            output_format: Audio format
            
        Returns:
            Audio bytes
        """
        if not settings.is_speech_enabled:
            return b""
        
        try:
            response = self.client.synthesize_speech(
                Text=ssml,
                TextType="ssml",
                OutputFormat=output_format,
                VoiceId=self.voice_id,
                Engine=self.engine,
            )
            
            audio_stream = response.get("AudioStream")
            if audio_stream:
                return audio_stream.read()
            return b""
            
        except ClientError as e:
            logger.error("Polly SSML synthesis error", error=str(e))
            raise
    
    def list_voices(self, language_code: str = "en-US") -> list[dict]:
        """List available voices for a language."""
        try:
            response = self.client.describe_voices(LanguageCode=language_code)
            return response.get("Voices", [])
        except ClientError as e:
            logger.error("Polly list voices error", error=str(e))
            return []


def synthesize_speech(text: str, output_format: str = "mp3") -> bytes:
    """
    Convenience function to synthesize speech.
    
    Args:
        text: Text to convert to speech
        output_format: Audio format
        
    Returns:
        Audio bytes
    """
    client = PollyClient()
    return client.synthesize(text, output_format)
