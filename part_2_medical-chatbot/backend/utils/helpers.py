import logging
import json
from typing import Dict, List, Any, Optional
import re 

logger = logging.getLogger(__name__)

def sanitize_input(text: str) -> str:
    if not text:
        return ""
    
    text = re.sub(r'<[^>]*>', '', text) 
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text)
    text = text.strip()
    
    return text

def detect_language(text: str) -> str:
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]') ## acording to my ASCII table
    if hebrew_pattern.search(text):
        return 'he'
    else:
        return 'en'

def format_error_response(error_message: str, status_code: int = 400) -> Dict[str, Any]:
    return {
        "status": "error",
        "status_code": status_code,
        "message": error_message
    }

def extract_user_info_from_llm_response(response_text: str) -> Optional[Dict[str, Any]]:
    ## I already extract the info in a json format in the frontend app.py file. But I want to make sure it's in a json foramt,
    ## because different browsers might handle regex and JSON parsing slightly differently
    ## and also for security reasons 
    try:
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                json_str = json_match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        info = {}
        
        name_match = re.search(r'name:?\s*([^\n]+)', response_text, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                info['first_name'] = name_parts[0]
                info['last_name'] = ' '.join(name_parts[1:])
        
        id_match = re.search(r'id(?:\s*number)?:?\s*(\d{9})', response_text, re.IGNORECASE)
        if id_match:
            info['id_number'] = id_match.group(1)
        
        gender_match = re.search(r'gender:?\s*(\w+)', response_text, re.IGNORECASE)
        if gender_match:
            gender = gender_match.group(1).lower()
            if gender in ['male', 'זכר']:
                info['gender'] = 'male'
            elif gender in ['female', 'נקבה']:
                info['gender'] = 'female'
            else:
                info['gender'] = 'other'
        
        age_match = re.search(r'age:?\s*(\d+)', response_text, re.IGNORECASE)
        if age_match:
            info['age'] = int(age_match.group(1))
        
        hmo_match = re.search(r'hmo:?\s*([^\n]+)', response_text, re.IGNORECASE)
        if hmo_match:
            hmo = hmo_match.group(1).strip()
            info['hmo'] = hmo
        
        card_match = re.search(r'card(?:\s*number)?:?\s*(\d{9})', response_text, re.IGNORECASE)
        if card_match:
            info['hmo_card_number'] = card_match.group(1)
        
        tier_match = re.search(r'tier:?\s*([^\n]+)', response_text, re.IGNORECASE)
        if tier_match:
            tier = tier_match.group(1).strip()
            info['insurance_tier'] = tier
        
        required_fields = ['first_name', 'last_name', 'id_number', 'gender', 'age', 'hmo', 'hmo_card_number', 'insurance_tier']
        if not all(field in info for field in required_fields):
            logger.warning("Could not extract all required user information fields")
            return None
        
        return info
        
    except Exception as e:
        logger.error(f"Error extracting user info from LLM response: {str(e)}")
        return None