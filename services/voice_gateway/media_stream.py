"""
Twilio Media Streams WebSocket Handler
======================================

Handles real-time bidirectional audio streaming with Twilio.

Twilio Media Streams Protocol:
- Audio is sent as base64-encoded μ-law (PCMU) at 8kHz
- Messages are JSON with event types: connected, start, media, stop
- We need to convert to/from formats suitable for STT/TTS
"""

import asyncio
import base64
import json
from typing import Optional
import audioop

from fastapi import WebSocket

from services.common.logging import get_logger
from services.voice_gateway.audio_processor import AudioProcessor

logger = get_logger("media-stream")


class TwilioMediaStreamHandler:
    """
    Handles a single Twilio Media Stream connection.
    
    Processes incoming audio, sends to LLM, and returns synthesized speech.
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        service: str,
        service_url: str,
    ):
        self.websocket = websocket
        self.service = service
        self.service_url = service_url
        
        # Stream metadata
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.account_sid: Optional[str] = None
        
        # Audio processing
        self.audio_processor = AudioProcessor()
        
        # Audio buffer for accumulating speech
        self.audio_buffer = bytearray()
        self.silence_threshold = 500  # Silence detection threshold
        self.silence_duration = 0
        self.max_silence_frames = 50  # ~1 second of silence at 20ms frames
        self.is_speaking = False
        
        # State
        self.is_processing = False
        self.closed = False
    
    async def handle_stream(self):
        """Main loop to handle incoming WebSocket messages."""
        try:
            while not self.closed:
                message = await self.websocket.receive_text()
                await self._process_message(json.loads(message))
                
        except Exception as e:
            logger.error("Stream handling error", error=str(e))
            raise
    
    async def _process_message(self, message: dict):
        """Process a single Twilio Media Stream message."""
        event = message.get("event")
        
        if event == "connected":
            logger.info("Media stream connected")
            
        elif event == "start":
            # Stream metadata
            start_data = message.get("start", {})
            self.stream_sid = start_data.get("streamSid")
            self.call_sid = start_data.get("callSid")
            self.account_sid = start_data.get("accountSid")
            
            # Get custom parameters (service selection)
            custom_params = start_data.get("customParameters", {})
            if "service" in custom_params:
                self.service = custom_params["service"]
            
            logger.info(
                "Media stream started",
                stream_sid=self.stream_sid,
                call_sid=self.call_sid,
                service=self.service,
            )
            
            # Send initial greeting
            await self._send_greeting()
            
        elif event == "media":
            # Process incoming audio
            await self._process_audio(message.get("media", {}))
            
        elif event == "stop":
            logger.info("Media stream stopped", stream_sid=self.stream_sid)
            self.closed = True
            
        elif event == "mark":
            # Audio playback marker (for tracking when audio finishes playing)
            mark_name = message.get("mark", {}).get("name")
            logger.debug("Playback mark", name=mark_name)
    
    async def _send_greeting(self):
        """Send an initial greeting when the stream starts."""
        service_greetings = {
            "voicebank": "You are now connected to Voice Bank, your banking assistant. I can help you with account balances, transfers, and more. How can I help you today?",
            "voiceadmin": "You are now connected to Voice Admin, the system administration console. I can help you manage users, run queries, and execute commands. What would you like to do?",
            "voicerag": "You are now connected to Voice RAG, the knowledge base assistant. I can search documents and answer questions from our knowledge base. What would you like to know?",
        }
        greeting = service_greetings.get(
            self.service, 
            f"You are now connected to {self.service.replace('voice', 'Voice ')}. How can I help you?"
        )
        logger.info("Sending greeting", service=self.service, greeting_length=len(greeting))
        await self._send_speech(greeting)
    
    async def _process_audio(self, media: dict):
        """
        Process incoming audio from Twilio.
        
        Audio comes as base64-encoded μ-law (PCMU) at 8kHz.
        We accumulate audio until we detect end of speech, then process.
        """
        if self.is_processing:
            # Skip incoming audio while we're generating a response
            return
        
        # Decode the audio
        payload = media.get("payload", "")
        if not payload:
            return
        
        try:
            audio_data = base64.b64decode(payload)
            
            # Convert μ-law to linear PCM for analysis
            pcm_data = audioop.ulaw2lin(audio_data, 2)
            
            # Simple voice activity detection based on RMS
            rms = audioop.rms(pcm_data, 2)
            
            if rms > self.silence_threshold:
                # Speech detected
                self.is_speaking = True
                self.silence_duration = 0
                self.audio_buffer.extend(audio_data)
            else:
                # Silence
                if self.is_speaking:
                    self.silence_duration += 1
                    self.audio_buffer.extend(audio_data)
                    
                    # Check if we've had enough silence to consider speech ended
                    if self.silence_duration >= self.max_silence_frames:
                        # Process the accumulated audio
                        await self._process_speech_segment()
                        self.audio_buffer = bytearray()
                        self.is_speaking = False
                        self.silence_duration = 0
                        
        except Exception as e:
            logger.error("Audio processing error", error=str(e))
    
    async def _process_speech_segment(self):
        """Process a complete speech segment."""
        if len(self.audio_buffer) < 1000:
            # Too short, probably noise
            return
        
        self.is_processing = True
        
        try:
            logger.info(
                "Processing speech segment",
                audio_bytes=len(self.audio_buffer),
                service=self.service,
            )
            
            # Convert μ-law to format suitable for STT
            # First convert to linear PCM
            pcm_data = audioop.ulaw2lin(bytes(self.audio_buffer), 2)
            
            # Transcribe the audio
            transcription = await self.audio_processor.speech_to_text(pcm_data)
            
            if not transcription or len(transcription.strip()) < 2:
                logger.debug("Empty or too short transcription, skipping")
                return
            
            logger.info("Transcription", text=transcription)
            
            # Send to the appropriate VoiceGoat service
            response_text = await self._call_service(transcription)
            
            if response_text:
                logger.info("Service response", text=response_text[:100])
                await self._send_speech(response_text)
                
        except Exception as e:
            logger.error("Speech processing error", error=str(e))
            await self._send_speech("I'm sorry, I encountered an error processing your request.")
            
        finally:
            self.is_processing = False
    
    async def _call_service(self, text: str) -> str:
        """Call the VoiceGoat service with the transcribed text."""
        import httpx
        
        logger.info(
            "Calling service",
            service=self.service,
            service_url=self.service_url,
            text=text[:100],
        )
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if self.service == "voicebank":
                    logger.debug("Calling VoiceBank /chat endpoint")
                    response = await client.post(
                        f"{self.service_url}/chat",
                        json={
                            "message": text,
                            "user_id": f"phone_{self.call_sid or 'unknown'}",
                        },
                    )
                    data = response.json()
                    result = data.get("response", "")
                    logger.info("VoiceBank response", response_length=len(result))
                    return result
                    
                elif self.service == "voiceadmin":
                    logger.debug("Calling VoiceAdmin /command endpoint")
                    response = await client.post(
                        f"{self.service_url}/command",
                        json={
                            "command": text,
                            "user_id": f"phone_{self.call_sid or 'unknown'}",
                        },
                    )
                    data = response.json()
                    # VoiceAdmin returns output which could be dict or string
                    output = data.get("output", data)
                    if isinstance(output, dict):
                        result = output.get("message", str(output))
                    else:
                        result = str(output)
                    logger.info("VoiceAdmin response", response_length=len(result))
                    return result
                    
                elif self.service == "voicerag":
                    logger.debug("Calling VoiceRAG /chat endpoint")
                    response = await client.post(
                        f"{self.service_url}/chat",
                        json={
                            "message": text,
                            "user_id": f"phone_{self.call_sid or 'unknown'}",
                            "tenant_id": "default",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    result = data.get("response", "")
                    logger.info("VoiceRAG response", response_length=len(result), has_response=bool(result))
                    return result if result else "I couldn't find any relevant information in the knowledge base."
                    
                else:
                    logger.warning("Unknown service requested", service=self.service)
                    return f"Unknown service: {self.service}"
                    
        except httpx.ConnectError as e:
            logger.error("Service connection failed", service=self.service, url=self.service_url, error=str(e))
            return f"I'm having trouble connecting to the {self.service.replace('voice', 'Voice ')} service."
        except httpx.HTTPStatusError as e:
            logger.error("Service HTTP error", service=self.service, status=e.response.status_code, error=str(e))
            return "The service encountered an error. Please try again."
        except Exception as e:
            logger.error("Service call error", service=self.service, error=str(e), error_type=type(e).__name__)
            return "I'm having trouble connecting to the service right now."
    
    async def _send_speech(self, text: str):
        """Convert text to speech and send to Twilio."""
        try:
            # Generate speech audio
            audio_base64 = await self.audio_processor.text_to_speech_twilio(text)
            
            if not audio_base64:
                logger.warning("Failed to generate speech audio")
                return
            
            # Send audio in chunks to Twilio
            # Twilio expects 20ms chunks of μ-law audio at 8kHz = 160 bytes per chunk
            chunk_size = 160
            audio_bytes = base64.b64decode(audio_base64)
            
            for i in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    # Pad the last chunk with silence (μ-law silence = 0xFF)
                    chunk = chunk + bytes([0xFF] * (chunk_size - len(chunk)))
                
                # Send media message
                media_message = {
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {
                        "payload": base64.b64encode(chunk).decode("utf-8"),
                    },
                }
                await self.websocket.send_text(json.dumps(media_message))
                
                # Small delay to prevent overwhelming the connection
                await asyncio.sleep(0.018)  # ~20ms
            
            # Send mark to know when playback is complete
            mark_message = {
                "event": "mark",
                "streamSid": self.stream_sid,
                "mark": {
                    "name": f"response_{id(text)}",
                },
            }
            await self.websocket.send_text(json.dumps(mark_message))
            
            logger.info("Sent speech response", text_length=len(text), audio_bytes=len(audio_bytes))
            
        except Exception as e:
            logger.error("Send speech error", error=str(e))
    
    async def close(self):
        """Clean up resources."""
        self.closed = True
        try:
            await self.websocket.close()
        except Exception:
            pass
