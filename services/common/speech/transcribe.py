"""AWS Transcribe wrapper for Speech-to-Text."""

import asyncio
from typing import AsyncGenerator, Optional

import boto3
from botocore.exceptions import ClientError

from services.common.config import settings
from services.common.logging import get_logger

logger = get_logger("transcribe")


class TranscribeClient:
    """Client for AWS Transcribe speech-to-text service."""
    
    def __init__(
        self,
        region: str | None = None,
        language_code: str | None = None,
        sample_rate: int | None = None,
    ):
        self.region = region or settings.aws_region
        self.language_code = language_code or settings.transcribe_language_code
        self.sample_rate = sample_rate or settings.transcribe_sample_rate
        
        self._client: Optional[boto3.client] = None
    
    @property
    def client(self) -> boto3.client:
        """Lazy-load the Transcribe client."""
        if self._client is None:
            self._client = boto3.client(
                "transcribe",
                region_name=self.region,
            )
        return self._client
    
    async def transcribe_audio_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[str, None]:
        """
        Transcribe audio stream in real-time.
        
        Args:
            audio_stream: Async generator yielding audio chunks
            
        Yields:
            Transcribed text segments
        """
        if not settings.is_speech_enabled:
            logger.warning("Speech mode disabled, returning mock transcription")
            yield "[MOCK] Speech-to-text disabled"
            return
        
        # For streaming transcription, we'd use amazon-transcribe library
        # This is a simplified implementation
        try:
            from amazon_transcribe.client import TranscribeStreamingClient
            from amazon_transcribe.handlers import TranscriptResultStreamHandler
            from amazon_transcribe.model import TranscriptEvent
            
            client = TranscribeStreamingClient(region=self.region)
            
            stream = await client.start_stream_transcription(
                language_code=self.language_code,
                media_sample_rate_hz=self.sample_rate,
                media_encoding="pcm",
            )
            
            async def audio_generator():
                async for chunk in audio_stream:
                    yield chunk
            
            handler = TranscriptResultStreamHandler(stream.output_stream)
            
            await asyncio.gather(
                stream.input_stream.send_audio_event(audio_stream=audio_generator()),
                handler.handle_events(),
            )
            
            for result in handler.transcript_result_stream:
                if isinstance(result, TranscriptEvent):
                    for transcript in result.transcript.results:
                        if not transcript.is_partial:
                            for alt in transcript.alternatives:
                                yield alt.transcript
                                
        except ImportError:
            logger.warning("amazon-transcribe not installed, using mock")
            yield "[MOCK] Install amazon-transcribe for real STT"
        except ClientError as e:
            logger.error("Transcribe error", error=str(e))
            raise
    
    def transcribe_file(self, audio_path: str) -> str:
        """
        Transcribe an audio file (batch mode).
        
        Args:
            audio_path: S3 URI or local path to audio file
            
        Returns:
            Transcribed text
        """
        if not settings.is_speech_enabled:
            return "[MOCK] Speech-to-text disabled"
        
        import uuid
        job_name = f"voicegoat-{uuid.uuid4().hex[:8]}"
        
        try:
            self.client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={"MediaFileUri": audio_path},
                MediaFormat="wav",
                LanguageCode=self.language_code,
            )
            
            # Wait for job completion
            while True:
                status = self.client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
                
                if job_status == "COMPLETED":
                    # Get transcript
                    transcript_uri = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                    # Fetch and parse transcript
                    import httpx
                    response = httpx.get(transcript_uri)
                    return response.json()["results"]["transcripts"][0]["transcript"]
                    
                elif job_status == "FAILED":
                    raise Exception(f"Transcription failed: {status}")
                    
                asyncio.sleep(1)
                
        except ClientError as e:
            logger.error("Transcribe job error", error=str(e))
            raise


async def transcribe_audio(audio_data: bytes) -> str:
    """
    Convenience function to transcribe audio bytes.
    
    Args:
        audio_data: Raw audio bytes (PCM)
        
    Returns:
        Transcribed text
    """
    if not settings.is_speech_enabled:
        return "[MOCK] Speech-to-text disabled"
    
    client = TranscribeClient()
    
    async def audio_gen():
        yield audio_data
    
    result = []
    async for text in client.transcribe_audio_stream(audio_gen()):
        result.append(text)
    
    return " ".join(result)
