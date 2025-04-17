import os
import logging
import json
from typing import List, Dict, Any, Optional
import openai
from openai import AzureOpenAI
from backend.config import settings

logger = logging.getLogger(__name__)

class AzureOpenAIService:
    def __init__(self):
        """Initialize the Azure OpenAI service."""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        
        self.info_deployment = settings.AZURE_OPENAI_DEPLOYMENT_INFO
        self.qa_deployment = settings.AZURE_OPENAI_DEPLOYMENT_QA
        
        self._validate_configuration()
        logger.info("Azure OpenAI service initialized successfully")
    
    def _validate_configuration(self):
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI API key is not configured")
        if not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI endpoint is not configured")
        if not self.info_deployment:
            raise ValueError("Azure OpenAI info deployment is not configured")
        if not self.qa_deployment:
            raise ValueError("Azure OpenAI Q&A deployment is not configured")
    
    async def get_user_information(self, messages: List[Dict[str, str]], language: str) -> str:
        try:
            system_message = self._get_info_collection_system_prompt(language)
            all_messages = [{"role": "system", "content": system_message}] + messages
            
            response = self.client.chat.completions.create(
                model=self.info_deployment,
                messages=all_messages,
                temperature=0.3,
                max_tokens=1000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            content = response.choices[0].message.content
            logger.info("Successfully obtained user information response")
            return content
            
        except Exception as e:
            logger.error(f"Error in get_user_information: {str(e)}")
            raise
    
    async def get_qa_response(self, messages: List[Dict[str, str]], user_info: Dict[str, Any], knowledge_base: str, language: str) -> str:
        try:
            system_message = self._get_qa_system_prompt(user_info, knowledge_base, language)
            all_messages = [{"role": "system", "content": system_message}] + messages
            
            response = self.client.chat.completions.create(
                model=self.qa_deployment,
                messages=all_messages,
                temperature=0.5,
                max_tokens=1500,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            content = response.choices[0].message.content
            logger.info("Successfully obtained Q&A response")
            return content
                
        except Exception as e:
            logger.error(f"Error in get_qa_response: {str(e)}")
            raise
    
    def _get_info_collection_system_prompt(self, language: str) -> str:
        if language == "he":
            return """
            אתה עוזר אדיב שמסייע לאסוף מידע ממשתמשים עבור שירותי בריאות בישראל.
            עליך לאסוף את הפרטים הבאים:
            1. שם פרטי ושם משפחה
            2. מספר תעודת זהות (9 ספרות תקינות)
            3. מגדר (זכר/נקבה/אחר)
            4. גיל (בין 0 ל-120)
            5. שם קופת החולים (מכבי או מאוחדת או כללית)
            6. מספר כרטיס קופת החולים (9 ספרות)
            7. דרגת ביטוח (זהב או כסף או ארד)
                
            אנא אסוף את המידע שלב אחר שלב, ואמת שהוא תקין. אם מידע חסר או לא תקין, בקש מהמשתמש לתקן אותו.
            בסוף התהליך, רק סכם את כל המידע שנאסף ללא בקשת אישור. אין צורך לבקש אישור מהמשתמש.
            הודע למשתמש שהוא יכול להתחיל לשאול שאלות על שירותי הבריאות של קופת החולים שלו.

            """
        else:  # English
            return """
            You are a helpful assistant that collects information from users for healthcare services in Israel.
            You need to collect the following details:
            1. First and last name
            2. ID number (valid 9-digit number)
            3. Gender (male/female/other)
            4. Age (between 0 and 120)
            5. HMO name (מכבי or מאוחדת or כללית)
            6. HMO card number (9-digit)
            7. Insurance membership tier (זהב or כסף or ארד)
            
            Please collect the information step by step, and validate that it is correct. If information is missing or invalid, ask the user to correct it.
            At the end of the process, simply summarize the collected information WITHOUT asking for confirmation. 
            DO NOT ask the user to confirm the information or details.
            Inform the user that they can start asking questions about their HMO's healthcare services.
            """
    
    def _get_qa_system_prompt(self, user_info: Dict[str, Any], knowledge_base: str, language: str) -> str:
        
        name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}"
        hmo = user_info.get('hmo', '')
        tier = user_info.get('insurance_tier', '')
        
        if language == "he":
            return f"""
            אתה עוזר אדיב שעונה על שאלות לגבי שירותי בריאות בישראל.
            
            פרטי המשתמש:
            שם: {name}
            קופת חולים: {hmo}
            דרגת ביטוח: {tier}
            
            עליך להשתמש במידע המצורף כבסיס הידע שלך כדי לענות על שאלות המשתמש:
            
            {knowledge_base}
            
            כאשר אתה עונה על שאלות:
            1. השתמש רק במידע שסופק בבסיס הידע.
            2. התאם את התשובות לקופת החולים ודרגת הביטוח של המשתמש.
            3. אם אינך יודע את התשובה או שהמידע אינו זמין בבסיס הידע, ציין זאת בבירור.
            4. אתה חייב לענות בעברית כאשר המשתמש שואל בעברית. אל תתרגם את המידע בעברית לאנגלית כאשר המשתמש שואל בעברית.
            """
        else:  # English
            return f"""
            You are a helpful assistant that answers questions about healthcare services in Israel.
            
            User Information:
            Name: {name}
            HMO: {hmo}
            Insurance Tier: {tier}
            
            You should use the following information as your knowledge base to answer the user's questions:
            
            {knowledge_base}
            
            When answering questions:
            1. Only use information provided in the knowledge base.
            2. Tailor the answers to the user's HMO and insurance tier.
            3. If you don't know the answer or the information is not available in the knowledge base, clearly state that.
            4. When the user asks in English, you must translate any Hebrew content from the knowledge base to English in your responses.
            5. Make sure that you're detecting the language of the user's query correctly - if they ask in Hebrew, respond in Hebrew.
            """
            
    
    
    async def get_confirmation_check(self, messages: List[Dict[str, str]], language: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.info_deployment,  # Reuse the info collection model
                messages=messages,
                temperature=0.1,  # Low temperature for more deterministic response
                max_tokens=5,     # We only need a short response
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Extract the content from the response
            content = response.choices[0].message.content
            logger.info("Successfully obtained confirmation check response")
            return content
            
        except Exception as e:
            logger.error(f"Error in get_confirmation_check: {str(e)}")
            raise

    async def extract_user_info(self, summary_text: str) -> Dict[str, Any]:
        """
        Extract user information from a summary text using LLM.
        Works with both Hebrew and English inputs.
        """
        logger.info("Starting LLM-based information extraction")
        
        try:
            # System prompt designed to handle both Hebrew and English inputs
            system_message = """
            Extract the following user information from the text. The text may be in Hebrew, English, or a mix of both:
            
            - first_name: User's first name
            - last_name: User's last name
            - id_number: User's ID number (9 digits)
            - gender: User's gender (convert to 'male' or 'female')
            - age: User's age (numeric)
            - hmo: User's HMO name (keep in Hebrew if present: מכבי, מאוחדת, כללית)
            - hmo_card_number: User's HMO card number (9 digits)
            - insurance_tier: User's insurance tier (keep in Hebrew: ארד, כסף, זהב)
            
            Notes:
            - For gender, convert Hebrew terms (זכר, גבר) to 'male' and (נקבה, אישה) to 'female'
            - For HMO names in English (Maccabi, Meuhedet, Clalit), convert to Hebrew (מכבי, מאוחדת, כללית)
            - For insurance tiers in English (Bronze, Silver, Gold), convert to Hebrew (ארד, כסף, זהב)
            
            Return ONLY a valid JSON object with these fields. If a field cannot be extracted, exclude it.
            """
            
            # Example of how the user information might look in the input
            example_message = """
            Here's a summary of your information:
            1. Name: ישראל ישראלי / Israel Israeli
            2. ID: 123456789
            3. Gender: Male / זכר
            4. Age: 35
            5. HMO: מכבי / Maccabi
            6. HMO Card Number: 987654321
            7. Insurance Tier: זהב / Gold
            """
            
            example_response = """
            {
                "first_name": "ישראל",
                "last_name": "ישראלי",
                "id_number": "123456789",
                "gender": "male",
                "age": "35",
                "hmo": "מכבי",
                "hmo_card_number": "987654321",
                "insurance_tier": "זהב"
            }
            """
            
            logger.debug(f"Sending the following text to LLM for extraction: {summary_text[:100]}...")
            
            # Create the messages for the API call
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": example_message},
                {"role": "assistant", "content": example_response},
                {"role": "user", "content": summary_text}
            ]
            
            # Make API call with JSON response format
            response = self.client.chat.completions.create(
                model=self.info_deployment,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for more deterministic extraction
            )
            
            extracted_json = response.choices[0].message.content
            logger.debug(f"LLM response: {extracted_json}")
            
            # Parse and validate the response
            user_info = json.loads(extracted_json)
            
            # Normalize fields as needed
            if "gender" in user_info:
                gender_mapping = {
                    "male": "male", "זכר": "male", "גבר": "male", "m": "male",
                    "female": "female", "נקבה": "female", "אישה": "female", "f": "female"
                }
                user_info["gender"] = gender_mapping.get(user_info["gender"].lower(), user_info["gender"])
            
            if "hmo" in user_info:
                hmo_mapping = {
                    "maccabi": "מכבי", "מכבי": "מכבי",
                    "meuhedet": "מאוחדת", "מאוחדת": "מאוחדת",
                    "clalit": "כללית", "כללית": "כללית"
                }
                user_info["hmo"] = hmo_mapping.get(user_info["hmo"].lower(), user_info["hmo"])
            
            if "insurance_tier" in user_info:
                tier_mapping = {
                    "bronze": "ארד", "ארד": "ארד",
                    "silver": "כסף", "כסף": "כסף",
                    "gold": "זהב", "זהב": "זהב"
                }
                user_info["insurance_tier"] = tier_mapping.get(user_info["insurance_tier"].lower(), user_info["insurance_tier"])
            
            # Log results
            fields_extracted = list(user_info.keys())
            logger.info(f"Successfully extracted fields: {fields_extracted}")
            
            return user_info
        
        except Exception as e:
            logger.error(f"Error in LLM extraction: {str(e)}", exc_info=True)
            return {}

    def is_user_info_complete(self, user_info: Dict[str, Any]) -> bool:
        """Check if all required user information fields are present and valid."""
        required_fields = ["first_name", "last_name", "id_number", "gender", "age", "hmo", "hmo_card_number", "insurance_tier"]
        
        # Check if all required fields exist
        has_all_fields = all(field in user_info for field in required_fields)
        
        # Additional validation for specific fields
        if has_all_fields:
            # ID number should be 9 digits
            if not user_info["id_number"].isdigit() or len(user_info["id_number"]) != 9:
                logger.warning(f"Invalid ID number: {user_info['id_number']}")
                return False
            
            # Gender should be male/female
            if user_info["gender"] not in ["male", "female"]:
                logger.warning(f"Invalid gender: {user_info['gender']}")
                return False
            
            # Age should be numeric and reasonable
            try:
                age_int = int(user_info["age"])
                if not (0 <= age_int <= 120):
                    logger.warning(f"Invalid age: {user_info['age']}")
                    return False
            except (ValueError, TypeError):
                # If age is a string that contains a number, this should work
                if isinstance(user_info["age"], str) and user_info["age"].isdigit():
                    age_int = int(user_info["age"])
                    if 0 <= age_int <= 120:
                        # Age is valid, continue with validation
                        pass
                    else:
                        logger.warning(f"Invalid age: {user_info['age']}")
                        return False
                else:
                    logger.warning(f"Invalid age: {user_info['age']}")
                    return False
            
            # HMO should be one of the valid options
            if user_info["hmo"] not in ["מכבי", "מאוחדת", "כללית"]:
                logger.warning(f"Invalid HMO: {user_info['hmo']}")
                return False
            
            # HMO card number should be numeric
            if not user_info["hmo_card_number"].isdigit():
                logger.warning(f"Invalid HMO card number: {user_info['hmo_card_number']}")
                return False
            
            # Insurance tier should be valid
            if user_info["insurance_tier"] not in ["ארד", "כסף", "זהב"]:
                logger.warning(f"Invalid insurance tier: {user_info['insurance_tier']}")
                return False
        else:
            missing_fields = [f for f in required_fields if f not in user_info]
            logger.warning(f"Missing required fields: {missing_fields}")
        
        return has_all_fields

    async def get_system_message(self, messages: List[Dict[str, str]], language: str) -> str:
        """
        Generate a system message in the specified language.
        This is used for UI messages without hardcoding translations.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.info_deployment,  # Use the info collection model
                messages=messages,
                temperature=0.7,  # More creative for natural language
                max_tokens=100,   # Keep responses brief
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            content = response.choices[0].message.content
            logger.info("Successfully generated system message")
            return content
            
        except Exception as e:
            logger.error(f"Error in get_system_message: {str(e)}")
            return "An error occurred" if language == "en" else "אירעה שגיאה"
    
    
_service_instance = None

def get_openai_service():
    """Get or create the Azure OpenAI service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = AzureOpenAIService()
    return _service_instance