import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.core.controller import process_message
from app.models.session import HoneypotRequest, MessageData
import time

# Mocking external agents if needed? 
# No, let's try to run it for real since they use Gemini and my API key should be in .env

def test_integration_exit():
    print("Testing Controller Integration with Exit Engine...")
    
    # 1. Normal turn
    req1 = HoneypotRequest(
        sessionId="integration_test_1",
        message=MessageData(sender="scammer", text="Hello", timestamp=int(time.time())),
        conversationHistory=[]
    )
    
    res1 = process_message(req1)
    print(f"Turn 1 Response: {res1.reply}")

    # 2. Simulate Repetition to trigger exit
    for i in range(6):
        req_rep = HoneypotRequest(
            sessionId="integration_test_1",
            message=MessageData(sender="scammer", text="PAY ME NOW FAST", timestamp=int(time.time())),
            conversationHistory=[]
        )
        res_rep = process_message(req_rep)
        print(f"Turn {i+2} Response: {res_rep.reply}")
        
        # Check if session is reported (ended)
        # We can't strictly check the session object here easily without loading from Redis
        # but we can see if the response changed to a breakdown response.
        
    print("Integration test finished.")

if __name__ == "__main__":
    test_integration_exit()
