import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class NextGoal(str, Enum):
    EXTRACT_UPI = "extract_upi"
    EXTRACT_LINK = "extract_link"
    EXTRACT_PHONE = "extract_phone"
    DELAY = "delay"
    FORCE_REPETITION = "force_repetition"
    EXIT_AND_REPORT = "exit_and_report"

class Method(str, Enum):
    CONFUSED_COMPLIANCE = "confused_compliance"
    CLARIFICATION = "clarification"
    DELAY = "delay"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass(frozen=True)
class StrategyDecision:
    nextGoal: NextGoal
    method: Method
    riskLevel: RiskLevel

@dataclass(frozen=True)
class StrategyConfig:
    max_turns: int = 12
    repetition_threshold: int = 3
    minimum_required_intel: int = 2
    actionable_keys: tuple[str, ...] = ("upi_ids", "phone_numbers", "bank_accounts")
    safety_keywords: tuple[str, ...] = (
        "install", "download", "click", "call immediately", 
        "remote access", "anydesk", "teamviewer"
    )

class StrategyAgent:
    def __init__(self, config: Optional[StrategyConfig] = None) -> None:
        self._config: StrategyConfig = config or StrategyConfig()

    def decide(
        self,
        persona: Dict[str, Any],
        intelligence: Dict[str, Any],
        session_state: str,
        turn_count: int,
        recent_messages: Optional[List[str]] = None,
    ) -> StrategyDecision:
        
        # 1. Safety override
        if self._detect_high_risk(intelligence):
            return StrategyDecision(NextGoal.EXIT_AND_REPORT, Method.DELAY, RiskLevel.HIGH)

        # 2. Sufficient intelligence
        if self._has_sufficient_intelligence(intelligence):
            return StrategyDecision(NextGoal.EXIT_AND_REPORT, Method.DELAY, RiskLevel.LOW)

        # 3. Turn limit
        if turn_count >= self._config.max_turns:
            return StrategyDecision(NextGoal.EXIT_AND_REPORT, Method.DELAY, RiskLevel.MEDIUM)

        # 4. Loop detection
        if recent_messages and self._is_repetition_detected(recent_messages):
            return self._alternate_extraction_strategy(intelligence)

        # 5. Normal strategy
        return self._normal_extraction_strategy(intelligence)

    def _has_sufficient_intelligence(self, intelligence: Dict[str, Any]) -> bool:
        # Note: teammate code used "found" key, while intelligence.py now returns flat dict
        # I will handle both or adapt to the new format
        count = 0
        for key in self._config.actionable_keys:
            count += len(intelligence.get(key, []))
        
        return count >= self._config.minimum_required_intel

    def _detect_high_risk(self, intelligence: Dict[str, Any]) -> bool:
        tactics = intelligence.get("tactics", [])
        for tactic in tactics:
            lowered = tactic.lower()
            for keyword in self._config.safety_keywords:
                if keyword in lowered:
                    return True
        return False

    def _is_repetition_detected(self, messages: List[str]) -> bool:
        if len(messages) < self._config.repetition_threshold:
            return False
        normalized = [msg.strip().lower() for msg in messages[-self._config.repetition_threshold:]]
        return len(set(normalized)) == 1

    def _normal_extraction_strategy(self, intelligence: Dict[str, Any]) -> StrategyDecision:
        missing = intelligence.get("missing_info", [])
        
        if "upi_id" in missing:
            return StrategyDecision(NextGoal.EXTRACT_UPI, Method.CONFUSED_COMPLIANCE, RiskLevel.LOW)
        if "phishing_link" in missing:
            return StrategyDecision(NextGoal.EXTRACT_LINK, Method.CLARIFICATION, RiskLevel.MEDIUM)
        if "phone_number" in missing:
            return StrategyDecision(NextGoal.EXTRACT_PHONE, Method.CLARIFICATION, RiskLevel.MEDIUM)

        return StrategyDecision(NextGoal.DELAY, Method.DELAY, RiskLevel.LOW)

    def _alternate_extraction_strategy(self, intelligence: Dict[str, Any]) -> StrategyDecision:
        missing = intelligence.get("missing_info", [])
        if "phone_number" in missing:
            return StrategyDecision(NextGoal.EXTRACT_PHONE, Method.CLARIFICATION, RiskLevel.MEDIUM)
        return StrategyDecision(NextGoal.EXIT_AND_REPORT, Method.DELAY, RiskLevel.MEDIUM)

def decide_strategy(persona: Dict, intelligence: Dict, state: str, turn_count: int, history: List[str]) -> Dict:
    agent = StrategyAgent()
    decision = agent.decide(persona, intelligence, state, turn_count, history)
    return {
        "nextGoal": decision.nextGoal.value,
        "method": decision.method.value,
        "riskLevel": decision.riskLevel.value
    }
