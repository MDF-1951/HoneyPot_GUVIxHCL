from app.agents.exit_engine import evaluate, ExitPhase
from app.models.session import SessionData, SessionState
import json

def test_exit_engine_logic():
    print("Testing Exit Engine Logic...")
    
    # 1. Test Continue
    session = SessionData(sessionId="test_1", turnCount=5, conversationHistory=[
        {"sender": "scammer", "text": "hello"},
        {"sender": "honeypot", "text": "hi"},
        {"sender": "scammer", "text": "send money"}
    ])
    intel = {"found": {}, "missing": []}
    strategy = {"nextGoal": "extract_upi"}
    
    decision = evaluate(session, intel, strategy)
    print(f"Test 1 (Continue): {decision.exit_phase} - {'PASS' if decision.exit_phase == ExitPhase.CONTINUE else 'FAIL'}")

    # 2. Test Repetition -> Breakdown
    session_rep = SessionData(sessionId="test_2", turnCount=10, conversationHistory=[
        {"sender": "scammer", "text": "pay now"},
        {"sender": "scammer", "text": "pay now"},
        {"sender": "scammer", "text": "pay now"},
        {"sender": "scammer", "text": "pay now"},
        {"sender": "scammer", "text": "pay now"}
    ])
    decision_rep = evaluate(session_rep, intel, strategy)
    print(f"Test 2 (Repetition): {decision_rep.exit_phase} - {'PASS' if decision_rep.exit_phase == ExitPhase.CONTROLLED_BREAKDOWN else 'FAIL'}")

    # 3. Test Intel Saturation -> Soft Exit
    session_intel = SessionData(sessionId="test_3", turnCount=15, conversationHistory=[])
    intel_sat = {
        "found": {
            "upi_ids": ["test@upi"],
            "bank_accounts": ["1234567890"],
            "phone_numbers": ["9876543210"],
            "phishing_links": ["http://scam.com"]
        }
    }
    decision_intel = evaluate(session_intel, intel_sat, strategy)
    print(f"Test 3 (Saturation): {decision_intel.exit_phase} - {'PASS' if decision_intel.exit_phase == ExitPhase.SOFT_EXIT else 'FAIL'}")

    # 4. Test Frustration -> Breakdown
    session_frust = SessionData(sessionId="test_4", turnCount=5, conversationHistory=[
        {"sender": "scammer", "text": "POLICE WILL ARREST YOU NOW HURRY UP IMMEDIATELY"}
    ])
    decision_frust = evaluate(session_frust, intel, strategy)
    print(f"Test 4 (Frustration): {decision_frust.exit_phase} - {'PASS' if decision_frust.exit_phase == ExitPhase.CONTROLLED_BREAKDOWN else 'FAIL'}")

if __name__ == "__main__":
    test_exit_engine_logic()
