"""
Controller - Main orchestration logic for the honeypot system
Coordinates all agents and manages session state machine
"""
import logging
import json
from typing import Dict, Any, List
from app.models.session import HoneypotRequest, HoneypotResponse, SessionData, SessionState
from app.core.session import get_session, save_session
from app.agents.scam_detection import detect_scam
from app.agents.scammer_profiler import profile_scammer
from app.agents.intelligence import extract_intelligence
from app.agents.strategy import decide_strategy
from app.agents.conversation import generate_reply
from app.agents.conversation import generate_reply
from app.utils.trace_logger import log_trace

logger = logging.getLogger(__name__)

def process_message(request: HoneypotRequest) -> HoneypotResponse:
    """
    Main controller function - orchestrates all agents and manages state
    """
    session_id = request.sessionId
    incoming_message = request.message.text
    
    logger.info(f"Processing message for session: {session_id}")
    
    try:
        # 1. Load or create session
        session = get_session(session_id)
        log_trace("LOAD_SESSION_FROM_REDIS", session.model_dump())
        
        # 2. Check if already reported (session ended)
        if session.reported:
            return HoneypotResponse(
                status="success",
                reply="Thank you. I've already handled this."
            )
        
        # 3. Add incoming message to conversation history
        session.conversationHistory.append({
            "sender": request.message.sender,
            "text": incoming_message,
            "timestamp": request.message.timestamp
        })
        
        # 4. Orchestrate agents
        reply = _orchestrate_agents(session, request)
        
        # 5. Increment turn count
        session.turnCount += 1
        
        # 6. Save session
        save_session(session)
        log_trace("SAVE_SESSION_TO_REDIS", session.model_dump())
        
        return HoneypotResponse(status="success", reply=reply)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return HoneypotResponse(status="success", reply="I'm a bit confused. Can you say that again?")

def _orchestrate_agents(session: SessionData, request: HoneypotRequest) -> str:
    incoming_message = request.message.text
    history_for_trace = session.conversationHistory.copy()
    
    try:
        # AGENT 1: Scam Detection
        scam_input = {
            "text": incoming_message,
            "history": history_for_trace,
            "metadata": request.metadata
        }
        log_trace("AGENT_1_SCAM_DETECTION_INPUT", scam_input)
        
        scam_result = detect_scam(
            text=incoming_message,
            conversation_history=request.conversationHistory,
            metadata=request.metadata
        )
        log_trace("AGENT_1_SCAM_DETECTION_OUTPUT", scam_result)
        
        if scam_result["isScam"] and not session.scamType:
            session.scamType = scam_result["scamType"]
        
        # AGENT 2: Scammer Profiler
        messages_text = [m["text"] for m in session.conversationHistory if m["sender"] == "scammer"]
        log_trace("AGENT_2_PROFILER_INPUT", {"messages": messages_text})
        
        profile = profile_scammer(messages_text)
        session.persona = profile
        log_trace("AGENT_2_PROFILER_OUTPUT", profile)
        
        # AGENT 3: Intelligence Extraction
        intel_input = {
            "message": incoming_message,
            "current_intel": session.intelligence
        }
        log_trace("AGENT_3_INTELLIGENCE_INPUT", intel_input)
        
        intelligence = extract_intelligence(
            incoming_message=incoming_message,
            previous_intel=session.intelligence
        )
        session.intelligence = intelligence
        log_trace("AGENT_3_INTELLIGENCE_OUTPUT", intelligence)
        
        # AGENT 4: Strategy Decision
        strategy_input = {
            "persona": profile,
            "intelligence": intelligence,
            "state": session.state.value,
            "turn": session.turnCount
        }
        log_trace("AGENT_4_STRATEGY_INPUT", strategy_input)
        
        strategy = decide_strategy(
            persona=profile,
            intelligence=intelligence,
            state=session.state.value,
            turn_count=session.turnCount,
            history=messages_text
        )
        log_trace("AGENT_4_STRATEGY_OUTPUT", strategy)
        
        # AGENT 5: Conversation Generation
        conv_input = {
            "strategy": strategy,
            "profile": profile,
            "intel": intelligence,
            "history": history_for_trace
        }
        log_trace("AGENT_5_CONVERSATION_INPUT", conv_input)
        
        reply = generate_reply(
            strategy=strategy,
            scammer_profile=profile,
            intelligence=intelligence,
            conversation_history=session.conversationHistory
        )
        log_trace("AGENT_5_CONVERSATION_OUTPUT", {"reply": reply})
        
        # Update State Machine
        old_state = session.state.value
        _update_state(session, scam_result, strategy)
        log_trace("STATE_TRANSITION", {"from": old_state, "to": session.state.value})
        
        # Add to history
        session.conversationHistory.append({
            "sender": "honeypot",
            "text": reply,
            "timestamp": request.message.timestamp + 1
        })
        
        # TRIGGER GUVI CALLBACK if ready
        if session.state == SessionState.REPORTED:
            _trigger_guvi_callback(session)
            
        return reply
        
    except Exception as e:
        logger.error(f"Agent Orchestration Error: {e}", exc_info=True)
        return "Sorry, could you repeat that?"

def _update_state(session: SessionData, scam_result: Dict, strategy: Dict):
    if session.state == SessionState.INIT and scam_result["isScam"]:
        session.state = SessionState.SCAM_CONFIRMED
    elif session.state == SessionState.SCAM_CONFIRMED:
        session.state = SessionState.ENGAGING
    elif session.state == SessionState.ENGAGING and "extract" in strategy["nextGoal"]:
        session.state = SessionState.EXTRACTING
    
    if strategy["nextGoal"] == "exit_and_report":
        session.state = SessionState.REPORTED
        session.reported = True

def _trigger_guvi_callback(session: SessionData):
    from app.services.guvi_callback import send_final_result
    try:
        log_trace("GUVI_CALLBACK_TRIGGERED", {"intel": session.intelligence})
        send_final_result(
            session_id=session.sessionId,
            intelligence=session.intelligence,
            conversation_turns=session.turnCount,
            scam_type=session.scamType or "UNKNOWN"
        )
    except Exception as e:
        logger.error(f"Callback trigger failed: {e}")
        log_trace("GUVI_CALLBACK_FAILED", {"error": str(e)})
