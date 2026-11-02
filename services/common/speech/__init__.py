"""Speech processing utilities - Transcribe (STT) and Polly (TTS) wrappers."""

from services.common.speech.transcribe import TranscribeClient, transcribe_audio
from services.common.speech.polly import PollyClient, synthesize_speech

__all__ = [
    "TranscribeClient",
    "transcribe_audio",
    "PollyClient", 
    "synthesize_speech",
]
