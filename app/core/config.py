from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str
    ENV: str = "development"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""
    SESSION_TTL: int = 3600  # 1 hour session timeout
    
    # GUVI Configuration
    GUVI_API_KEY: str = ""
    GUVI_CALLBACK_URL: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # AI Model Keys
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    
    # Session Configuration
    MAX_TURNS: int = 15  # Maximum conversation turns before forcing exit

    class Config:
        env_file = ".env"

settings = Settings()
