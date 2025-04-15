import logging
import json
from typing import Dict, List, Any, Optional
import re 

logger = logging.getLogger(__name__)

def sanitize_input(text: str) -> str:
    """
    Sanitize user input by removing any potentially harmful characters.
    
    Args:
        text: The input text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove any HTML/XML tags
    import re
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove any script tags and their contents
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    return text

def detect_language(text: str) -> str:
    """
    Detect if the text is in Hebrew or English.
    
    Args:
        text: The input text
        
    Returns:
        Language code ('he' for Hebrew, 'en' for English)
    """
    # Check if the text contains Hebrew characters
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    if hebrew_pattern.search(text):
        return 'he'
    else:
        return 'en'

def format_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Format an error response.
    
    Args:
        error_message: Error message
        status_code: HTTP status code
        
    Returns:
        Formatted error response dictionary
    """
    return {
        "status": "error",
        "status_code": status_code,
        "message": error_message
    }

def extract_user_info_from_llm_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to extract structured user information from LLM responses.
    This is a fallback method if the LLM doesn't provide structured data.
    
    Args:
        response_text: The text response from the LLM
        
    Returns:
        Dictionary of user information or None if extraction failed
    """
    try:
        # Look for JSON-like structure in the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Fallback: Look for key-value pairs in the text
        info = {}
        
        # Look for name
        name_match = re.search(r'name:?\s*([^\n]+)', response_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                info['first_name'] = name_parts[0]
                info['last_name'] = ' '.join(name_parts[1:])
        
        # Look for ID number
        id_match = re.search(r'id(?:\s*number)?:?\s*(\d{9})', response_text, re.IGNORECASE)
        if id_match:
            info['id_number'] = id_match.group(1)
        
        # Look for gender
        gender_match = re.search(r'gender:?\s*(\w+)', response_text, re.IGNORECASE)
        if gender_match:
            gender = gender_match.group(1).lower()
            if gender in ['male', 'זכר']:
                info['gender'] = 'male'
            elif gender in ['female', 'נקבה']:
                info['gender'] = 'female'
            else:
                info['gender'] = 'other'
        
        # Look for age
        age_match = re.search(r'age:?\s*(\d+)', response_text, re.IGNORECASE)
        if age_match:
            info['age'] = int(age_match.group(1))
        
        # Look for HMO
        hmo_match = re.search(r'hmo:?\s*([^\n]+)', response_text, re.IGNORECASE)
        if hmo_match:
            hmo = hmo_match.group(1).strip()
            info['hmo'] = hmo
        
        # Look for HMO card number
        card_match = re.search(r'card(?:\s*number)?:?\s*(\d{9})', response_text, re.IGNORECASE)
        if card_match:
            info['hmo_card_number'] = card_match.group(1)
        
        # Look for insurance tier
        tier_match = re.search(r'tier:?\s*([^\n]+)', response_text, re.IGNORECASE)
        if tier_match:
            tier = tier_match.group(1).strip()
            info['insurance_tier'] = tier
        
        # Return None if we couldn't extract critical fields
        required_fields = ['first_name', 'last_name', 'id_number', 'gender', 'age', 'hmo', 'hmo_card_number', 'insurance_tier']
        if not all(field in info for field in required_fields):
            logger.warning("Could not extract all required user information fields")
            return None
        
        return info
        
    except Exception as e:
        logger.error(f"Error extracting user info from LLM response: {str(e)}")
        return None