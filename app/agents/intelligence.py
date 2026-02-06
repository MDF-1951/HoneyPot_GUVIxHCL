import logging
import json
from typing import List, Optional, Dict, Any
from langchain_groq import ChatGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

# --- 2. INITIALIZE GROQ ---
# Use standard LLM call instead of structured output for better compatibility
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    groq_api_key="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"
)

def extract_intelligence(incoming_message: str, previous_intel: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyzes the message and returns structured intelligence data using standard prompt.
    """
    if not previous_intel:
        previous_intel = {
            "upi_ids": [],
            "bank_accounts": [],
            "phishing_links": [],
            "phone_numbers": [],
            "tactics": [],
            "missing_info": []
        }

    system_prompt = f"""
    You are a Scam Intelligence Extraction System. 
    Analyze the LATEST MESSAGE from a scammer.
    
    CONTEXT (What we already know):
    {json.dumps(previous_intel)}
    
    TASK:
    1. Extract ANY new UPI IDs, Phone Numbers, or Bank Details from the LATEST MESSAGE.
    2. Identify the tactic used (e.g., urgency, fear, greed).
    3. Check if we are still missing key details compared to common scams.
    4. Set has_new_intel to true if any field was updated.
    
    OUTPUT FORMAT:
    You MUST return a valid JSON object with these keys:
    upi_ids: list[str]
    bank_accounts: list[str]
    phishing_links: list[str]
    phone_numbers: list[str]
    tactics: list[str]
    missing_info: list[str]
    has_new_intel: bool
    """

    try:
        full_prompt = f"{system_prompt}\n\nLATEST MESSAGE: {incoming_message}\n\nJSON OUTPUT:"
        response = llm.invoke(full_prompt)
        text = response.content.strip()
        
        # Remove markdown code blocks if any
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        return json.loads(text)
    except Exception as e:
        logger.error(f"Error in intelligence extraction: {e}")
        # Return previous intel as fallback
        return previous_intel
