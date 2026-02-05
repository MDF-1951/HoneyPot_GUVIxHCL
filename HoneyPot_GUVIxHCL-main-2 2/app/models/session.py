"""
Data models for session management and API contracts
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class SessionState(str, Enum):
    """Session state machine states"""
    INIT = "INIT"
    SCAM_CONFIRMED = "SCAM_CONFIRMED"
    ENGAGING = "ENGAGING"
    EXTRACTING = "EXTRACTING"
    EXIT_READY = "EXIT_READY"
    REPORTED = "REPORTED"


class MessageData(BaseModel):
    """Individual message structure from GUVI"""
    sender: str
    text: str
    timestamp: int


class HoneypotRequest(BaseModel):
    """Incoming request from GUVI"""
    sessionId: str
    message: MessageData
    conversationHistory: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class HoneypotResponse(BaseModel):
    """Response to GUVI"""
    status: str = "success"
    reply: str


class SessionData(BaseModel):
    """Complete session state stored in Redis"""
    sessionId: str
    state: SessionState = SessionState.INIT
    turnCount: int = 0
    persona: Dict[str, Any] = {}
    intelligence: Dict[str, Any] = {}
    conversationHistory: List[Dict[str, Any]] = []
    reported: bool = False
    scamType: Optional[str] = None
