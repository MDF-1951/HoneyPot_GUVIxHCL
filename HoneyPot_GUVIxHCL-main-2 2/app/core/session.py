"""
Session management with Redis persistence
"""
import json
import logging
from typing import Optional
import redis
from app.core.config import settings
from app.models.session import SessionData, SessionState

logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = None

try:
    if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
        from upstash_redis import Redis
        redis_client = Redis(
            url=settings.UPSTASH_REDIS_REST_URL,
            token=settings.UPSTASH_REDIS_REST_TOKEN
        )
        logger.info("Upstash Redis connection established")
    else:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        # Test connection
        redis_client.ping()
        logger.info("Standard Redis connection established")
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")
    redis_client = None

# In-memory fallback for when Redis is unavailable
_memory_store: dict = {}


def _get_session_key(session_id: str) -> str:
    """Generate Redis key for session"""
    return f"session:{session_id}"


def get_session(session_id: str) -> SessionData:
    """
    Load session from Redis or create new session
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        SessionData object (existing or new)
    """
    try:
        if redis_client:
            # Try to load from Redis
            key = _get_session_key(session_id)
            data = redis_client.get(key)
            
            if data:
                if isinstance(data, str):
                    session_dict = json.loads(data)
                else:
                    session_dict = data
                return SessionData(**session_dict)
        else:
            # Fallback to in-memory store
            if session_id in _memory_store:
                return SessionData(**_memory_store[session_id])
                
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {e}")
    
    # Create new session if not found or error occurred
    logger.info(f"Creating new session: {session_id}")
    return SessionData(sessionId=session_id)


def save_session(session: SessionData) -> bool:
    """
    Save session to Redis with TTL
    
    Args:
        session: SessionData object to persist
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        session_dict = session.model_dump()
        
        if redis_client:
            # Save to Redis with TTL
            key = _get_session_key(session.sessionId)
            redis_client.setex(
                key,
                settings.SESSION_TTL,
                json.dumps(session_dict)
            )
            logger.debug(f"Session {session.sessionId} saved to Redis")
            return True
        else:
            # Fallback to in-memory store
            _memory_store[session.sessionId] = session_dict
            logger.debug(f"Session {session.sessionId} saved to memory")
            return True
            
    except Exception as e:
        logger.error(f"Error saving session {session.sessionId}: {e}")
        return False


def delete_session(session_id: str) -> bool:
    """
    Delete session from Redis (for cleanup/testing)
    
    Args:
        session_id: Session to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        if redis_client:
            key = _get_session_key(session_id)
            redis_client.delete(key)
        else:
            _memory_store.pop(session_id, None)
        
        logger.info(f"Session {session_id} deleted")
        return True
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        return False
