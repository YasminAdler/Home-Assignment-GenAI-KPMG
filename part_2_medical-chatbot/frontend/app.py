import streamlit as st
import requests
import json
import os
import sys
from typing import Dict, List, Any, Optional
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.models import UserInformation, ChatHistory, Message, Language

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Medical Services Chatbot",
    page_icon="🏥",
    layout="centered",
)

### Initialization 
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "information_phase_complete" not in st.session_state:
    st.session_state.information_phase_complete = False

def call_chat_api(message: str) -> Dict[str, Any]: # Create the request payload
    try:
        payload = {
            "message": message,
            "language": st.session_state.language
        }
        
        if st.session_state.chat_history:
            payload["chat_history"] = {
                "messages": st.session_state.chat_history
            }
        
        if st.session_state.user_info:
            payload["user_info"] = st.session_state.user_info
        
        response = requests.post(     
            f"{API_URL}/api/chat/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
### errors handeling: 
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            st.error(error_msg)
            return {"error": error_msg}
        
        return response.json()
        
    except Exception as e:
        error_msg = f"Error calling API: {str(e)}"
        st.error(error_msg)
        return {"error": error_msg}

def is_user_info_complete() -> bool: ## I want to make sure that all data was collected before moving to the Q&A phase 
    if not st.session_state.user_info:
        return False
    
    required_fields = [
        "first_name", "last_name", "id_number", "gender", 
        "age", "hmo", "hmo_card_number", "insurance_tier"
    ]
    
    for field in required_fields:
        if field not in st.session_state.user_info:
            return False
    return True

def extract_user_info(message: str) -> Optional[Dict[str, Any]]: ## extracts the user info out of the llm response 
    try:
        import re
        json_match = re.search(r'\{.*\}', message, re.DOTALL)
        if json_match:
            try:
                user_info = json.loads(json_match.group(0))
                return user_info
            except json.JSONDecodeError:
                pass
        user_info = {}
        
# Extract first and last name
        name_match = re.search(r'Name:?\s*([^\n]+)', message, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = full_name.split()
            if len(name_parts) >= 2:
                user_info['first_name'] = name_parts[0]
                user_info['last_name'] = ' '.join(name_parts[1:])
        
# Extract other fields (simplified example)
        id_match = re.search(r'ID Number:?\s*(\d{9})', message, re.IGNORECASE)
        if id_match:
            user_info['id_number'] = id_match.group(1)
        
        gender_match = re.search(r'Gender:?\s*(\w+)', message, re.IGNORECASE)
        if gender_match:
            user_info['gender'] = gender_match.group(1).lower()
        
        age_match = re.search(r'Age:?\s*(\d+)', message, re.IGNORECASE)
        if age_match:
            user_info['age'] = int(age_match.group(1))
        
        hmo_match = re.search(r'HMO:?\s*([^\n]+)', message, re.IGNORECASE)
        if hmo_match:
            user_info['hmo'] = hmo_match.group(1).strip()
        
        card_match = re.search(r'HMO Card Number:?\s*(\d{9})', message, re.IGNORECASE)
        if card_match:
            user_info['hmo_card_number'] = card_match.group(1)
        
        tier_match = re.search(r'Insurance Tier:?\s*([^\n]+)', message, re.IGNORECASE)
        if tier_match:
            user_info['insurance_tier'] = tier_match.group(1).strip()
        
# Check if we have all required fields
        required_fields = ["first_name", "last_name", "id_number", "gender", "age", "hmo", "hmo_card_number", "insurance_tier"]
        if all(field in user_info for field in required_fields):
            return user_info
        
        return None
        
    except Exception as e:
        st.error(f"Error extracting user info: {str(e)}")
        return None

def check_confirmation(message: str) -> bool:
    try:
        payload = {
            "message": message,
            "language": st.session_state.language
        }
        
        response = requests.post(
            f"{API_URL}/api/chat/confirm_intent",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Handle errors
        if response.status_code != 200:
            st.error(f"Confirmation check error: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        return result.get("is_confirmation", False)
        
    except Exception as e:
        st.error(f"Error checking confirmation: {str(e)}")
        # Fall back to simple keyword check if API fails
        simple_keywords = ["yes", "correct", "confirm", "כן", "נכון", "מאשר"]
        return any(keyword in message.lower() for keyword in simple_keywords)

def render_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://www.health.gov.il/Style%20Library/images/logo.png", width=80)
    with col2:
        st.title("Medical Services Chatbot")
    
    language_options = {"English": "en", "עברית": "he"}
    selected_language = st.radio(
        "Select Language / בחר שפה",
        options=list(language_options.keys()),
        horizontal=True,
    )
    st.session_state.language = language_options[selected_language]
    
    if st.session_state.language == "en":
        st.markdown("### Welcome to the Israeli Health Funds Information System")
        st.markdown("This chatbot will help you get information about medical services based on your HMO and insurance tier.")
    else:
        st.markdown("### ברוכים הבאים למערכת המידע של קופות החולים בישראל")
        st.markdown("צ'אטבוט זה יעזור לך לקבל מידע על שירותים רפואיים בהתאם לקופת החולים ורמת הביטוח שלך.")

def main():
    render_header()
    
    st.divider()
    
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("user").write(prompt)
        
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.spinner("Just a sec! I'm thinking..."):
            response = call_chat_api(prompt)
            
            if "error" in response:
                st.error(response["error"])
            else:
                st.chat_message("assistant").write(response["response"])
                
                st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
                
                if not st.session_state.information_phase_complete:
                    is_confirming = check_confirmation(prompt)
                    
                    if is_confirming:
                        for i in range(len(st.session_state.chat_history) - 2, -1, -2):
                            if st.session_state.chat_history[i]["role"] == "assistant":
                                user_info = extract_user_info(st.session_state.chat_history[i]["content"])
                                if user_info:
                                    # Verify the user info is complete
                                    st.session_state.user_info = user_info
                                    if is_user_info_complete():
                                        st.session_state.information_phase_complete = True
                                        
                                        # Notify that we're moving to Q&A phase
                                        if st.session_state.language == "en":
                                            st.success("Information collection complete! You can now ask questions about medical services.")
                                        else:
                                            st.success("איסוף המידע הושלם! כעת תוכל לשאול שאלות על שירותים רפואיים.")
                                    else:
                                        if st.session_state.language == "en":
                                            st.warning("Some information appears to be missing. Please provide complete information.")
                                        else:
                                            st.warning("חלק מהמידע חסר. אנא השלם את כל המידע הנדרש.")
                                    break

# Run the app
if __name__ == "__main__":
    main()