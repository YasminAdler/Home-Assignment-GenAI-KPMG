from fastapi import APIRouter, HTTPException, Depends, Request, status
import logging
from typing import Dict

from models import ChatRequest, ChatResponse, Message, ChatHistory
from services.azure_openai import AzureOpenAIService
from services.knowledge_base import KnowledgeBaseService

logger = logging.getLogger(__name__)

router = APIRouter()

openai_service = AzureOpenAIService()
knowledge_base_service = KnowledgeBaseService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history.messages
        ]
        
        formatted_messages.append({"role": "user", "content": request.message})
        
        if not request.user_info:
            logger.info("Processing information collection phase")
            response_content = await openai_service.get_user_information(
                formatted_messages, 
                request.language
            )
        else:
            # Q&A Phase
            logger.info(f"Processing Q&A phase for HMO: {request.user_info.hmo}")
            
            knowledge_base = knowledge_base_service.get_knowledge_for_hmo(request.user_info.hmo)
            
            if not knowledge_base:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Knowledge base for HMO {request.user_info.hmo} not found"
                )
            
            response_content = await openai_service.get_qa_response(
                formatted_messages,
                request.user_info.dict(),
                knowledge_base,
                request.language
            )
        
        updated_history = ChatHistory(
            messages=request.chat_history.messages + [
                Message(role="user", content=request.message),
                Message(role="assistant", content=response_content)
            ]
        )
        
        return ChatResponse(
            response=response_content,
            updated_chat_history=updated_history
        )
        
    except HTTPException as e:
        logger.error(f"HTTP exception in chat endpoint: {str(e)}")
        raise
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
        

@router.post("/confirm_intent", response_model=Dict[str, bool])
async def confirm_intent(request: Request):
    try:
        data = await request.json()
        message = data.get("message", "")
        language = data.get("language", "en")
        
        if not message:
            return {"is_confirmation": False}
        
        # System prompt for confirmation detection
        system_prompt = """
        Your task is to determine if a user message is confirming their personal information.
        Analyze the intent of the message and respond with ONLY "true" if the message appears to be 
        confirming information, or "false" if it does not.
        
        Examples of confirmation messages:
        - "Yes, that's correct"
        - "The information looks good"
        - "כן, הפרטים נכונים" (Hebrew: "Yes, the details are correct")
        
        Examples of non-confirmation messages:
        - "I have a question"
        - "That's not right"
        - "What services does my insurance cover?"
        """
        
        user_prompt = f"""
        The user has been providing their personal information for healthcare services.
        The system has summarized their information and asked them to confirm if it's correct.
        
        The user's response is: "{message}"
        
        Is this a confirmation of their information? Respond with ONLY the word "true" or "false".
        """
        
        formatted_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_content = await openai_service.get_confirmation_check(
            formatted_messages, 
            language
        )
        
        response_text = response_content.strip().lower()
        is_confirmation = response_text == "true"
        
        logger.info(f"Confirmation check: '{message}' -> {is_confirmation}")
        
        return {"is_confirmation": is_confirmation}
        
    except Exception as e:
        logger.error(f"Error in confirmation check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during confirmation check: {str(e)}"
        )