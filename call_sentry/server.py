"""
BRO Call Sentry - Twilio Server
FastAPI server that handles incoming calls from Twilio.

How it works:
1. Twilio receives a call and hits /incoming-call
2. We tell Twilio to stream audio to our websocket
3. We transcribe, think, and speak back in real-time
4. Summary is generated and saved after the call

Setup:
1. pip install fastapi uvicorn twilio websockets
2. Get a Twilio account and phone number
3. Run: python server.py
4. Run: ngrok http 5000
5. Configure Twilio webhook to: https://YOUR-NGROK-URL/incoming-call
"""

import os
import sys
import json
import base64
import asyncio
from datetime import datetime
from typing import Optional

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi import FastAPI, WebSocket, Request
    from fastapi.responses import Response
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not installed. Run: pip install fastapi uvicorn")

try:
    from twilio.twiml.voice_response import VoiceResponse, Connect, Stream, Say, Gather
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Twilio not installed. Run: pip install twilio")

from call_sentry import (
    PERSONALITIES, CURRENT_MODE, set_mode, get_mode, get_greeting,
    generate_response, generate_summary,
    CallRecord, CallHistoryManager
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Your ngrok URL (update this when you run ngrok)
NGROK_URL = os.getenv("NGROK_URL", "your-ngrok-url.ngrok.io")

# Twilio credentials (optional - for outbound features)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")

# Server settings
HOST = "0.0.0.0"
PORT = 5000

# =============================================================================
# APP SETUP
# =============================================================================

if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="BRO Call Sentry",
        description="AI-powered call screening with personality switching"
    )
else:
    app = None

# Active calls tracker
active_calls = {}


# =============================================================================
# ROUTES
# =============================================================================

if app:
    @app.get("/")
    async def root():
        """Health check and status."""
        return {
            "status": "online",
            "service": "BRO Call Sentry",
            "mode": CURRENT_MODE,
            "personality": PERSONALITIES[CURRENT_MODE].name,
            "greeting": get_greeting()
        }
    
    @app.get("/mode")
    async def get_current_mode():
        """Get current screening mode."""
        return {"mode": CURRENT_MODE, "info": get_mode()}
    
    @app.post("/mode/{mode_name}")
    async def switch_mode(mode_name: str):
        """Switch personality mode."""
        result = set_mode(mode_name)
        return {"result": result, "current_mode": CURRENT_MODE}
    
    @app.post("/incoming-call")
    async def handle_incoming_call(request: Request):
        """
        Twilio webhook - called when someone calls your Twilio number.
        """
        if not TWILIO_AVAILABLE:
            return Response(content="Twilio not available", status_code=500)
        
        # Get call info from Twilio
        form_data = await request.form()
        caller_number = form_data.get("From", "Unknown")
        call_sid = form_data.get("CallSid", "unknown")
        
        print(f"\n{'='*50}")
        print(f"📞 INCOMING CALL from {caller_number}")
        print(f"   Mode: {CURRENT_MODE} ({PERSONALITIES[CURRENT_MODE].name})")
        print(f"{'='*50}")
        
        # Track this call
        active_calls[call_sid] = {
            "caller": caller_number,
            "mode": CURRENT_MODE,
            "transcript": [],
            "start_time": datetime.now()
        }
        
        # Build TwiML response
        response = VoiceResponse()
        
        # Option 1: Simple gather (wait for speech, then respond)
        # This is simpler but less real-time
        personality = PERSONALITIES[CURRENT_MODE]
        
        # Say greeting
        response.say(
            personality.greeting,
            voice="Polly.Matthew" if personality.use_formal_language else "Polly.Joey"
        )
        
        # Gather speech input
        gather = Gather(
            input="speech",
            action=f"/process-speech?call_sid={call_sid}",
            speech_timeout="auto",
            language="en-US"
        )
        response.append(gather)
        
        # If no input, hang up politely
        response.say("I didn't catch that. Goodbye.")
        
        return Response(
            content=str(response),
            media_type="application/xml"
        )
    
    @app.post("/process-speech")
    async def process_speech(request: Request, call_sid: str = "unknown"):
        """Process gathered speech and respond."""
        if not TWILIO_AVAILABLE:
            return Response(content="Twilio not available", status_code=500)
        
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        
        print(f"[Caller said]: {speech_result}")
        
        # Get call context
        call_data = active_calls.get(call_sid, {"transcript": [], "mode": CURRENT_MODE})
        call_data["transcript"].append({"role": "user", "content": speech_result})
        
        # Generate AI response
        ai_response = generate_response(speech_result, call_data["transcript"], call_data["mode"])
        print(f"[BRO]: {ai_response}")
        
        call_data["transcript"].append({"role": "assistant", "content": ai_response})
        active_calls[call_sid] = call_data
        
        # Build response
        response = VoiceResponse()
        personality = PERSONALITIES[call_data["mode"]]
        
        response.say(
            ai_response,
            voice="Polly.Matthew" if personality.use_formal_language else "Polly.Joey"
        )
        
        # Continue gathering or end
        if any(word in speech_result.lower() for word in ["bye", "goodbye", "that's all", "thanks"]):
            response.say("Goodbye, have a great day!")
            # Save call when done
            asyncio.create_task(save_call_record(call_sid))
        else:
            # Gather more speech
            gather = Gather(
                input="speech",
                action=f"/process-speech?call_sid={call_sid}",
                speech_timeout="auto",
                language="en-US"
            )
            response.append(gather)
        
        return Response(
            content=str(response),
            media_type="application/xml"
        )
    
    @app.post("/call-complete")
    async def call_complete(request: Request):
        """Called when a call ends - save the record."""
        form_data = await request.form()
        call_sid = form_data.get("CallSid", "unknown")
        await save_call_record(call_sid)
        return {"status": "recorded"}
    
    @app.get("/calls")
    async def get_calls():
        """Get recent call history."""
        manager = CallHistoryManager()
        return {"calls": manager.get_recent_calls(10)}
    
    @app.get("/calls/today")
    async def get_todays_calls():
        """Get today's calls."""
        manager = CallHistoryManager()
        return {"calls": manager.get_todays_calls()}


