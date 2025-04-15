import os
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import glob

from config import settings

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        """Initialize the knowledge base service."""
        self.knowledge_base_dir = settings.KNOWLEDGE_BASE_DIR
        self.hmo_data = {}
        self._load_knowledge_base()
        logger.info("Knowledge base service initialized successfully")
    
    def _load_knowledge_base(self):
        """Load and parse all HTML files in the knowledge base directory."""
        try:
            # Get all HTML files in the knowledge base directory
            html_files = glob.glob(os.path.join(self.knowledge_base_dir, "*.html"))
            
            if not html_files:
                logger.warning(f"No HTML files found in {self.knowledge_base_dir}")
                return
            
            for file_path in html_files:
                try:
                    # Extract the HMO name from the filename
                    file_name = os.path.basename(file_path)
                    hmo_name = file_name.split('.')[0]  # Assumes filename format is "hmo_name.html"
                    
                    # Read and parse the HTML file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Parse the HTML using BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract the text content
                    text_content = soup.get_text(separator='\n', strip=True)
                    
                    # Store the content in the hmo_data dictionary
                    self.hmo_data[hmo_name] = {
                        'text': text_content,
                        'html': html_content
                    }
                    
                    logger.info(f"Loaded knowledge base file: {file_name}")
                    
                except Exception as e:
                    logger.error(f"Error loading knowledge base file {file_path}: {str(e)}")
            
            logger.info(f"Loaded {len(self.hmo_data)} knowledge base files")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            raise
    
    def get_knowledge_for_hmo(self, hmo_name: str, format_type: str = 'text') -> Optional[str]:
        """
        Get knowledge base content for a specific HMO.
        
        Args:
            hmo_name: Name of the HMO
            format_type: 'text' or 'html'
            
        Returns:
            Knowledge base content or None if not found
        """
        try:
            # Normalize HMO name for lookup
            normalized_hmo = self._normalize_hmo_name(hmo_name)
            
            # Check if we have data for this HMO
            if normalized_hmo not in self.hmo_data:
                logger.warning(f"No knowledge base data found for HMO: {hmo_name}")
                return None
            
            # Return the requested format
            if format_type == 'html':
                return self.hmo_data[normalized_hmo]['html']
            else:
                return self.hmo_data[normalized_hmo]['text']
                
        except Exception as e:
            logger.error(f"Error getting knowledge for HMO {hmo_name}: {str(e)}")
            return None
    
    def _normalize_hmo_name(self, hmo_name: str) -> str:
        """
        Normalize the HMO name for consistent lookup.
        
        Args:
            hmo_name: Name of the HMO
            
        Returns:
            Normalized HMO name
        """
        # This is a simple implementation - you may need to enhance it based on your file naming convention
        hmo_mapping = {
            'מכבי': 'maccabi',
            'מאוחדת': 'meuhedet',
            'כללית': 'clalit'
        }
        
        # Check if the input is already in English
        if hmo_name.lower() in ['maccabi', 'meuhedet', 'clalit']:
            return hmo_name.lower()
        
        # Otherwise, try to map from Hebrew
        return hmo_mapping.get(hmo_name, hmo_name.lower())