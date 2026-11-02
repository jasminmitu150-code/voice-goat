"""
Voice Gateway - Twilio Integration for VoiceGoat
=================================================

This service handles incoming phone calls via Twilio and routes them
to the appropriate VoiceGoat services (VoiceBank, VoiceAdmin, VoiceRAG).

Architecture:
    Phone Call → Twilio → WebSocket (Media Streams) → Voice Gateway
                                                            ↓
                                                    STT (Whisper/Transcribe)
                                                            ↓
                                                    LLM (VoiceGoat Services)
                                                            ↓
                                                    TTS (OpenAI/Polly)
                                                            ↓
                                                    Audio Response → Caller
"""

import os
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urljoin

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.common.config import settings
from services.common.logging import get_logger
from services.voice_gateway.media_stream import TwilioMediaStreamHandler

logger = get_logger("voice-gateway")

# Service endpoints for routing
SERVICE_ENDPOINTS = {
    "voicebank": os.getenv("VOICEBANK_URL", "http://voicebank:8000"),
    "voiceadmin": os.getenv("VOICEADMIN_URL", "http://voiceadmin:8000"),
    "voicerag": os.getenv("VOICERAG_URL", "http://voicerag:8000"),
}

# Active WebSocket sessions
active_sessions: dict[str, TwilioMediaStreamHandler] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(
        "Voice Gateway starting",
        environment=settings.environment.value,
        services=list(SERVICE_ENDPOINTS.keys()),
    )
    yield
    # Cleanup active sessions
    for session_id, handler in active_sessions.items():
        await handler.close()
    logger.info("Voice Gateway shutting down")


app = FastAPI(
    title="VoiceGoat Voice Gateway",
    description="Twilio integration for voice-based security training",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Twilio Webhook Endpoints
# =============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "voice-gateway",
        "active_sessions": len(active_sessions),
    }


