"""
Application dependencies for dependency injection.
"""
import os
import logging
from functools import lru_cache
from typing import Optional

from backend.services.knowledge_base import KnowledgeBaseService
from backend.config import KNOWLEDGE_BASE_DIR

logger = logging.getLogger(__name__)

@lru_cache()
def get_knowledge_base_service() -> KnowledgeBaseService:
    """
    Factory function for KnowledgeBaseService.
    This is cached so only one instance is created.
    """
    logger.info(f"Creating KnowledgeBaseService with dir: {KNOWLEDGE_BASE_DIR}")
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        logger.error(f"Knowledge base directory doesn't exist: {KNOWLEDGE_BASE_DIR}")
        # Create directory if it doesn't exist
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        logger.info(f"Created knowledge base directory: {KNOWLEDGE_BASE_DIR}")
        
    # Check for HTML files
    html_files = [f for f in os.listdir(KNOWLEDGE_BASE_DIR) if f.endswith('.html')]
    logger.info(f"Found {len(html_files)} HTML files in knowledge base directory")
    
    # Create service
    service = KnowledgeBaseService()
    
    # Validate service has data
    if hasattr(service, 'hmo_data') and service.hmo_data:
        logger.info(f"KnowledgeBaseService loaded with {len(service.hmo_data)} HMOs")
    else:
        logger.warning("KnowledgeBaseService initialized but no HMO data was loaded")
        
    return service

