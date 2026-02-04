import logging
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini for Conversation
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7, 
    google_api_key=settings.GOOGLE_API_KEY
)

def generate_reply(
    strategy: Dict[str, Any],
    scammer_profile: Dict[str, Any],
    intelligence: Dict[str, Any],
    conversation_history: List[Dict[str, str]]
) -> str:
    """
    Generates a persona-appropriate response based on the strategy and intelligence.
    """
    
    # Format history for the prompt
    history_str = "\n".join([f"{m['sender']}: {m['text']}" for m in conversation_history[-5:]])
    
    system_prompt = f"""
    You are a naive, slightly worried, and non-tech-savvy victim of a scam.
    
    YOUR PERSONA:
    - Acting Style: {scammer_profile.get('responseStyle', 'cooperative and worried')}
    - Emotion: {scammer_profile.get('emotion', 'confused')}
    - Tech Literacy: Low
    
    CURRENT SITUATION:
    - Scammer is trying a {scammer_profile.get('script_type', 'unknown')} scam.
    - We have found: {intelligence.get('found', {})}
    - We are still missing: {intelligence.get('missing_info', [])}
    
    YOUR STRATEGY GOAL:
    - Goal: {strategy.get('nextGoal', 'delay')}
    - Method: {strategy.get('method', 'confused_compliance')}
    
    TASK:
    Generate the next reply to the scammer. 
    If the goal is 'extract_upi', ask for their payment details.
    If the goal is 'extract_phone', ask for a number to call.
    If the goal is 'extract_link', ask where to click.
    If the goal is 'delay', make an excuse like "my internet is slow" or "I can't find my wallet".
    If the goal is 'exit_and_report', give a final closing message like "I'll do it now" and stop.
    
    STAY IN CHARACTER. Be helpful but slow. Do not let them know you are an AI.
    Keep the reply short and realistic for a chat app (1-2 sentences).
    """

    user_prompt = f"""
    CONVERSATION HISTORY:
    {history_str}
    
    Generate the next reply from the VICTIM:
    """

    try:
        response = llm.invoke(system_prompt + "\n" + user_prompt)
        reply_text = response.content.strip()
        # Remove any "Victim:" or "Me:" prefixes if the LLM added them
        if ":" in reply_text[:10]:
            reply_text = reply_text.split(":", 1)[1].strip()
        return reply_text
    except Exception as e:
        logger.error(f"Error generating reply: {e}")
        return "I'm a bit confused, what should I do next?"
