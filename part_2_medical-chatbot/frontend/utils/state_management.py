import json
import streamlit as st

def save_chat_state() -> str: # returns a json of all info
    state_data = {
        "chat_history": st.session_state.chat_history,
        "user_info": st.session_state.user_info,
        "language": st.session_state.language,
        "information_phase_complete": st.session_state.information_phase_complete
    }
    try:
        return json.dumps(state_data)
    except Exception as e:
        st.error(f"Error saving state: {str(e)}")
        return ""

def load_chat_state(state_json: str) -> None: # loads a json of all info 
    if not state_json:
        return
    
    try:
        state_data = json.loads(state_json)
        
        if "chat_history" in state_data:
            st.session_state.chat_history = state_data["chat_history"]
        if "user_info" in state_data:
            st.session_state.user_info = state_data["user_info"]
        if "language" in state_data:
            st.session_state.language = state_data["language"]
        if "information_phase_complete" in state_data:
            st.session_state.information_phase_complete = state_data["information_phase_complete"]
    except Exception as e:
        st.error(f"Error loading state: {str(e)}")

def reset_chat_state() -> None:
    st.session_state.chat_history = []
    st.session_state.user_info = None
    st.session_state.information_phase_complete = False

def toggle_language() -> None:
    if st.session_state.language == "en":
        st.session_state.language = "he"
    else:
        st.session_state.language = "en"