import streamlit as st
import requests
import json
import os
import sys
from typing import Dict, Any, Optional
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.models import UserInformation, ChatHistory, Message, Language

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
    ("awaiting_confirmation", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default
        
        
def set_test_user_info():
    """Set test user info for debugging purposes."""
    test_info = {
        "first_name": "ישראל",
        "last_name": "ישראלי",
        "id_number": "123456789",
        "gender": "male",
        "age": "35",
        "hmo": "מכבי",
        "hmo_card_number": "987654321",
        "insurance_tier": "זהב"
    }
    st.session_state.user_info = test_info
    st.session_state.information_phase_complete = True
    st.session_state.awaiting_confirmation = False
    print(f"✅ DEBUG: Manually set test user_info: {test_info}")
    st.success("Test user information set for debugging!")


def call_chat_api(message: str) -> Dict[str, Any]:
    payload = {
        "message": message,
        "language": st.session_state.language
    }

    if st.session_state.chat_history:
        payload["chat_history"] = {"messages": st.session_state.chat_history}

    if st.session_state.user_info and st.session_state.information_phase_complete:
        # Make sure we only send user_info if we're in the Q&A phase
        user_info = st.session_state.user_info
        print(f"✅ SENDING USER INFO TO API: {user_info}")
        payload["user_info"] = user_info
    else:
        print("❌ No user_info in payload - still in information collection phase")

    # Add debugging
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

    # Add debugging
    print(f"✅ API Response: {response.status_code}")
    return response.json()

def force_complete_information_phase():
    """Force the information phase to be complete for debugging."""
    if not st.session_state.user_info:
        st.session_state.user_info = {
            "first_name": "יסמין",
            "last_name": "אדלר",
            "id_number": "208462184",
            "gender": "female",
            "age": "28",
            "hmo": "מכבי",
            "hmo_card_number": "365478927",
            "insurance_tier": "ארד"
        }
    
    st.session_state.information_phase_complete = True
    print(f"✅ MANUALLY SET information_phase_complete = True")
    print(f"✅ USING USER INFO: {st.session_state.user_info}")
    st.success("Information phase marked as complete for debugging!")

def extract_user_info(message: str) -> Optional[Dict[str, Any]]:
    user_info = {}

    # Original patterns
    patterns = {
        'first_name': r'שם פרטי ושם משפחה:\s*([^\s\n]+)',
        'last_name': r'שם פרטי ושם משפחה:\s*[^\s\n]+\s+([^\s\n]+)',
        'id_number': r'מספר תעודת זהות:\s*(\d{9})',
        'gender': r'מגדר:\s*(זכר|נקבה|גבר|אישה)',
        'age': r'גיל:\s*(\d+)',
        'hmo': r'שם קופת החולים:\s*(מכבי|מאוחדת|כללית)',
        'hmo_card_number': r'מספר כרטיס קופת החולים:\s*(\d{9})',
        'insurance_tier': r'דרגת ביטוח:\s*(ארד|כסף|זהב)',
    }
    
    # Alternative patterns (add more alternatives as needed)
    alt_patterns = {
        'first_name': [r'שם:\s*([^\s\n]+)'],
        'last_name': [r'שם משפחה:\s*([^\s\n]+)'],
        'id_number': [r'ת.ז.:\s*(\d{9})', r'תעודת זהות:\s*(\d{9})'],
        'gender': [r'מין:\s*(זכר|נקבה|גבר|אישה)'],
        'age': [r'בן/בת:\s*(\d+)'],
        'hmo': [r'קופת חולים:\s*(מכבי|מאוחדת|כללית)'],
        'hmo_card_number': [r'מספר כרטיס:\s*(\d{9})'],
        'insurance_tier': [r'דרגת ביטוח:\s*(ארד|כסף|זהב)', r'רמת ביטוח:\s*(ארד|כסף|זהב)'],
    }

    import re
    
    # Try the original patterns first
    for field, pattern in patterns.items():
        match = re.search(pattern, message)
        if match:
            user_info[field] = match.group(1).strip()
    
    # Try alternative patterns for missing fields
    for field, alt_pattern_list in alt_patterns.items():
        if field not in user_info:  # Only if not already found
            for pattern in alt_pattern_list:
                match = re.search(pattern, message)
                if match:
                    user_info[field] = match.group(1).strip()
                    break

    gender_mapping = {'זכר': 'male', 'גבר': 'male', 'נקבה': 'female', 'אישה': 'female'}
    if 'gender' in user_info:
        user_info['gender'] = gender_mapping.get(user_info['gender'], user_info['gender'])

    required_fields = set(patterns.keys())
    missing_fields = required_fields - set(user_info.keys())

    if missing_fields:
        print(f"❌ DEBUG: Missing fields after extraction: {missing_fields}")
        return user_info if user_info else None  # Return partial info rather than None

    print(f"✅ DEBUG: Successfully extracted all required fields: {user_info}")
    return user_info


def is_user_info_complete() -> bool:
    required_fields = ["first_name", "last_name", "id_number", "gender",
                       "age", "hmo", "hmo_card_number", "insurance_tier"]
    return all(field in st.session_state.user_info for field in required_fields)


def check_confirmation(message: str) -> bool:
    payload = {"message": message, "language": st.session_state.language}

    response = requests.post(
        f"{API_URL}/api/chat/confirm_intent",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        return response.json().get("is_confirmation", False)

    st.error("Confirmation check failed.")
    return False


def render_header():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://www.health.gov.il/Style%20Library/images/logo.png", width=80)
    with col2:
        st.title("Medical Services Chatbot")

    language_options = {"English": "en", "עברית": "he"}
    selected_language = st.radio("Select Language / בחר שפה", list(language_options.keys()), horizontal=True)
    st.session_state.language = language_options[selected_language]

    st.markdown("### Welcome to the Israeli Health Funds Information System" if st.session_state.language == "en" else
                "### ברוכים הבאים למערכת המידע של קופות החולים בישראל")
    
    # Add debug options
    with st.expander("Debug Options"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Force Complete Info Phase"):
                force_complete_information_phase()
        with col2:
            if st.button("Reset Info Phase"):
                st.session_state.user_info = None
                st.session_state.information_phase_complete = False
                st.info("Information phase reset")
        
        # Display current state
        st.write("Current State:")
        st.write(f"- Information Phase Complete: {st.session_state.information_phase_complete}")
        st.write(f"- User Info: {st.session_state.user_info}")
        
        # Add a button to extract info from the last assistant message
        if st.button("Extract Info From Last Message"):
            last_assistant_msg = None
            for msg in reversed(st.session_state.chat_history):
                if msg["role"] == "assistant":
                    last_assistant_msg = msg["content"]
                    break
            
            if last_assistant_msg:
                st.write("Last assistant message:")
                st.text(last_assistant_msg[:200] + "...")
                
                user_info = extract_user_info_from_summary(last_assistant_msg)
                if user_info:
                    st.session_state.user_info = user_info
                    st.session_state.information_phase_complete = True
                    st.success(f"Extracted user info: {user_info}")
                else:
                    st.error("Failed to extract user info from the message")
            else:
                st.warning("No assistant message found in chat history")

def main():
    render_header()
    st.divider()

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Type your message here..."):
        st.chat_message("user").write(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Check if we already have user_info, otherwise we need to collect it
        if st.session_state.information_phase_complete and st.session_state.user_info:
            print(f"✅ USING EXISTING USER INFO: {st.session_state.user_info}")
            # Skip ahead to the Q&A phase
            with st.spinner("Just a sec! I'm thinking..."):
                response = call_chat_api(prompt)
                if "error" in response:
                    st.error(response["error"])
                    return
                st.chat_message("assistant").write(response["response"])
                st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
            return

        # Handle the information collection phase
        with st.spinner("Just a sec! I'm thinking..."):
            # Get the summary message from the chat history if it exists
            # and contains information that can be extracted
            summary_message = find_summary_message(st.session_state.chat_history)
            
            # Check if this message is a confirmation after seeing a summary
            if summary_message and is_confirmation_message(prompt):
                print(f"🔍 CONFIRMATION DETECTED: '{prompt}' after summary")
                user_info = extract_user_info_from_summary(summary_message)
                
                if user_info:
                    # We successfully extracted the user info
                    st.session_state.user_info = user_info
                    st.session_state.information_phase_complete = True
                    print(f"✅ USER INFO EXTRACTED: {user_info}")
                    
                    # Now make the API call with the new user_info
                    response = call_chat_api(prompt)
                    if "error" in response:
                        st.error(response["error"])
                        return
                    
                    # Add a success message before the assistant's response
                    st.success("Information collection complete! You can now ask questions about medical services.")
                    
                    st.chat_message("assistant").write(response["response"])
                    st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
                    return
                else:
                    print("❌ FAILED TO EXTRACT USER INFO FROM SUMMARY")
            
            # Normal flow - get response from the API
            response = call_chat_api(prompt)
            if "error" in response:
                st.error(response["error"])
                return
            
            st.chat_message("assistant").write(response["response"])
            st.session_state.chat_history.append({"role": "assistant", "content": response["response"]})
            
            # Check if this response is a summary of user info
            # (We'll handle the confirmation on the next user message)
            if is_summary_message(response["response"]):
                print("🔍 SUMMARY DETECTED - Will check for confirmation in next message")


def is_confirmation_message(message: str) -> bool:
    """Check if a message is confirming information."""
    confirmation_phrases = [
        "כן", "נכון", "מאשר", "מאשרת", "אישור", "הכל נכון", "הכל בסדר",
        "yes", "correct", "confirm", "accurate", "right", "looks good"
    ]
    message_lower = message.lower()
    
    for phrase in confirmation_phrases:
        if phrase in message_lower:
            return True
    
    # Simple messages like "כן" (yes)
    if message_lower.strip() in ["כן", "yes", "ok", "אוקיי", "אוקי"]:
        return True
        
    return False

def is_summary_message(message: str) -> bool:
    """Check if a message is a summary of user information."""
    summary_indicators = [
        "הנה סיכום המידע", "here's a summary", "summary of your information",
        "המידע שאספתי", "הפרטים שמסרת", "האם כל הפרטים נכונים",
        "האם המידע נכון", "are these details correct", "verify the information"
    ]
    
    for indicator in summary_indicators:
        if indicator in message:
            return True
    
    # Check for multiple information fields in the message
    fields = ["שם", "תעודת זהות", "מגדר", "גיל", "קופת חולים", "name", "id", "gender", "age", "hmo"]
    field_count = sum(1 for field in fields if field in message)
    
    # If at least 4 information fields are present, it's likely a summary
    return field_count >= 4

def find_summary_message(chat_history):
    """Find the last summary message in the chat history."""
    # Search backwards through the history for assistant messages
    for i in range(len(chat_history) - 1, -1, -1):
        msg = chat_history[i]
        if msg["role"] == "assistant" and is_summary_message(msg["content"]):
            return msg["content"]
    return None

def extract_user_info_from_summary(summary: str) -> dict:
    """Extract user information from a summary message."""
    # This function needs to be more flexible to capture information
    # from differently formatted summaries
    
    user_info = {}
    
    # Try to extract information using pattern matching
    patterns = {
        # Try to match both list format and prose format
        'first_name': [
            r'שם(?:\s+פרטי)?:\s*([^\s\n,\.]+)',
            r'שם(?:\s+מלא)?:\s*([^\s\n,\.]+)',
            r'name:\s*([^\s\n,\.]+)',
        ],
        'last_name': [
            r'שם(?:\s+פרטי)?:\s*[^\s\n,\.]+\s+([^\s\n,\.]+)',
            r'שם משפחה:\s*([^\s\n,\.]+)',
            r'last name:\s*([^\s\n,\.]+)',
            # Sometimes the name might be listed as "first_name last_name"
            r'שם(?:\s+מלא)?:\s*([^\s\n,\.]+)\s+([^\s\n,\.]+)',
        ],
        'id_number': [
            r'(?:מספר\s+)?תעודת\s*זהות:\s*(\d{9})',
            r'ת\.?ז\.?:\s*(\d{9})',
            r'id(?:\s+number)?:\s*(\d{9})',
        ],
        'gender': [
            r'מגדר:\s*(זכר|נקבה|גבר|אישה)',
            r'מין:\s*(זכר|נקבה|גבר|אישה)',
            r'gender:\s*(male|female|man|woman)',
        ],
        'age': [
            r'גיל:\s*(\d+)',
            r'בן/בת:\s*(\d+)',
            r'age:\s*(\d+)',
        ],
        'hmo': [
            r'(?:שם\s+)?קופת\s*(?:ה)?חולים:\s*(מכבי|מאוחדת|כללית)',
            r'hmo:\s*(maccabi|meuhedet|clalit)',
        ],
        'hmo_card_number': [
            r'מספר\s+כרטיס\s+קופת\s*(?:ה)?חולים:\s*(\d{9})',
            r'מספר\s+כרטיס:\s*(\d{9})',
            r'hmo\s+card(?:\s+number)?:\s*(\d{9})',
        ],
        'insurance_tier': [
            r'(?:מסלול|דרגת)\s+(?:ה)?ביטוח:\s*(ארד|כסף|זהב)',
            r'רמת\s+ביטוח:\s*(ארד|כסף|זהב)',
            r'insurance\s+(?:tier|level):\s*(bronze|silver|gold)',
        ],
    }
    
    import re
    
    # Try each pattern for each field
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, summary, re.IGNORECASE)
            if match:
                # For last_name with the pattern that captures both names
                if field == 'last_name' and len(match.groups()) > 1 and match.group(2):
                    user_info['first_name'] = match.group(1)
                    user_info['last_name'] = match.group(2)
                else:
                    user_info[field] = match.group(1).strip()
                break
    
    # If we couldn't extract the last name but have the first name
    # Try to find it from context
    if 'first_name' in user_info and 'last_name' not in user_info:
        # Look for the first name plus something after it
        full_name_pattern = rf'{re.escape(user_info["first_name"])}\s+([^\s\n,\.]+)'
        match = re.search(full_name_pattern, summary)
        if match:
            user_info['last_name'] = match.group(1).strip()
    
    # Map Hebrew gender terms to English
    gender_mapping = {'זכר': 'male', 'גבר': 'male', 'נקבה': 'female', 'אישה': 'female'}
    if 'gender' in user_info:
        user_info['gender'] = gender_mapping.get(user_info['gender'], user_info['gender'])
    
    # Map Hebrew insurance tiers to English if needed
    tier_mapping = {'ארד': 'bronze', 'כסף': 'silver', 'זהב': 'gold'}
    if 'insurance_tier' in user_info:
        # Convert English tiers back to Hebrew if needed
        reverse_tier_mapping = {'bronze': 'ארד', 'silver': 'כסף', 'gold': 'זהב'}
        if user_info['insurance_tier'].lower() in reverse_tier_mapping:
            user_info['insurance_tier'] = reverse_tier_mapping[user_info['insurance_tier'].lower()]
        
        # Ensure it's one of the expected values
        valid_tiers = ['ארד', 'כסף', 'זהב']
        if user_info['insurance_tier'] not in valid_tiers:
            user_info['insurance_tier'] = 'ארד'  # Default to bronze/ארד if unrecognized
    
    # Map HMO names to normalized format if needed
    hmo_mapping = {'מכבי': 'maccabi', 'מאוחדת': 'meuhedet', 'כללית': 'clalit'}
    if 'hmo' in user_info:
        # Keep the original Hebrew name, as that's what the backend expects
        pass
    
    # Log what we found and what's missing
    found_fields = list(user_info.keys())
    missing_fields = [f for f in ["first_name", "last_name", "id_number", "gender", "age", "hmo", "hmo_card_number", "insurance_tier"] if f not in user_info]
    
    print(f"✅ Found fields: {found_fields}")
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        
    # Look for field values in text for missing fields
    # This handles cases where the formatting isn't standard
    if missing_fields:
        print("🔍 Attempting to extract missing fields from context...")
        
        # Define keywords to look for
        keywords = {
            'id_number': ['id', 'ת.ז', 'תעודת זהות'],
            'gender': ['מגדר', 'מין', 'gender'],
            'age': ['גיל', 'age'],
            'hmo': ['קופת חולים', 'hmo'],
            'hmo_card_number': ['מספר כרטיס', 'card number'],
            'insurance_tier': ['ביטוח', 'insurance']
        }
        
        # Extract text around each keyword
        for field in missing_fields:
            if field in keywords:
                for keyword in keywords[field]:
                    # Find the keyword and extract the text around it
                    indices = [m.start() for m in re.finditer(keyword, summary, re.IGNORECASE)]
                    for idx in indices:
                        # Look for a value in the next 20 characters
                        context = summary[idx:idx+50]
                        print(f"Context for {field}: {context}")
                        
                        # Try to extract based on field type
                        if field == 'id_number' or field == 'hmo_card_number':
                            # Look for 9 digits
                            digit_match = re.search(r'(\d{9})', context)
                            if digit_match:
                                user_info[field] = digit_match.group(1)
                                print(f"Extracted {field} from context: {user_info[field]}")
                                break
                        elif field == 'age':
                            # Look for 1-3 digits
                            age_match = re.search(r'(\d{1,3})', context)
                            if age_match:
                                user_info[field] = age_match.group(1)
                                print(f"Extracted {field} from context: {user_info[field]}")
                                break
                        elif field == 'hmo':
                            # Look for HMO names
                            hmo_match = re.search(r'(מכבי|מאוחדת|כללית|Maccabi|Meuhedet|Clalit)', context, re.IGNORECASE)
                            if hmo_match:
                                user_info[field] = hmo_match.group(1)
                                print(f"Extracted {field} from context: {user_info[field]}")
                                break
                        elif field == 'insurance_tier':
                            # Look for tier names
                            tier_match = re.search(r'(ארד|כסף|זהב|Bronze|Silver|Gold)', context, re.IGNORECASE)
                            if tier_match:
                                user_info[field] = tier_match.group(1)
                                print(f"Extracted {field} from context: {user_info[field]}")
                                break
                        elif field == 'gender':
                            # Look for gender terms
                            gender_match = re.search(r'(זכר|נקבה|גבר|אישה|Male|Female)', context, re.IGNORECASE)
                            if gender_match:
                                raw_gender = gender_match.group(1)
                                user_info[field] = gender_mapping.get(raw_gender, raw_gender)
                                print(f"Extracted {field} from context: {user_info[field]}")
                                break
    
    # If we couldn't extract first or last name, try simpler approach
    if 'first_name' not in user_info or 'last_name' not in user_info:
        # Look for name indicators and nearby text
        name_indices = [m.start() for m in re.finditer(r'שם|name', summary, re.IGNORECASE)]
        for idx in name_indices:
            context = summary[idx:idx+50]
            print(f"Name context: {context}")
            
            # Try to extract a name (usually 2-3 words after "name:")
            name_match = re.search(r'(?:שם|name)[^:]*:\s*([^\n\.,]{2,50})', context, re.IGNORECASE)
            if name_match:
                full_name = name_match.group(1).strip()
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    if 'first_name' not in user_info:
                        user_info['first_name'] = name_parts[0]
                    if 'last_name' not in user_info:
                        user_info['last_name'] = name_parts[-1]
                    print(f"Extracted name from context: {user_info.get('first_name')} {user_info.get('last_name')}")
                    break
    
    # Final check for required fields
    missing_fields = [f for f in ["first_name", "last_name", "id_number", "gender", "age", "hmo", "hmo_card_number", "insurance_tier"] if f not in user_info]
    
    if missing_fields:
        print(f"❌ Still missing fields after extraction: {missing_fields}")
        # If too many fields are missing, we might need to return None or a partial result
        if len(missing_fields) > 3:  # If more than 3 fields are missing
            print("❌ Too many fields missing, extraction likely failed")
            return None if len(user_info) < 3 else user_info  # Return None if we have less than 3 fields
    
    print(f"✅ Final extracted user info: {user_info}")
    return user_info

def test_regex_extraction(message):
    """Test each regex pattern individually against the message."""
    import re
    
    patterns = {
        'first_name': r'שם פרטי ושם משפחה:\s*([^\s\n]+)',
        'last_name': r'שם פרטי ושם משפחה:\s*[^\s\n]+\s+([^\s\n]+)',
        'id_number': r'מספר תעודת זהות:\s*(\d{9})',
        'gender': r'מגדר:\s*(זכר|נקבה|גבר|אישה)',
        'age': r'גיל:\s*(\d+)',
        'hmo': r'שם קופת החולים:\s*(מכבי|מאוחדת|כללית)',
        'hmo_card_number': r'מספר כרטיס קופת החולים:\s*(\d{9})',
        'insurance_tier': r'דרגת ביטוח:\s*(ארד|כסף|זהב)',
    }
    
    print("🔍 DEBUG: Testing each regex pattern:")
    for field, pattern in patterns.items():
        match = re.search(pattern, message)
        if match:
            print(f"✅ Pattern match for {field}: {match.group(1)}")
        else:
            print(f"❌ No match for {field} pattern")
            
    # Also try some alternative formats that might be used
    alt_patterns = {
        'first_name_alt': r'שם:\s*([^\s\n]+)',
        'id_number_alt': r'ת.ז.:\s*(\d{9})',
        'gender_alt': r'מין:\s*(זכר|נקבה|גבר|אישה)',
    }
    
    print("🔍 DEBUG: Testing alternative patterns:")
    for field, pattern in alt_patterns.items():
        match = re.search(pattern, message)
        if match:
            print(f"✅ Alternative match for {field}: {match.group(1)}")

if __name__ == "__main__":
    main()
