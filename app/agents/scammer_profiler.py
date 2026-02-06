import re
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from groq import Groq
from app.core.config import settings

logger = logging.getLogger(__name__)

# =========================
# OUTPUT SCHEMA
# =========================
class ScammerPersona(BaseModel):
    age_range: str
    gender_likelihood: Dict[str, float]
    experience_level: str
    script_type: str
    region_hint: str
    aggression_level: float
    confidence: float

# =========================
# RULE-BASED LOGIC
# =========================
class RuleBasedProfiler:
    def run(self, messages: List[str]) -> ScammerPersona:
        features = self._extract_features(messages)
        experience = self._infer_experience(features)
        aggression = self._infer_aggression(features)
        script_type = self._infer_script_type(features)
        age_range = self._infer_age(experience, features)
        region_hint = self._infer_region(features)

        return ScammerPersona(
            age_range=age_range,
            gender_likelihood={"male": 0.7, "female": 0.3},
            experience_level=experience,
            script_type=script_type,
            region_hint=region_hint,
            aggression_level=aggression,
            confidence=self._infer_confidence(features)
        )

    def _extract_features(self, messages: List[str]) -> Dict:
        text = " ".join(messages).lower()
        return {
            "has_otp": "otp" in text or "one time password" in text,
            "has_kyc": "kyc" in text,
            "has_crypto": "crypto" in text or "wallet" in text,
            "has_job": "job" in text or "hr" in text,
            "has_delivery": "delivery" in text or "package" in text,
            "urgent_count": len(re.findall(r"\b(urgent|immediately|now|asap|today)\b", text)),
            "exclamation_count": text.count("!"),
            "threat_words": any(w in text for w in ["blocked", "suspended", "terminated", "legal action", "arrest"]),
            "formal_phrases": any(p in text for p in ["dear customer", "as per", "kindly", "regards"]),
            "emoji_count": len(re.findall(r"[\U0001F600-\U0001F64F]", text)),
            "link_present": "http" in text or "www" in text,
            "message_count": len(messages),
            "has_bank": any(k in text for k in ["bank", "account", "upi", "ifsc"]),
            "has_card": any(k in text for k in ["credit card", "debit card", "cvv", "expiry"]),
            "has_payment_app": any(k in text for k in ["gpay", "phonepe", "paytm", "paypal"]),
            "has_prize": any(k in text for k in ["won", "lottery", "reward", "prize"]),
            "has_loan": any(k in text for k in ["loan", "emi", "interest"]),
            "has_tax": any(k in text for k in ["tax", "gst", "income tax"]),
            "authority_claim": any(k in text for k in ["rbi", "government", "police", "customs", "income tax department"]),
            "short_link": any(k in text for k in ["bit.ly", "tinyurl", "t.co"]),
            "apk_reference": any(k in text for k in ["apk", "download app", "install app"]),
            "repetitive_messages": len(set(messages)) < len(messages),
            "avg_message_length": sum(len(m) for m in messages) / max(len(messages), 1),
            "grammar_errors": len(re.findall(r"\b[a-z]{1,2}\b", text)),
            "caps_abuse": sum(1 for c in text if c.isupper()) / max(len(text), 1),
            "mixed_language": any(w in text for w in ["please", "kripya", "aap"]),
        }

    def _infer_experience(self, f: Dict) -> str:
        if f["formal_phrases"] and f["urgent_count"] <= 1 and f["grammar_errors"] < 3:
            return "high"
        if f["exclamation_count"] > 3 or f["urgent_count"] > 2:
            return "low"
        return "medium"

    def _infer_script_type(self, f: Dict) -> str:
        scores = {"bank": 0, "hr": 0, "crypto": 0, "delivery": 0}
        if f["has_otp"]: scores["bank"] += 3
        if f["has_kyc"]: scores["bank"] += 2
        if f["has_bank"]: scores["bank"] += 2
        if f["has_card"]: scores["bank"] += 2
        if f["has_payment_app"]: scores["bank"] += 1
        if f["authority_claim"]: scores["bank"] += 1
        if f["has_job"]: scores["hr"] += 3
        if f["formal_phrases"]: scores["hr"] += 1
        if f["link_present"]: scores["hr"] += 1
        if f["has_crypto"]: scores["crypto"] += 3
        if f["short_link"]: scores["crypto"] += 1
        if f["emoji_count"] > 2: scores["crypto"] += 1
        if f["has_delivery"]: scores["delivery"] += 3
        if f["link_present"]: scores["delivery"] += 1
        if f["urgent_count"] > 0: scores["delivery"] += 1
        if f["mixed_language"]: scores["hr"] += 1
        if f["caps_abuse"] > 0.1: scores["crypto"] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] >= 3 else "unknown"

    def _infer_aggression(self, f: Dict) -> float:
        score = 0.0
        score += f["urgent_count"] * 0.2
        score += f["exclamation_count"] * 0.1
        score += 0.3 if f["threat_words"] else 0.0
        if f["caps_abuse"] > 0.1: score += 0.1
        return min(score, 1.0)

    def _infer_age(self, experience: str, f: Dict) -> str:
        if experience == "low" and f["emoji_count"] > 0:
            return "18-25"
        return "25-35"

    def _infer_region(self, f: Dict) -> str:
        if f["has_kyc"] or f["has_payment_app"]:
            return "South Asia"
        if f["has_tax"] and f["authority_claim"]:
            return "Government Impersonation"
        return "Unknown"

    def _infer_confidence(self, f: Dict) -> float:
        signal_strength = 0
        for key in ["has_otp", "formal_phrases", "urgent_count", "threat_words", "link_present"]:
            signal_strength += 1 if f.get(key) else 0
        return min(0.4 + signal_strength * 0.12, 0.9)

