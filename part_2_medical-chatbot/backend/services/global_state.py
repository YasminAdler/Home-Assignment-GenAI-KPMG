"""
Global state for sharing service instances across the application.
"""

import logging
from typing import Optional
from backend.services.knowledge_base import KnowledgeBaseService


logger = logging.getLogger(__name__)

knowledge_base_service: Optional[KnowledgeBaseService] = None
