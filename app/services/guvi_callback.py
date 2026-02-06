import logging
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

CALLBACK_PREVIEW_FILE = "guvi_callback_preview.log"

def send_final_result(
    session_id: str,
    intelligence: Dict[str, Any],
    conversation_turns: int,
    scam_type: str
) -> bool:
    """
    Sends the final extracted intelligence to GUVI API.
    Also logs the exact payload to guvi_callback_preview.log
    """
    
    # Map internal naming to GUVI required keys
    formatted_intel = {
        "bankAccounts": intelligence.get("bank_accounts", []),
        "upiIds": intelligence.get("upi_ids", []),
        "phishingLinks": intelligence.get("phishing_links", []),
        "phoneNumbers": intelligence.get("phone_numbers", []),
        "suspiciousKeywords": intelligence.get("tactics", [])
    }
    
    # Construct exact requested payload
    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": conversation_turns,
        "extractedIntelligence": formatted_intel,
        "agentNotes": f"Scam type: {scam_type}. Scammer used {', '.join(intelligence.get('tactics', []))} tactics."
    }
    
    # Log to preview file for the user
    _log_preview(payload)
    
    headers = {
        "x-api-key": settings.GUVI_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Skip actual API call if key is not set (useful for local hackathon testing)
    if not settings.GUVI_API_KEY:
        logger.warning(f"GUVI_API_KEY not set. Logged preview to {CALLBACK_PREVIEW_FILE} but skipping POST.")
        return True

    try:
        logger.info(f"Sending final result for session {session_id} to {settings.GUVI_CALLBACK_URL}")
        
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                settings.GUVI_CALLBACK_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully reported session {session_id}. Response: {response.text}")
                return True
            else:
                logger.error(f"Failed to report session {session_id}. Status: {response.status_code}, Body: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending GUVI callback for session {session_id}: {e}")
        return False

def _log_preview(payload: dict):
    """Logs the exact payload to a preview file as requested by the user"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(CALLBACK_PREVIEW_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] FINAL GUVI CALLBACK PAYLOAD\n")
        f.write(f"{'='*80}\n")
        f.write(json.dumps(payload, indent=2))
        f.write("\n")
