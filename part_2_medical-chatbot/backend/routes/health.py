from fastapi import APIRouter, HTTPException, status
import logging
from datetime import datetime
from typing import Dict, Any

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint to verify the API is up and running.
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "message": "Medical Services Chatbot API is running"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@router.get("/version")
async def version() -> Dict[str, Any]:
    """
    Version endpoint to get API version information.
    """
    try:
        return {
            "name": "Medical Services Chatbot API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Version check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Version check failed"
        )