@app.api_route("/voice/incoming", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """
    Handle incoming Twilio voice calls.
    
    Returns TwiML to:
    1. Play a welcome message
    2. Gather DTMF or speech input for service selection
    3. Route to selected service
    """
    # Get the base URL for callbacks
    host = request.headers.get("host", "localhost:8004")
    scheme = "https" if "ngrok" in host or request.url.scheme == "https" else "http"
    base_url = f"{scheme}://{host}"
    
    logger.info(
        "Incoming call",
        from_number=request.query_params.get("From", "unknown"),
        to_number=request.query_params.get("To", "unknown"),
    )
    
    # TwiML with Gather for DTMF and speech input
    # - numDigits="1" for single button press
    # - input="dtmf speech" allows both button and voice
    # - timeout="10" waits 10 seconds for input
    # - speechTimeout="auto" for automatic speech detection
    # - hints help speech recognition
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="dtmf speech" numDigits="1" timeout="10" speechTimeout="auto" 
            action="{base_url}/voice/menu" method="POST"
            hints="voice bank, bank, one, voice admin, admin, two, voice rag, rag, knowledge, three">
        <Say voice="Polly.Joanna">
            Welcome to Voice Goat, the vulnerable voice agent training platform.
            Please select a service by pressing a button or saying the name.
            Press 1 or say Voice Bank for the banking assistant.
            Press 2 or say Voice Admin for system administration.
            Press 3 or say Voice Rag for the knowledge base.
        </Say>
    </Gather>
    <Say voice="Polly.Joanna">
        I didn't receive any input. Connecting you to Voice Bank by default.
    </Say>
    <Redirect>{base_url}/voice/connect?service=voicebank</Redirect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@app.api_route("/voice/menu", methods=["GET", "POST"])
async def handle_menu_selection(request: Request):
    """
    Handle DTMF (keypad) or speech menu selections.
    
    Twilio sends:
    - Digits: for DTMF input (e.g., "1", "2", "3")
    - SpeechResult: for speech input (e.g., "voice bank", "admin")
    """
    form_data = await request.form() if request.method == "POST" else {}
    
    # Get DTMF digits or speech result
    digits = form_data.get("Digits", "")
    speech_result = form_data.get("SpeechResult", "").lower()
    
    logger.info(
        "Menu selection received",
        digits=digits,
        speech_result=speech_result,
    )
    
    # Determine service from input
    service_id = "voicebank"  # default
    
    # Check DTMF first
    if digits == "1":
        service_id = "voicebank"
    elif digits == "2":
        service_id = "voiceadmin"
    elif digits == "3":
        service_id = "voicerag"
    # Check speech input
    elif speech_result:
        if any(word in speech_result for word in ["bank", "one", "1", "banking"]):
            service_id = "voicebank"
        elif any(word in speech_result for word in ["admin", "two", "2", "administration"]):
            service_id = "voiceadmin"
        elif any(word in speech_result for word in ["rag", "three", "3", "knowledge", "search"]):
            service_id = "voicerag"
    
    # Get base URL for redirect
    host = request.headers.get("host", "localhost:8004")
    scheme = "https" if "ngrok" in host or request.url.scheme == "https" else "http"
    base_url = f"{scheme}://{host}"
    
    logger.info("Routing to service", service=service_id, input_type="dtmf" if digits else "speech")
    
    # Redirect to connect endpoint
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Redirect>{base_url}/voice/connect?service={service_id}</Redirect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@app.api_route("/voice/connect", methods=["GET", "POST"])
async def connect_to_service(request: Request, service: str = "voicebank", mode: str = "fallback"):
    """
    Connect the call to a VoiceGoat service.
    
    Modes:
    - "stream": Use Twilio Media Streams (WebSocket) for real-time audio
    - "fallback": Use Gather/Say loop for more reliable interaction
    """
    service_names = {
        "voicebank": "Voice Bank, the banking assistant",
        "voiceadmin": "Voice Admin, the system administration console",
        "voicerag": "Voice Rag, the knowledge base assistant",
    }
    
    service_name = service_names.get(service, "Voice Bank")
    host = request.headers.get("host", "localhost:8004")
    scheme = "https" if "ngrok" in host or request.url.scheme == "https" else "http"
    base_url = f"{scheme}://{host}"
    
    logger.info("Connecting to service", service=service, mode=mode)
    
    # Use fallback mode by default (more reliable)
    if mode == "stream":
        ws_protocol = "wss" if "ngrok" in host or request.url.scheme == "https" else "ws"
        ws_url = f"{ws_protocol}://{host}/media-stream?service={service}"
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Connecting you to {service_name}. 
        You can now speak to interact with the assistant.
        Say your request after the tone.
    </Say>
    <Play digits="w"></Play>
    <Connect>
        <Stream url="{ws_url}">
            <Parameter name="service" value="{service}" />
        </Stream>
    </Connect>
    <Say voice="Polly.Joanna">
        The connection has ended. Thank you for using Voice Goat.
    </Say>
</Response>"""
    else:
        # Fallback mode using Gather/Say loop
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        You are now connected to {service_name}. 
        Please speak your request after the beep.
    </Say>
    <Play digits="1"></Play>
    <Gather input="speech" timeout="8" speechTimeout="auto" 
            action="{base_url}/voice/process?service={service}" method="POST"
            language="en-US">
    </Gather>
    <Say voice="Polly.Joanna">
        I didn't hear anything. Let me try again.
    </Say>
    <Redirect>{base_url}/voice/connect?service={service}&amp;mode=fallback</Redirect>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@app.api_route("/voice/process", methods=["POST"])
async def process_voice_input(request: Request, service: str = "voicebank"):
    """
    Process speech input from Twilio Gather and call the VoiceGoat service.
    
    This is the fallback mode handler that uses Twilio's STT instead of WebSocket.
    """
    import httpx
    
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "").strip()
    confidence = form_data.get("Confidence", "0")
    
    host = request.headers.get("host", "localhost:8004")
    scheme = "https" if "ngrok" in host or request.url.scheme == "https" else "http"
    base_url = f"{scheme}://{host}"
    
    logger.info(
        "Processing voice input",
        service=service,
        speech=speech_result[:100] if speech_result else "(empty)",
        confidence=confidence,
    )
    
    if not speech_result:
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        I didn't catch that. Please try again.
    </Say>
    <Redirect>{base_url}/voice/connect?service={service}&amp;mode=fallback</Redirect>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    
    # Call the appropriate VoiceGoat service
    service_url = SERVICE_ENDPOINTS.get(service, SERVICE_ENDPOINTS["voicebank"])
    response_text = "I encountered an error. Please try again."
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if service == "voicebank":
                response = await client.post(
                    f"{service_url}/chat",
                    json={"message": speech_result, "user_id": "phone_user"},
                )
                data = response.json()
                response_text = data.get("response", "I couldn't process that request.")
                
            elif service == "voiceadmin":
                response = await client.post(
                    f"{service_url}/command",
                    json={"command": speech_result, "user_id": "phone_user"},
                )
                data = response.json()
                output = data.get("output", data)
                response_text = output.get("message", str(output)) if isinstance(output, dict) else str(output)
                
            elif service == "voicerag":
                response = await client.post(
                    f"{service_url}/chat",
                    json={"message": speech_result, "user_id": "phone_user", "tenant_id": "default"},
                )
                data = response.json()
                response_text = data.get("response", "I couldn't find any relevant information.")
                
    except Exception as e:
        logger.error("Service call failed", service=service, error=str(e))
        response_text = f"I'm having trouble connecting to {service.replace('voice', 'Voice ')}."
    
    # Truncate long responses for voice
    if len(response_text) > 1000:
        response_text = response_text[:997] + "..."
    
    logger.info("Service response", service=service, response_length=len(response_text))
    
    # Return response and loop back for more input
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{_escape_xml(response_text)}</Say>
    <Pause length="1"/>
    <Say voice="Polly.Joanna">Is there anything else I can help you with?</Say>
    <Gather input="speech" timeout="8" speechTimeout="auto" 
            action="{base_url}/voice/process?service={service}" method="POST"
            language="en-US">
    </Gather>
    <Say voice="Polly.Joanna">
        Thank you for using Voice Goat. Goodbye.
    </Say>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


def _escape_xml(text: str) -> str:
    """Escape special characters for XML/TwiML."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


@app.api_route("/voice/status", methods=["POST"])
async def handle_call_status(request: Request):
    """Handle call status callbacks from Twilio."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    logger.info("Call status update", call_sid=call_sid, status=call_status)
    
    # Cleanup session if call ended
    if call_status in ["completed", "failed", "busy", "no-answer"]:
        if call_sid in active_sessions:
            await active_sessions[call_sid].close()
            del active_sessions[call_sid]
    
    return Response(content="OK", media_type="text/plain")


# =============================================================================
# WebSocket Media Streams Handler
# =============================================================================

@app.websocket("/media-stream")
async def media_stream_websocket(
    websocket: WebSocket,
    service: str = Query(default="voicebank"),
):
    """
    WebSocket endpoint for Twilio Media Streams.
    
    Handles real-time bidirectional audio:
    - Receives audio from caller (μ-law encoded)
    - Transcribes audio using STT
    - Sends transcribed text to LLM service
    - Synthesizes response using TTS
    - Sends audio back to caller
    """
    await websocket.accept()
    
    logger.info("Media stream WebSocket connected", service=service)
    
    # Create handler for this stream
    handler = TwilioMediaStreamHandler(
        websocket=websocket,
        service=service,
        service_url=SERVICE_ENDPOINTS.get(service, SERVICE_ENDPOINTS["voicebank"]),
    )
    
    try:
        # Process the media stream
        await handler.handle_stream()
        
    except WebSocketDisconnect:
        logger.info("Media stream WebSocket disconnected")
    except Exception as e:
        logger.error("Media stream error", error=str(e))
    finally:
        await handler.close()


# =============================================================================
# Direct API Access (for testing without phone)
# =============================================================================

class TextInteractionRequest(BaseModel):
    """Text-based interaction request (for testing)."""
    text: str
    service: str = "voicebank"
    user_id: str = "phone_user"
    return_audio: bool = False


@app.post("/interact")
async def text_interaction(request: TextInteractionRequest):
    """
    Direct text interaction endpoint for testing without Twilio.
    
    Useful for testing the pipeline without making actual phone calls.
    """
    import httpx
    
    service_url = SERVICE_ENDPOINTS.get(request.service, SERVICE_ENDPOINTS["voicebank"])
    
    async with httpx.AsyncClient() as client:
        # Route to appropriate service endpoint
        if request.service == "voicebank":
            response = await client.post(
                f"{service_url}/chat",
                json={
                    "message": request.text,
                    "user_id": request.user_id,
                },
            )
        elif request.service == "voiceadmin":
            response = await client.post(
                f"{service_url}/command",
                json={
                    "command": request.text,
                    "user_id": request.user_id,
                },
            )
        elif request.service == "voicerag":
            response = await client.post(
                f"{service_url}/chat",
                json={
                    "message": request.text,
                    "user_id": request.user_id,
                    "tenant_id": "default",
                },
            )
        else:
            return {"error": f"Unknown service: {request.service}"}
        
        result = response.json()
        
        # Optionally generate audio response
        if request.return_audio:
            from services.voice_gateway.audio_processor import AudioProcessor
            processor = AudioProcessor()
            
            response_text = result.get("response") or result.get("output") or result.get("answer", "")
            audio_base64 = await processor.text_to_speech(response_text)
            result["audio_base64"] = audio_base64
        
        return result


@app.get("/services")
async def list_services():
    """List available voice services."""
    return {
        "services": [
            {
                "id": "voicebank",
                "name": "VoiceBank",
                "description": "Banking assistant (LLM01: Prompt Injection)",
                "dtmf": "1",
            },
            {
                "id": "voiceadmin", 
                "name": "VoiceAdmin",
                "description": "Admin console (LLM06: Excessive Agency)",
                "dtmf": "2",
            },
            {
                "id": "voicerag",
                "name": "VoiceRAG",
                "description": "Knowledge base (LLM08: Vector Weaknesses)",
                "dtmf": "3",
            },
        ],
        "instructions": "Call your Twilio number and press 1, 2, or 3 to select a service.",
    }
