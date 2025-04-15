import os
import tempfile
from typing import Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

class DocumentProcessor:
    
    def __init__(self, endpoint: str, key: str):
        self.endpoint = endpoint
        self.credential = AzureKeyCredential(key)
        self.client = DocumentIntelligenceClient(endpoint=self.endpoint, credential=self.credential)
    
    def process_document(self, file_content: bytes, file_extension: str) -> Dict[str, Any]:
        try:
            with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            with open(temp_file_path, "rb") as file:
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-layout",
                    body=file
                )
                result = poller.result()
            
            os.unlink(temp_file_path)
            
            ocr_result = {
                "content": result.content,
                "pages": [],
                "tables": [],
                "language": self._detect_language(result.content)
            }
            
            for page in result.pages:
                page_info = {
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "unit": page.unit,
                    "lines": [{"content": line.content, "bounding_box": line.polygon} for line in page.lines],
                    "words": [{"content": word.content, "confidence": word.confidence} for word in page.words]
                }
                ocr_result["pages"].append(page_info)
            
            for table in result.tables:
                table_info = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": [
                        {
                            "row_index": cell.row_index,
                            "column_index": cell.column_index,
                            "content": cell.content,
                            "bounding_box": cell.bounding_regions[0].polygon if cell.bounding_regions else None
                        } for cell in table.cells
                    ]
                }
                ocr_result["tables"].append(table_info)
            
            return ocr_result
            
        except Exception as e:
            raise
    
    def _detect_language(self, text: str) -> str:
        hebrew_chars = sum(1 for char in text if '\u0590' <= char <= '\u05FF')
        english_chars = sum(1 for char in text if 'a' <= char.lower() <= 'z')
        
        if hebrew_chars > english_chars * 0.5:
            return "he"
        return "en"