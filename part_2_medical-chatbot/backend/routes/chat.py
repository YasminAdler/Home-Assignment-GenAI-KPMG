from fastapi import APIRouter, HTTPException, Depends, status
import logging
from typing import Dict, List, Optional

from models import ChatRequest, ChatResponse, Message, ChatHistory
from services.azure_openai import AzureOpenAIService
from services.knowledge_base import KnowledgeBaseService

logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances
openai_service = AzureOpenAIService()
knowledge_base_service = KnowledgeBaseService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return a response.
    If user_info is not provided, assume we're in the information collection phase.
    If user_info is provided, we're in the Q&A phase.
    """
    try:
        # Format the chat history for the Azure OpenAI API
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history.messages
        ]
        
        # Add the current message to the formatted messages
        formatted_messages.append({"role": "user", "content": request.message})
        
        # Determine the phase based on whether user_info is provided
        if not request.user_info:
            # Information Collection Phase
            logger.info("Processing information collection phase")
            response_content = await openai_service.get_user_information(
                formatted_messages, 
                request.language
            )
        else:
            # Q&A Phase
            logger.info(f"Processing Q&A phase for HMO: {request.user_info.hmo}")
            
            # Get the knowledge base for the user's HMO
            knowledge_base = knowledge_base_service.get_knowledge_for_hmo(request.user_info.hmo)
            
            if not knowledge_base:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Knowledge base for HMO {request.user_info.hmo} not found"
                )
            
            # Get the response from Azure OpenAI
            response_content = await openai_service.get_qa_response(
                formatted_messages,
                request.user_info.dict(),
                knowledge_base,
                request.language
            )
        
        # Add the assistant's response to the chat history
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
        # Re-raise HTTP exceptions
        logger.error(f"HTTP exception in chat endpoint: {str(e)}")
        raise
        
    except Exception as e:
        # Log and convert other exceptions to HTTPException
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )