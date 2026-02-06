from fastapi import FastAPI
from app.api.honeypot import router as honeypot_router
from app.api.health import router as health_router
from app.utils.logging_config import setup_logging

# Setup logging
setup_logging()

app = FastAPI(title="Agentic Honeypot API")

# Register routes
app.include_router(honeypot_router, prefix="/honeypot", tags=["honeypot"])
app.include_router(health_router, prefix="/health", tags=["health"])
