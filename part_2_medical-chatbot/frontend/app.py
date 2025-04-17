import streamlit as st
import requests
import os
import re
from typing import Dict, Any

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Medical Services Chatbot",
    page_icon="🏥",
    layout="centered",
)

# Initialization
for key, default in [
    ("chat_history", []),
    ("user_info", None),
    ("language", "en"),
    ("information_phase_complete", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def call_chat_api(message: str) -> Dict[str, Any]:
    payload = {
        "message": message,
        "language": st.session_state.language
    }

    if st.session_state.chat_history:
        payload["chat_history"] = {"messages": st.session_state.chat_history}

    if st.session_state.user_info and st.session_state.information_phase_complete:
        user_info = st.session_state.user_info
        print(f"✅ SENDING USER INFO TO API: {user_info}")
        payload["user_info"] = user_info
    else:
        print("❌ No user_info in payload - still in information collection phase")

    print(f"🔍 API Request payload: {payload}")

    response = requests.post(
        f"{API_URL}/api/chat/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        error_msg = f"API Error: {response.status_code} - {response.text}"
        print(f"❌ API ERROR: {error_msg}")
        st.error(error_msg)
        return {"error": error_msg}

    print(f"✅ API Response: {response.status_code}")
    return response.json()


def extract_user_info_api(text: str) -> Dict[str, Any]:
    """Extract user information using the backend API."""
    try:
        print(f"🔍 Sending text to extraction API: {text[:100]}...")
        
        payload = {"text": text}
        response = requests.post(
            f"{API_URL}/api/chat/extract_user_info",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            error_msg = f"API Error: {response.status_code} - {response.text}"
            print(f"❌ EXTRACTION API ERROR: {error_msg}")
            return {"error": error_msg}
        
        result = response.json()
        print(f"✅ Extraction API Response: {result}")
        
        if "user_info" in result:
            user_info = result["user_info"]
            required_fields = ["first_name", "last_name", "id_number", "gender", "age", "hmo", "hmo_card_number", "insurance_tier"]
            missing_fields = [field for field in required_fields if field not in user_info]
            
            if missing_fields:
                print(f"⚠️ Missing fields in extracted user info: {missing_fields}")
            else:
                print(f"✅ All required fields are present in user info")
        
        return result
    except Exception as e:
        print(f"❌ EXTRACTION API Exception: {str(e)}")
        return {"error": str(e)}


def check_confirmation_api(message: str) -> bool:
    """Check if a message is a confirmation using the API."""
    try:
        payload = {
            "message": message,
            "language": st.session_state.language
        }
        
        print(f"🔍 Checking confirmation for: '{message}' in language: {st.session_state.language}")
        
        response = requests.post(
            f"{API_URL}/api/chat/confirm_intent",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ CONFIRMATION API ERROR: {response.status_code} - {response.text}")
            return False
        
        result = response.json()
        is_confirmation = result.get("is_confirmation", False)
        print(f"✅ Confirmation API Response: is_confirmation={is_confirmation}")
        return is_confirmation
    except Exception as e:
        print(f"❌ CONFIRMATION API Exception: {str(e)}")
        return False


def process_information_directly(user_message: str) -> bool:
    """
    A direct approach to process user information without relying on complex detection.
    Returns True if successful, False otherwise.
    """
    # Check if the message contains all the required information fields
    required_fields = ["name", "id", "gender", "age", "hmo", "card", "tier"]
    
    # For Hebrew
    if any(hebrew_char in user_message for hebrew_char in "אבגדהוזחטיכלמנסעפצקרשת"):
        required_fields = ["שם", "תעודת", "מגדר", "גיל", "קופת", "כרטיס", "ביטוח"]
    
    # Simple check if message contains all required fields
    has_all_fields = all(field.lower() in user_message.lower() for field in required_fields)
    
    if not has_all_fields:
        print(f"❌ Message does not contain all required fields")
        return False
    
    # Extract user information directly
    try:
        print(f"🔍 Attempting direct information extraction...")
        
        # Use our extraction API
        result = extract_user_info_api(user_message)
        
        if "error" in result or not result.get("is_complete", False):
            print(f"❌ Direct extraction failed: {result.get('error', 'Incomplete information')}")
            return False
            
        # Success! Set the session state directly
        st.session_state.user_info = result["user_info"]
        st.session_state.information_phase_complete = True
        
        print(f"✅ DIRECT EXTRACTION SUCCESSFUL: {result['user_info']}")
        return True
        
    except Exception as e:
        print(f"❌ Exception during direct information processing: {str(e)}")
        return False


def check_and_process_from_assistant_response(message: str) -> bool:
    """
    Check if the assistant response contains complete user information and process it.
    Returns True if successful, False otherwise.
    """
    # First check if this looks like it might contain user information
    info_indicators = [
        # English indicators
        "name", "id", "gender", "age", "hmo", "card", "tier", "information",
        # Hebrew indicators
        "שם", "תעודת", "מגדר", "גיל", "קופת", "כרטיס", "ביטוח"
    ]
    
    # Count how many indicators are present
    indicator_count = sum(1 for indicator in info_indicators if indicator.lower() in message.lower())
    
    # If too few indicators, it's probably not information
    if indicator_count < 4:
        return False
    
    # Try to extract user information
    try:
        print(f"🔍 Attempting to extract user info from assistant response...")
        result = extract_user_info_api(message)
        
        if "error" in result or not result.get("is_complete", False):
            print(f"❌ Extraction from assistant response failed: {result.get('error', 'Incomplete information')}")
            return False
            
        # Success! Set the session state directly
        st.session_state.user_info = result["user_info"]
        st.session_state.information_phase_complete = True
        
        print(f"✅ USER INFO EXTRACTED FROM ASSISTANT RESPONSE: {result['user_info']}")
        return True
    
    except Exception as e:
        print(f"❌ Exception during assistant response extraction: {str(e)}")
        return False


def render_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://www.health.gov.il/Style%20Library/images/logo.png", width=80)
    with col2:
        st.title("Medical Services Chatbot")

    # Bilingual welcome message
    st.markdown("### ברוכים הבאים למערכת המידע של קופות החולים בישראל")
    st.markdown("### Welcome to the Israeli Health Funds Information System")


def main():
    render_header()
    st.divider()

    # Display chat history
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # First, check if we have an assistant message with complete information
    # This helps auto-transition after the assistant has summarized the information
    if not st.session_state.information_phase_complete and len(st.session_state.chat_history) > 0:
        # Look for the last assistant message
        for msg in reversed(st.session_state.chat_history):
            if msg["role"] == "assistant":
                # Check if it contains complete information
                if check_and_process_from_assistant_response(msg["content"]):
                    print("✅ AUTO-TRANSITIONING: Found complete information in assistant message")
                    st.success("Your information is complete! You can now ask questions about health services.")
                    # We don't return here - allow the user to continue with their next message
                break

    # Get user input
    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("user").write(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Check if this might be a direct information submission (regardless of line count)
        if not st.session_state.information_phase_complete:
            # Try to process information directly
            if process_information_directly(prompt):
                # If successful, handle it as if we're in the Q&A phase
                with st.spinner("Processing your information..."):
                    welcome_msg = "Thank you! Your information has been processed successfully. You can now ask questions about your health services."
                    st.success(welcome_msg)
                    st.chat_message("assistant").write(welcome_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": welcome_msg})
                return

        # Continue with the regular flow...
        if st.session_state.information_phase_complete and st.session_state.user_info:
            print(f"✅ USING EXISTING USER INFO: {st.session_state.user_info}")
            # Q&A phase
            with st.spinner("Just a sec! I'm thinking..."):
                response = call_chat_api(prompt)
                if "error" in response:
                    st.error(response["error"])
                    return
                st.chat_message("assistant").write(response["response"])
                st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
            return

        # Add a simpler confirmation check that works with the existing API
        if len(st.session_state.chat_history) >= 3 and prompt.lower() in ["yes", "correct", "right", "כן", "נכון"]:
            # This is likely a confirmation - get the previous assistant message
            last_assistant_msg = None
            for msg in reversed(st.session_state.chat_history[:-1]):  # Exclude the current user message
                if msg["role"] == "assistant":
                    last_assistant_msg = msg["content"]
                    break
                    
            if last_assistant_msg:
                print(f"🔍 Got confirmation, extracting from last assistant message...")
                result = extract_user_info_api(last_assistant_msg)
                
                if "error" not in result and result.get("is_complete", False):
                    # Success! Set the session state
                    st.session_state.user_info = result["user_info"]
                    st.session_state.information_phase_complete = True
                    print(f"✅ USER INFO EXTRACTED: {result['user_info']}")
                    
                    # Add a success message
                    success_msg = "Information collection complete! You can now ask questions about medical services."
                    st.success(success_msg)
                    
                    # Make the API call with the new user_info
                    response = call_chat_api(prompt)
                    if "error" in response:
                        st.error(response["error"])
                        return
                        
                    st.chat_message("assistant").write(response["response"])
                    st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
                    return

        # Normal flow - information collection phase
        with st.spinner("Just a sec! I'm thinking..."):
            response = call_chat_api(prompt)
            if "error" in response:
                st.error(response["error"])
                return
            
            assistant_response = response["response"]
            st.chat_message("assistant").write(assistant_response)
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
            
            # Auto-transition: Check if the assistant response has complete information
            if not st.session_state.information_phase_complete:
                if check_and_process_from_assistant_response(assistant_response):
                    # Show a success message since we'll auto-transition to Q&A phase
                    st.success("Your information is complete! You can now ask questions about health services.")


if __name__ == "__main__":
    main()