# backend/routers/extraction.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from backend.services.azure_openai import get_openai_service

logger = logging.getLogger(__name__)
router = APIRouter()

class ExtractionRequest(BaseModel):
    text: str
    
class ExtractionResponse(BaseModel):
    user_info: Dict[str, Any]
    is_complete: bool

@router.post("/extract_user_info", response_model=ExtractionResponse)
async def extract_user_info(request: ExtractionRequest):
    """
    Extract user information from text using LLM.
    """
    try:
        service = get_openai_service()
        user_info = await service.extract_user_info(request.text)
        is_complete = service.is_user_info_complete(user_info)
        
        logger.info(f"User info extraction complete. Is complete: {is_complete}")
        
        return ExtractionResponse(
            user_info=user_info,
            is_complete=is_complete
        )
    except Exception as e:
        logger.error(f"Error in extract_user_info endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error extracting user information: {str(e)}")

class ConfirmationRequest(BaseModel):
    message: str
    language: str = "en"

class ConfirmationResponse(BaseModel):
    is_confirmation: bool

@router.post("/confirm_intent", response_model=ConfirmationResponse)
async def check_confirmation(request: ConfirmationRequest):
    """
    Check if a message is confirming information.
    """
    try:
        logger.info(f"Checking confirmation for message: '{request.message}' in language: {request.language}")
        
        # Simple rule-based approach
        confirmation_phrases = {
            "en": ["yes", "correct", "confirm", "accurate", "right", "ok", "sure", "looks good"],
            "he": ["כן", "נכון", "מאשר", "מאשרת", "אישור", "הכל נכון", "הכל בסדר", "אוקיי", "אוקי"]
        }
        
        language = request.language
        if language not in confirmation_phrases:
            language = "en"  # Default to English
            
        message_lower = request.message.lower().strip()
        logger.info(f"Checking message '{message_lower}' against phrases: {confirmation_phrases[language]}")
        
        # Check for exact matches (e.g., "yes", "כן")
        if message_lower in confirmation_phrases[language]:
            logger.info(f"Exact match found for '{message_lower}'")
            return ConfirmationResponse(is_confirmation=True)
        
        # Check for phrases within the message
        for phrase in confirmation_phrases[language]:
            if phrase in message_lower:
                logger.info(f"Phrase '{phrase}' found in message")
                return ConfirmationResponse(is_confirmation=True)
        
        # If no confirmation phrases found, it's not a confirmation
        logger.info(f"No confirmation phrases found in message")
        return ConfirmationResponse(is_confirmation=False)
    except Exception as e:
        logger.error(f"Error in confirm_intent endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking confirmation: {str(e)}")
    

class DirectExtractionRequest(BaseModel):
    message: str
    language: str = "en"

class DirectExtractionResponse(BaseModel):
    user_info: Dict[str, Any]
    is_complete: bool
    success: bool

@router.post("/direct_extract", response_model=DirectExtractionResponse)
async def direct_extract(request: DirectExtractionRequest):
    """
    Directly extract and process user information from a message.
    This is a simplified approach that works when a user provides all their information at once.
    """
    try:
        message = request.message
        language = request.language
        
        logger.info(f"Attempting direct extraction for {language} message of length {len(message)}")
        
        # Use our existing extraction service
        service = get_openai_service()
        user_info = await service.extract_user_info(message)
        is_complete = service.is_user_info_complete(user_info)
        
        # Log the result
        fields_found = list(user_info.keys())
        logger.info(f"Direct extraction found fields: {fields_found}")
        logger.info(f"Is information complete: {is_complete}")
        
        return DirectExtractionResponse(
            user_info=user_info,
            is_complete=is_complete,
            success=is_complete and len(user_info) >= 7  # At least 7 fields should be present
        )
    except Exception as e:
        logger.error(f"Error in direct extraction: {str(e)}", exc_info=True)
        return DirectExtractionResponse(
            user_info={},
            is_complete=False,
            success=False
        )
        
