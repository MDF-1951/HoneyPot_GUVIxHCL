import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class ExitPhase(str, Enum):
    CONTINUE = "CONTINUE"
    SOFT_EXIT = "SOFT_EXIT"
    CONTROLLED_BREAKDOWN = "CONTROLLED_BREAKDOWN"
    TERMINATE = "TERMINATE"

class ExitDecision(BaseModel):
    should_exit: bool
    exit_phase: ExitPhase
    reason: str
    metrics: Dict[str, float] = {}

def evaluate(session: Any, intelligence: Dict[str, Any], strategy: Dict[str, Any]) -> ExitDecision:
    """
    Computes exit signals and decides on the conversation phase.
    """
    turn_count = session.turnCount
    history = session.conversationHistory
    
    # 1. Compute Signals
    repetition_signal = _calculate_repetition(history)
    intel_saturation = _calculate_intel_saturation(intelligence)
    frustration_signal = _calculate_frustration(history)
    
    metrics = {
        "repetition": repetition_signal,
        "intel_saturation": intel_saturation,
        "frustration": frustration_signal,
        "turns": float(turn_count)
    }
    
    # 2. Hard Limits (Fail-safes)
    if turn_count >= 20:
        return ExitDecision(
            should_exit=True,
            exit_phase=ExitPhase.TERMINATE,
            reason="Maximum turn limit reached",
            metrics=metrics
        )

    # 3. Intelligence Based Exit
    # If we have UPI/Bank/Phone and it's been a few turns, we've won.
    if intel_saturation > 0.8 and turn_count > 10:
        return ExitDecision(
            should_exit=True,
            exit_phase=ExitPhase.SOFT_EXIT,
            reason="Intelligence goals achieved",
            metrics=metrics
        )

    # 4. Stress/Repetition Based Exit (Psychological Realism)
    if repetition_signal > 0.7 or frustration_signal > 0.8:
        # If the scammer is repeating or getting very aggressive, the victim "breaks down"
        return ExitDecision(
            should_exit=True,
            exit_phase=ExitPhase.CONTROLLED_BREAKDOWN,
            reason="Scammer aggression or circular loop detected",
            metrics=metrics
        )

    # 5. Check Strategy's internal exit flag
    if strategy.get("nextGoal") == "exit_and_report":
        return ExitDecision(
            should_exit=True,
            exit_phase=ExitPhase.SOFT_EXIT,
            reason="Strategy agent requested exit",
            metrics=metrics
        )

    return ExitDecision(
        should_exit=False,
        exit_phase=ExitPhase.CONTINUE,
        reason="Conversation in progress",
        metrics=metrics
    )

def _calculate_repetition(history: List[Dict[str, Any]]) -> float:
    """Calculates if the scammer is repeating themselves."""
    scammer_msgs = [m["text"].lower() for m in history if m["sender"] == "scammer"]
    if len(scammer_msgs) < 3:
        return 0.0
    
    last_msg = scammer_msgs[-1]
    similar_count = sum(1 for m in scammer_msgs[:-1] if last_msg in m or m in last_msg)
    
    return min(1.0, similar_count / 5.0)

def _calculate_intel_saturation(intelligence: Dict[str, Any]) -> float:
    """Calculates how much of the target info we've extracted."""
    found = intelligence.get("found", {})
    # Simple count of non-empty categories
    categories = ["upi_ids", "bank_accounts", "phone_numbers", "phishing_links"]
    found_count = sum(1 for cat in categories if found.get(cat))
    
    return found_count / len(categories)

def _calculate_frustration(history: List[Dict[str, Any]]) -> float:
    """Detects scammer frustration or urgency signals."""
    frustration_keywords = ["fast", "now", "hurry", "quick", "urgent", "police", "arrest", "blocked", "immediately"]
    scammer_msgs = [m["text"].lower() for m in history if m["sender"] == "scammer"]
    
    if not scammer_msgs:
        return 0.0
        
    latest = scammer_msgs[-1]
    matches = sum(1 for word in frustration_keywords if word in latest)
    
    return min(1.0, matches / 3.0)
