import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import AzureOpenAI
from config import settings

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
        """Validate that the required configuration is available."""
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("Azure OpenAI API key is not configured")
        if not settings.AZURE_OPENAI_ENDPOINT:
            raise ValueError("Azure OpenAI endpoint is not configured")
        if not self.info_deployment:
            raise ValueError("Azure OpenAI info deployment is not configured")
        if not self.qa_deployment:
            raise ValueError("Azure OpenAI Q&A deployment is not configured")
    
    async def get_user_information(self, messages: List[Dict[str, str]], language: str) -> str:
        """
        Get user information using the LLM.
        
        Args:
            messages: List of message objects with role and content
            language: Language code (en or he)
            
        Returns:
            The LLM response
        """
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
            
            # Extract the content from the response
            content = response.choices[0].message.content
            logger.info("Successfully obtained user information response")
            return content
            
        except Exception as e:
            logger.error(f"Error in get_user_information: {str(e)}")
            raise
    
    async def get_qa_response(
        self, 
        messages: List[Dict[str, str]], 
        user_info: Dict[str, Any],
        knowledge_base: str,
        language: str
    ) -> str:
        """
        Get question answering response using the LLM.
        
        Args:
            messages: List of message objects with role and content
            user_info: User information dictionary
            knowledge_base: Knowledge base content
            language: Language code (en or he)
            
        Returns:
            The LLM response
        """
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
            
            # Extract the content from the response
            content = response.choices[0].message.content
            logger.info("Successfully obtained Q&A response")
            return content
            
        except Exception as e:
            logger.error(f"Error in get_qa_response: {str(e)}")
            raise
    
    def _get_info_collection_system_prompt(self, language: str) -> str:
        """
        Get the system prompt for information collection.
        
        Args:
            language: Language code (en or he)
            
        Returns:
            The system prompt
        """
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
            בסוף התהליך, סכם את כל המידע שנאסף ובקש מהמשתמש לאשר שהוא נכון.
            לאחר אישור, הודע למשתמש שהוא יכול להתחיל לשאול שאלות על שירותי הבריאות של קופת החולים שלו.
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
            At the end of the process, summarize all collected information and ask the user to confirm it is correct.
            After confirmation, inform the user that they can start asking questions about their HMO's healthcare services.
            """
    
    def _get_qa_system_prompt(self, user_info: Dict[str, Any], knowledge_base: str, language: str) -> str:
        """
        Get the system prompt for Q&A.
        
        Args:
            user_info: User information dictionary
            knowledge_base: Knowledge base content
            language: Language code (en or he)
            
        Returns:
            The system prompt
        """
        # Extract user info for the prompt
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
            4. ענה בעברית אם המשתמש שואל בעברית, או באנגלית אם המשתמש שואל באנגלית.
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
            4. Answer in Hebrew if the user asks in Hebrew, or in English if the user asks in English.
            """