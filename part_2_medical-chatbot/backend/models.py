from pydantic import BaseModel, Field, validator
import re
from typing import List, Optional, Dict, Any
from enum import Enum

class Language(str, Enum):
    ENGLISH = "en"
    HEBREW = "he"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class HMO(str, Enum):
    MACCABI = "מכבי"
    MEUHEDET = "מאוחדת"
    CLALIT = "כללית"

class InsuranceTier(str, Enum):
    GOLD = "זהב"
    SILVER = "כסף"
    BRONZE = "ארד"

class UserInformation(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    id_number: str = Field(..., min_length=9, max_length=9)
    gender: Gender
    age: int = Field(..., ge=0, le=120)
    hmo: HMO
    hmo_card_number: str = Field(..., min_length=9, max_length=9)
    insurance_tier: InsuranceTier
    language: Language = Language.ENGLISH

    @validator('id_number', 'hmo_card_number')
    def validate_numeric_field(cls, v):
        if not v.isdigit():
            raise ValueError("Must contain only digits")
        return v
    
    @validator('id_number')
    def validate_id_number(cls, v):
        # Israeli ID validation - simple version
        if not v.isdigit() or len(v) != 9:
            raise ValueError("ID number must be 9 digits")
        return v

class Message(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    messages: List[Message] = []

class ChatRequest(BaseModel):
    user_info: Optional[UserInformation] = None
    chat_history: ChatHistory = Field(default_factory=ChatHistory)
    message: str
    language: Language = Language.ENGLISH

class ChatResponse(BaseModel):
    response: str
    updated_chat_history: ChatHistory