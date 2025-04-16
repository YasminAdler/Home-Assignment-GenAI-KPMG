import os
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import glob

from config import settings

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        self.knowledge_base_dir = settings.KNOWLEDGE_BASE_DIR
        self.service_data = {}  # changed from hmo_data
        self._load_knowledge_base()
        logger.info("Knowledge base service initialized successfully")

    def _load_knowledge_base(self):
        """Load and parse all HTML files in the knowledge base directory."""
        try:
            html_files = glob.glob(os.path.join(self.knowledge_base_dir, "*.html"))

            if not html_files:
                logger.warning(f"No HTML files found in {self.knowledge_base_dir}")
                return

            for file_path in html_files:
                try:
                    file_name = os.path.basename(file_path)
                    service_name = file_name.split('.')[0].lower()  # e.g., "dentel_services"

                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()

                    soup = BeautifulSoup(html_content, 'html.parser')
                    text_content = soup.get_text(separator='\n', strip=True)

                    self.service_data[service_name] = {
                        'text': text_content,
                        'html': html_content
                    }

                    logger.info(f"Loaded knowledge base file: {file_name}")

                except Exception as e:
                    logger.error(f"Error loading knowledge base file {file_path}: {str(e)}")

            logger.info(f"Loaded {len(self.service_data)} knowledge base files")

        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            raise

    def get_knowledge_for_service(self, service_name: str, format_type: str = 'text') -> Optional[str]:

        try:
            normalized_service = self._normalize_service_name(service_name)

            if normalized_service not in self.service_data:
                logger.warning(f"No knowledge base data found for service: {service_name}")
                return None

            return self.service_data[normalized_service][format_type]

        except Exception as e:
            logger.error(f"Error getting knowledge for service {service_name}: {str(e)}")
            return None

    def _normalize_service_name(self, name: str) -> str:

        return name.strip().lower().replace(" ", "_")

    def get_available_services(self) -> List[str]:
        """Return a list of all available service names."""
        return list(self.service_data.keys())
