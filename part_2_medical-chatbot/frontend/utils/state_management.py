import json
import streamlit as st
from typing import Dict, List, Any, Optional
import base64

def encode_state(state_data: Dict[str, Any]) -> str:
    """
    Encode state data to a base64 string for client-side storage.
    
    Args:
        state_data: Dictionary of state data
        
    Returns:
        Base64 encoded string
    """
    try:
        json_str = json.dumps(state_data)
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    except Exception as e:
        st.error(f"Error encoding state: {str(e)}")
        return ""

def decode_state(encoded_state: str) -> Dict[str, Any]:
    """
    Decode a base64 string to state data.
    
    Args:
        encoded_state: Base64 encoded string
        
    Returns:
        Dictionary of state data
    """
    try:
        if not encoded_state:
            return {}
        
        json_str = base64.b64decode(encoded_state).decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Error decoding state: {str(e)}")
        return {}

def save_chat_state() -> str:
    """
    Save the current chat state to a base64 encoded string.
    
    Returns:
        Base64 encoded string of the current chat state
    """
    state_data = {
        "chat_history": st.session_state.chat_history,
        "user_info": st.session_state.user_info,
        "language": st.session_state.language,
        "information_phase_complete": st.session_state.information_phase_complete
    }
    
    return encode_state(state_data)

def load_chat_state(encoded_state: str) -> None:
    """
    Load chat state from a base64 encoded string.
    
    Args:
        encoded_state: Base64 encoded string of the chat state
    """
    if not encoded_state:
        return
    
    state_data = decode_state(encoded_state)
    
    if "chat_history" in state_data:
        st.session_state.chat_history = state_data["chat_history"]
    if "user_info" in state_data:
        st.session_state.user_info = state_data["user_info"]
    if "language" in state_data:
        st.session_state.language = state_data["language"]
    if "information_phase_complete" in state_data:
        st.session_state.information_phase_complete = state_data["information_phase_complete"]

def reset_chat_state() -> None:
    """
    Reset the chat state to its initial values.
    """
    st.session_state.chat_history = []
    st.session_state.user_info = None
    st.session_state.information_phase_complete = False
    # Keep the language setting

def toggle_language() -> None:
    """
    Toggle between Hebrew and English.
    """
    if st.session_state.language == "en":
        st.session_state.language = "he"
    else:
        st.session_state.language = "en"