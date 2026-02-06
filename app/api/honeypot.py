from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_api_key
from app.models.session import HoneypotRequest, HoneypotResponse
from app.core.controller import process_message
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=HoneypotResponse, dependencies=[Depends(verify_api_key)])
def honeypot_entry(request: HoneypotRequest) -> HoneypotResponse:
    """
    Main honeypot endpoint - receives messages from GUVI and returns replies
    
    Flow:
    1. Validate incoming request
    2. Pass to controller for processing
    3. Return generated reply
    
    Args:
        request: HoneypotRequest with sessionId, message, conversationHistory, metadata
        
    Returns:
        HoneypotResponse with status and reply
    """
    try:
        logger.info(f"Received request for session: {request.sessionId}")
        
        # Validate request has required fields
        if not request.sessionId:
            raise HTTPException(status_code=400, detail="sessionId is required")
        if not request.message or not request.message.text:
            raise HTTPException(status_code=400, detail="message.text is required")
        
        # Process through controller
        response = process_message(request)
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in honeypot endpoint: {e}", exc_info=True)
        # Return safe fallback response instead of crashing
        return HoneypotResponse(
            status="success",
            reply="I'm having trouble understanding. Could you repeat that?"
        )
