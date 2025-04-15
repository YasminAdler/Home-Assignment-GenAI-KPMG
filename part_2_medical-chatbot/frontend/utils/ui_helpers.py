import streamlit as st
from typing import Dict, List, Any, Optional

def get_language_text(en_text: str, he_text: str) -> str:
    """
    Get text based on the current language.
    
    Args:
        en_text: English text
        he_text: Hebrew text
        
    Returns:
        Text in the current language
    """
    if st.session_state.language == "en":
        return en_text
    else:
        return he_text

def show_user_info_summary(user_info: Dict[str, Any]) -> None:
    """
    Display a summary of user information.
    
    Args:
        user_info: Dictionary of user information
    """
    # Create a formatted display of user information
    if st.session_state.language == "en":
        st.subheader("Your Information")
        info_md = f"""
        **Name:** {user_info.get('first_name', '')} {user_info.get('last_name', '')}  
        **ID Number:** {user_info.get('id_number', '')}  
        **Gender:** {user_info.get('gender', '')}  
        **Age:** {user_info.get('age', '')}  
        **HMO:** {user_info.get('hmo', '')}  
        **HMO Card Number:** {user_info.get('hmo_card_number', '')}  
        **Insurance Tier:** {user_info.get('insurance_tier', '')}  
        """
    else:
        st.subheader("הפרטים שלך")
        info_md = f"""
        **שם:** {user_info.get('first_name', '')} {user_info.get('last_name', '')}  
        **מספר ת.ז.:** {user_info.get('id_number', '')}  
        **מגדר:** {user_info.get('gender', '')}  
        **גיל:** {user_info.get('age', '')}  
        **קופת חולים:** {user_info.get('hmo', '')}  
        **מספר כרטיס קופת חולים:** {user_info.get('hmo_card_number', '')}  
        **דרגת ביטוח:** {user_info.get('insurance_tier', '')}  
        """
    
    st.markdown(info_md)

def show_welcome_message() -> None:
    """
    Display a welcome message based on the current phase.
    """
    if st.session_state.information_phase_complete:
        if st.session_state.language == "en":
            st.info("You can now ask questions about medical services based on your HMO and insurance tier.")
        else:
            st.info("כעת ניתן לשאול שאלות על שירותים רפואיים בהתאם לקופת החולים ורמת הביטוח שלך.")
    else:
        if st.session_state.language == "en":
            st.info("Please provide your personal information so we can assist you better.")
        else:
            st.info("אנא ספק את פרטיך האישיים כדי שנוכל לסייע לך טוב יותר.")

def render_chat_message(role: str, content: str) -> None:
    """
    Render a chat message with the appropriate styling.
    
    Args:
        role: The role of the message sender ('user' or 'assistant')
        content: The message content
    """
    if role == "user":
        st.chat_message("user").write(content)
    else:
        st.chat_message("assistant").write(content)

def render_error(message: str) -> None:
    """
    Render an error message.
    
    Args:
        message: The error message
    """
    st.error(message)

def render_info(message: str) -> None:
    """
    Render an info message.
    
    Args:
        message: The info message
    """
    st.info(message)

def render_success(message: str) -> None:
    """
    Render a success message.
    
    Args:
        message: The success message
    """
    st.success(message)

def render_warning(message: str) -> None:
    """
    Render a warning message.
    
    Args:
        message: The warning message
    """
    st.warning(message)