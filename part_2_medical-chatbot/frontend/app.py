import streamlit as st
import requests
import json
import os
import sys
from typing import Dict, List, Any, Optional
import time

# Add the parent directory to path so we can import the backend models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.models import UserInformation, ChatHistory, Message, Language

# API Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# App title and configuration
st.set_page_config(
    page_title="Medical Services Chatbot",
    page_icon="🏥",
    layout="centered",
)

# Initialize session state for chat history and user info
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "information_phase_complete" not in st.session_state:
    st.session_state.information_phase_complete = False

# Helper function to call the backend API
def call_chat_api(message: str) -> Dict[str, Any]:
    """
    Call the chat API with the given message.
    
    Args:
        message: The user message
        
    Returns:
        The API response
    """
    try:
        # Create the request payload
        payload = {
            "message": message,
            "language": st.session_state.language
        }
        
        # Add chat history if available
        if st.session_state.chat_history:
            payload["chat_history"] = {
                "messages": st.session_state.chat_history
            }
        
        # Add user info if available
        if st.session_state.user_info:
            payload["user_info"] = st.session_state.user_info
        
        # Make the API request
        response = requests.post(
            f"{API_URL}/api/chat/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Handle errors
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            st.error(error_msg)
            return {"error": error_msg}
        
        return response.json()
        
    except Exception as e:
        error_msg = f"Error calling API: {str(e)}"
        st.error(error_msg)
        return {"error": error_msg}

# Function to check if user information is complete
def is_user_info_complete() -> bool:
    """
    Check if the user info session state contains complete information.
    
    Returns:
        True if user info is complete, False otherwise
    """
    if not st.session_state.user_info:
        return False
    
    required_fields = [
        "first_name", "last_name", "id_number", "gender", 
        "age", "hmo", "hmo_card_number", "insurance_tier"
    ]
    
    return all(field in st.session_state.user_info for field in required_fields)

# Function to parse and extract user information from LLM response
def extract_user_info(message: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to extract user information from an LLM response message.
    This is a basic implementation - extend as needed.
    
    Args:
        message: The LLM response message
        
    Returns:
        Extracted user information or None
    """
    try:
        # Look for a JSON block in the message
        import re
        json_match = re.search(r'\{.*\}', message, re.DOTALL)
        if json_match:
            try:
                user_info = json.loads(json_match.group(0))
                return user_info
            except json.JSONDecodeError:
                pass
        
        # Fallback to text parsing if JSON not found
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

# Function to check if a message indicates user info confirmation
def is_confirmation_message(message: str) -> bool:
    """
    Check if a message indicates that the user has confirmed their information.
    
    Args:
        message: The message to check
        
    Returns:
        True if confirmation message, False otherwise
    """
    confirmation_phrases = [
        "information is correct",
        "information looks good",
        "information is accurate",
        "details are correct",
        "all correct",
        "yes, that's correct",
        "המידע נכון",
        "הפרטים נכונים",
        "yes",
        "confirm",
        "מאשר",
        "כן"
    ]
    
    return any(phrase in message.lower() for phrase in confirmation_phrases)

# App header
def render_header():
    """Render the app header."""
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://www.health.gov.il/Style%20Library/images/logo.png", width=80)
    with col2:
        st.title("Medical Services Chatbot")
    
    # Language selector
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

# Main app UI
def main():
    """Main application function."""
    # Render the header
    render_header()
    
    # Divider
    st.divider()
    
    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Display user message
        st.chat_message("user").write(prompt)
        
        # Add message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Show thinking indicator
        with st.spinner("Thinking..."):
            # Call the chat API
            response = call_chat_api(prompt)
            
            if "error" in response:
                st.error(response["error"])
            else:
                # Display assistant response
                st.chat_message("assistant").write(response["response"])
                
                # Update chat history
                st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
                
                # Check if we are in the information phase and the response contains confirmation
                if not st.session_state.information_phase_complete:
                    # If user confirms information, check if we can extract user info
                    if is_confirmation_message(prompt):
                        # Look for user info in previous messages
                        for i in range(len(st.session_state.chat_history) - 2, -1, -2):
                            if st.session_state.chat_history[i]["role"] == "assistant":
                                user_info = extract_user_info(st.session_state.chat_history[i]["content"])
                                if user_info:
                                    st.session_state.user_info = user_info
                                    st.session_state.information_phase_complete = True
                                    
                                    # Notify that we're moving to Q&A phase
                                    if st.session_state.language == "en":
                                        st.success("Information collection complete! You can now ask questions about medical services.")
                                    else:
                                        st.success("איסוף המידע הושלם! כעת תוכל לשאול שאלות על שירותים רפואיים.")
                                    
                                    break

# Run the app
if __name__ == "__main__":
    main()