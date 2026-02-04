"""
Scam Detection Agent - Stub Implementation
Team members will replace this with actual LLM-based detection
"""
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def detect_scam(text: str, conversation_history: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze incoming message to detect if it's a scam
    
    Args:
        text: The message text to analyze
        conversation_history: Previous messages in the conversation
        metadata: Additional context from GUVI
        
    Returns:
        {
            "isScam": bool,
            "confidence": float (0.0-1.0),
            "scamType": str ("UPI_FRAUD" | "BANK_FRAUD" | "PHISHING" | "OTHER")
        }
    """
    logger.info(f"[STUB] Scam Detection called with text: {text[:50]}...")
    
    # STUB LOGIC: Simple keyword detection for testing
    # Real implementation will use LLM
    scam_keywords = ["upi", "bank", "account", "transfer", "payment", "link", "verify", "urgent", "prize", "won"]
    text_lower = text.lower()
    
    is_scam = any(keyword in text_lower for keyword in scam_keywords)
    
    # Determine scam type based on keywords
    if "upi" in text_lower or "payment" in text_lower:
        scam_type = "UPI_FRAUD"
    elif "bank" in text_lower or "account" in text_lower:
        scam_type = "BANK_FRAUD"
    elif "link" in text_lower or "verify" in text_lower:
        scam_type = "PHISHING"
    else:
        scam_type = "OTHER"
    
    result = {
        "isScam": is_scam,
        "confidence": 0.85 if is_scam else 0.3,
        "scamType": scam_type if is_scam else "NONE"
    }
    
    logger.debug(f"[STUB] Scam Detection result: {result}")
    return result
