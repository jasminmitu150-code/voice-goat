"""
Audio Processing - Speech-to-Text and Text-to-Speech
====================================================

Handles audio conversion for the voice gateway:
- STT: OpenAI Whisper or AWS Transcribe
- TTS: OpenAI TTS or AWS Polly

Audio Formats:
- Twilio sends/receives: μ-law (PCMU) 8kHz mono
- OpenAI Whisper accepts: WAV, MP3, M4A, etc.
- OpenAI TTS outputs: MP3, WAV, etc.
"""

import asyncio
import base64
import io
import struct
import wave
import audioop
from typing import Optional

from services.common.config import settings
from services.common.logging import get_logger

logger = get_logger("audio-processor")


class AudioProcessor:
    """
    Handles audio conversion between Twilio and AI services.
    """
    
    def __init__(
        self,
        stt_provider: str = "openai",  # "openai" or "transcribe"
        tts_provider: str = "openai",  # "openai" or "polly"
    ):
        self.stt_provider = stt_provider
        self.tts_provider = tts_provider
        
        self._openai_client = None
    
    @property
    def openai_client(self):
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
        return self._openai_client
    
    async def speech_to_text(self, pcm_audio: bytes, sample_rate: int = 8000) -> str:
        """
        Convert speech audio to text.
        
        Args:
            pcm_audio: Raw PCM audio data (16-bit signed)
            sample_rate: Audio sample rate (default 8000 for Twilio)
            
        Returns:
            Transcribed text
        """
        if self.stt_provider == "openai":
            return await self._whisper_transcribe(pcm_audio, sample_rate)
        else:
            return await self._transcribe_audio(pcm_audio, sample_rate)
    
    async def _whisper_transcribe(self, pcm_audio: bytes, sample_rate: int) -> str:
        """Transcribe audio using OpenAI Whisper."""
        try:
            # Convert PCM to WAV format for Whisper
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_audio)
            
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"  # Whisper needs a filename
            
            # Call Whisper API
            # Run in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                None,
                lambda: self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=wav_buffer,
                    language="en",
                ),
            )
            
            return transcription.text
            
        except Exception as e:
            logger.error("Whisper transcription error", error=str(e))
            return ""
    
    async def _transcribe_audio(self, pcm_audio: bytes, sample_rate: int) -> str:
        """Transcribe audio using AWS Transcribe (fallback)."""
        # TODO: Implement AWS Transcribe streaming
        logger.warning("AWS Transcribe not yet implemented, using mock")
        return ""
    
    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Base64-encoded MP3 audio
        """
        if self.tts_provider == "openai":
            return await self._openai_tts(text)
        else:
            return await self._polly_tts(text)
    
    async def text_to_speech_twilio(self, text: str) -> str:
        """
        Convert text to speech in Twilio-compatible format.
        
        Returns μ-law (PCMU) audio at 8kHz for Twilio Media Streams.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Base64-encoded μ-law audio
        """
        if self.tts_provider == "openai":
            return await self._openai_tts_twilio(text)
        else:
            return await self._polly_tts_twilio(text)
    
    async def _openai_tts(self, text: str) -> str:
        """Generate speech using OpenAI TTS (returns MP3)."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text,
                    response_format="mp3",
                ),
            )
            
            audio_bytes = response.content
            return base64.b64encode(audio_bytes).decode("utf-8")
            
        except Exception as e:
            logger.error("OpenAI TTS error", error=str(e))
            return ""
    
    async def _openai_tts_twilio(self, text: str) -> str:
        """
        Generate speech using OpenAI TTS and convert to Twilio format.
        
        OpenAI TTS outputs 24kHz audio, we need to convert to 8kHz μ-law.
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Get PCM audio from OpenAI
            response = await loop.run_in_executor(
                None,
                lambda: self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text,
                    response_format="pcm",  # Raw PCM (24kHz, 16-bit, mono)
                ),
            )
            
            pcm_24k = response.content
            
            # Convert from 24kHz to 8kHz
            # First, resample to 8kHz
            pcm_8k, _ = audioop.ratecv(pcm_24k, 2, 1, 24000, 8000, None)
            
            # Convert to μ-law
            ulaw_audio = audioop.lin2ulaw(pcm_8k, 2)
            
            return base64.b64encode(ulaw_audio).decode("utf-8")
            
        except Exception as e:
            logger.error("OpenAI TTS (Twilio format) error", error=str(e))
            return ""
    
    async def _polly_tts(self, text: str) -> str:
        """Generate speech using AWS Polly (returns MP3)."""
        try:
            import boto3
            
            polly = boto3.client("polly", region_name=settings.aws_region)
            
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat="mp3",
                VoiceId=settings.polly_voice_id,
                Engine=settings.polly_engine,
            )
            
            audio_stream = response["AudioStream"]
            audio_bytes = audio_stream.read()
            
            return base64.b64encode(audio_bytes).decode("utf-8")
            
        except Exception as e:
            logger.error("Polly TTS error", error=str(e))
            return ""
    
    async def _polly_tts_twilio(self, text: str) -> str:
        """Generate speech using AWS Polly in Twilio format."""
        try:
            import boto3
            
            polly = boto3.client("polly", region_name=settings.aws_region)
            
            # Polly supports pcm output at 8000 Hz
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat="pcm",
                SampleRate="8000",
                VoiceId=settings.polly_voice_id,
                Engine="standard",  # Neural doesn't support 8000 Hz PCM
            )
            
            audio_stream = response["AudioStream"]
            pcm_audio = audio_stream.read()
            
            # Convert to μ-law
            ulaw_audio = audioop.lin2ulaw(pcm_audio, 2)
            
            return base64.b64encode(ulaw_audio).decode("utf-8")
            
        except Exception as e:
            logger.error("Polly TTS (Twilio format) error", error=str(e))
            return ""


# Utility functions for audio format conversion

def mulaw_to_pcm(mulaw_data: bytes) -> bytes:
    """Convert μ-law to 16-bit PCM."""
    return audioop.ulaw2lin(mulaw_data, 2)


def pcm_to_mulaw(pcm_data: bytes) -> bytes:
    """Convert 16-bit PCM to μ-law."""
    return audioop.lin2ulaw(pcm_data, 2)


def resample_audio(
    audio_data: bytes,
    sample_width: int,
    channels: int,
    from_rate: int,
    to_rate: int,
) -> bytes:
    """Resample audio to a different sample rate."""
    resampled, _ = audioop.ratecv(audio_data, sample_width, channels, from_rate, to_rate, None)
    return resampled


def create_wav_buffer(pcm_data: bytes, sample_rate: int, channels: int = 1, sample_width: int = 2) -> io.BytesIO:
    """Create a WAV file buffer from PCM data."""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    buffer.seek(0)
    return buffer