# =========================
# LLM-BASED LOGIC (Groq)
# =========================
class LLMProfiler:
    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY:
            self.client = Groq(api_key=settings.GROQ_API_KEY)

    def run(self, messages: List[str]) -> Optional[ScammerPersona]:
        if not self.client:
            return None
        try:
            conversation_text = "\n".join(messages)
            system_prompt = """
            You are an expert cyber-security analyst. Analyze the following conversation transcript.
            Infer the scammer's persona and return a JSON object strictly matching this schema:
            {
                "age_range": "string (e.g., '20-30')",
                "gender_likelihood": {"male": float, "female": float},
                "experience_level": "string (low, medium, or high)",
                "script_type": "string (e.g., bank, crypto, hr, tech_support)",
                "region_hint": "string (guessed geographic location)",
                "aggression_level": float (0.0 to 1.0),
                "confidence": float (0.0 to 1.0)
            }
            """
            chat_completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": conversation_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return ScammerPersona(**json.loads(chat_completion.choices[0].message.content))
        except Exception as e:
            logger.error(f"Error in LLM profiling: {e}")
            return None

# =========================
# HYBRID INTEGRATION
# =========================
def profile_scammer(messages: List[str]) -> Dict[str, Any]:
    rule_profiler = RuleBasedProfiler()
    llm_profiler = LLMProfiler()

    rule_persona = rule_profiler.run(messages)
    llm_persona = llm_profiler.run(messages)

    if not llm_persona:
        return rule_persona.model_dump()

    # Merge Logic
    def weighted_avg(v1, c1, v2, c2):
        if c1 + c2 == 0: return 0
        return (v1*c1 + v2*c2) / (c1 + c2)

    aggression = weighted_avg(
        rule_persona.aggression_level, rule_persona.confidence,
        llm_persona.aggression_level, llm_persona.confidence
    )

    def merge_category(rule_val, llm_val, rule_conf, llm_conf):
        return rule_val if rule_conf >= llm_conf else llm_val

    age_range = merge_category(rule_persona.age_range, llm_persona.age_range, rule_persona.confidence, llm_persona.confidence)
    experience_level = merge_category(rule_persona.experience_level, llm_persona.experience_level, rule_persona.confidence, llm_persona.confidence)
    script_type = merge_category(rule_persona.script_type, llm_persona.script_type, rule_persona.confidence, llm_persona.confidence)
    region_hint = merge_category(rule_persona.region_hint, llm_persona.region_hint, rule_persona.confidence, llm_persona.confidence)

    gender_likelihood = {}
    for g in ["male", "female"]:
        gender_likelihood[g] = weighted_avg(
            rule_persona.gender_likelihood[g], rule_persona.confidence,
            llm_persona.gender_likelihood[g], llm_persona.confidence
        )

    confidence = min(
        weighted_avg(rule_persona.confidence, rule_persona.confidence,
                     llm_persona.confidence, llm_persona.confidence),
        max(rule_persona.confidence, llm_persona.confidence)
    )

    return ScammerPersona(
        age_range=age_range,
        gender_likelihood=gender_likelihood,
        experience_level=experience_level,
        script_type=script_type,
        region_hint=region_hint,
        aggression_level=aggression,
        confidence=confidence
    ).model_dump()
