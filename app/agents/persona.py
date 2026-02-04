"""
Persona Agent - Stub Implementation
Team members will replace this with actual LLM-based persona management
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def update_persona(
    previous_persona: Dict[str, Any],
    latest_message: str,
    session_state: str,
    turn_count: int
) -> Dict[str, Any]:
    """
    Update and evolve the victim persona based on conversation progress
    
    Args:
        previous_persona: The persona from the last turn
        latest_message: Most recent message from scammer
        session_state: Current session state
        turn_count: Number of conversation turns
        
    Returns:
        {
            "emotion": str ("calm" | "worried" | "scared" | "confused"),
            "trustLevel": str ("low" | "medium" | "high"),
            "techLiteracy": str ("low"),
            "patience": str ("high" | "medium" | "low"),
            "responseStyle": str ("short_hesitant" | "cooperative" | "confused")
        }
    """
    logger.info(f"[STUB] Persona Agent called for turn {turn_count}, state: {session_state}")
    
    # STUB LOGIC: Evolve persona based on turn count
    # Real implementation will use LLM to dynamically adapt
    
    if turn_count <= 2:
        # Early stage: confused and hesitant
        persona = {
            "emotion": "confused",
            "trustLevel": "low",
            "techLiteracy": "low",
            "patience": "high",
            "responseStyle": "short_hesitant"
        }
    elif turn_count <= 5:
        # Middle stage: becoming worried but cooperative
        persona = {
            "emotion": "worried",
            "trustLevel": "medium",
            "techLiteracy": "low",
            "patience": "medium",
            "responseStyle": "cooperative"
        }
    else:
        # Later stage: scared but still engaged
        persona = {
            "emotion": "scared",
            "trustLevel": "high",
            "techLiteracy": "low",
            "patience": "low",
            "responseStyle": "cooperative"
        }
    
    logger.debug(f"[STUB] Persona result: {persona}")
    return persona
