import json
import os
from datetime import datetime

TRACE_LOG_FILE = "agent_trace.log"

def log_trace(step_name: str, data: dict):
    """
    Logs a detailed trace of agent interactions and Redis state to agent_trace.log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(TRACE_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{timestamp}] STEP: {step_name}\n")
        f.write(f"{'='*80}\n")
        f.write(json.dumps(data, indent=2))
        f.write("\n")

def clear_trace():
    """Clears the trace file if it exists"""
    if os.path.exists(TRACE_LOG_FILE):
        os.remove(TRACE_LOG_FILE)
