"""
Test script for the honeypot system
Tests the complete flow without needing Redis or GUVI
"""
import json
import time
from app.models.session import HoneypotRequest, MessageData
from app.core.controller import process_message

def test_conversation_flow():
    """Test a complete scam conversation flow"""
    
    print("=" * 60)
    print("HONEYPOT SYSTEM TEST")
    print("=" * 60)
    
    session_id = f"test-session-{int(time.time())}" # Use unique ID to avoid 'Already Reported' skip
    
    print(f"Session ID: {session_id}")
    
    # Optional: Clear redis for this ID if it exists
    try:
        import redis
        from app.core.config import settings
        r = redis.from_url(settings.REDIS_URL)
        r.delete(f"session:{session_id}")
    except:
        pass
    
    # Simulate a realistic scammer conversation flow
    messages = [
        "Hello! I am calling from your bank's security department. Your account is frozen due to suspicious activity.",
        "To unblock your account, we need to verify your identity. Please send 1 rupee to our security UPI ID.",
        "The security UPI ID is bank.verify@okaxis. This is just for verification.",
        "Did you send it? We also need you to install our security app from this link: http://bank-secure.apk",
        "Please provide your phone number so our manager can guide you through the final steps.",
        "Are you there? This is very urgent or your funds will be lost forever!",
        "If you don't cooperate, we will have to report this to the police.",
        "Final warning: send the confirmation to bank.verify@okaxis or your account is gone.",
    ]
    
    conversation_history = []
    
    for i, msg in enumerate(messages, 1):
        time.sleep(2)  # Delay to avoid rate limiting
        print(f"\n{'='*60}")
        print(f"TURN {i}")
        print(f"{'='*60}")
        print(f"📨 INCOMING: {msg}")
        
        # Create request
        request = HoneypotRequest(
            sessionId=session_id,
            message=MessageData(
                sender="scammer",
                text=msg,
                timestamp=1000000000 + i
            ),
            conversationHistory=conversation_history.copy(),
            metadata={}
        )
        
        # Process through controller
        response = process_message(request)
        
        print(f"🤖 REPLY: {response.reply}")
        print(f"📊 STATUS: {response.status}")
        
        # Add to history
        conversation_history.append({
            "sender": "scammer",
            "text": msg,
            "timestamp": 1000000000 + i
        })
        conversation_history.append({
            "sender": "honeypot",
            "text": response.reply,
            "timestamp": 1000000000 + i + 1
        })
        
        # Check if conversation ended
        if "go" in response.reply.lower() or "later" in response.reply.lower():
            print("\n⚠️  CONVERSATION ENDING DETECTED")
            break
    
    print(f"\n{'='*60}")
    print("TEST COMPLETED")
    print(f"{'='*60}")
    print(f"Total turns: {i}")
    print(f"Session ID: {session_id}")
    print("\n✅ System is working! Check logs above for:")
    print("  - State transitions (INIT → SCAM_CONFIRMED → ENGAGING → EXTRACTING)")
    print("  - Intelligence extraction (UPI IDs, phone numbers, URLs)")
    print("  - Persona evolution (confused → worried → scared)")
    print("  - Strategy decisions (extract_upi, extract_link, etc.)")

if __name__ == "__main__":
    test_conversation_flow()