async def save_call_record(call_sid: str):
    """Save call record to history."""
    call_data = active_calls.pop(call_sid, None)
    if not call_data or not call_data.get("transcript"):
        return
    
    # Generate summary
    summary, action_items = generate_summary(call_data["transcript"])
    
    # Calculate duration
    duration = (datetime.now() - call_data["start_time"]).seconds
    
    # Create record
    record = CallRecord(
        timestamp=datetime.now().isoformat(),
        caller_number=call_data.get("caller", "Unknown"),
        personality_mode=call_data.get("mode", CURRENT_MODE),
        duration_seconds=duration,
        transcript=call_data["transcript"],
        summary=summary,
        action_items=action_items
    )
    
    # Save
    manager = CallHistoryManager()
    manager.add_call(record)
    print(f"\n📝 Call saved. Summary: {summary}")


# =============================================================================
# WEBSOCKET STREAMING (Advanced - for real-time)
# =============================================================================

if app:
    @app.websocket("/stream")
    async def websocket_stream(websocket: WebSocket):
        """
        Real-time audio streaming endpoint.
        For future: integrate with Whisper for live transcription.
        """
        await websocket.accept()
        print("🎧 Audio stream connected")
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("event") == "media":
                    # Audio payload (base64 encoded)
                    payload = message.get("media", {}).get("payload", "")
                    # TODO: Decode and send to Whisper for transcription
                    # audio_bytes = base64.b64decode(payload)
                    
                elif message.get("event") == "stop":
                    print("📴 Stream stopped")
                    break
                    
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            print("🔇 Audio stream disconnected")


# =============================================================================
# CLI & MAIN
# =============================================================================

def print_setup_guide():
    """Print setup instructions."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║              BRO CALL SENTRY - SETUP GUIDE                ║
╚══════════════════════════════════════════════════════════════╝

📋 STEP 1: Install Dependencies
   pip install fastapi uvicorn twilio websockets

📋 STEP 2: Get Twilio Account (Free Trial)
   1. Go to: https://www.twilio.com/try-twilio
   2. Sign up (no credit card needed for trial)
   3. Get a phone number (~$1/month after trial)
   4. Note your Account SID and Auth Token

📋 STEP 3: Start the Server
   python server.py

📋 STEP 4: Expose with Ngrok
   1. Download ngrok: https://ngrok.com
   2. Run: ngrok http 5000
   3. Copy the https URL (e.g., https://abc123.ngrok.io)

📋 STEP 5: Configure Twilio Webhook
   1. Go to Twilio Console > Phone Numbers
   2. Click your number
   3. Under "Voice & Fax", set:
      - "A CALL COMES IN" = Webhook
      - URL = https://YOUR-NGROK-URL/incoming-call
      - Method = POST

📋 STEP 6: Forward Your Phone
   On Android: Dial **21*TWILIO_NUMBER# to forward all calls
   On iPhone: Settings > Phone > Call Forwarding

📋 STEP 7: Test It!
   Call your personal number - it should forward to BRO!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 CONFIGURATION

Current Mode: {mode} ({name})
Greeting: "{greeting}"

Switch modes:
  curl -X POST http://localhost:5000/mode/professional
  curl -X POST http://localhost:5000/mode/friendly
  curl -X POST http://localhost:5000/mode/guard

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(
        mode=CURRENT_MODE,
        name=PERSONALITIES[CURRENT_MODE].name,
        greeting=get_greeting()
    ))


if __name__ == "__main__":
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)
    
    print_setup_guide()
    
    print("🚀 Starting BRO Call Sentry Server...")
    print(f"   URL: http://localhost:{PORT}")
    print(f"   Mode: {CURRENT_MODE}")
    print("\nPress Ctrl+C to stop\n")
    
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
