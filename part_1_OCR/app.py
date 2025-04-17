import os
import json
import base64
from typing import Dict, Any
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from utilss import DocumentProcessor, FieldExtractor, FormValidator, FORM_SCHEMA_ENGLISH, FORM_SCHEMA_HEBREW

load_dotenv()

document_endpoint = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
document_key = os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_KEY")

openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
openai_key = os.environ.get("AZURE_OPENAI_KEY_1")
deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

required_vars = {
    "Document Intelligence Endpoint": document_endpoint,
    "Document Intelligence Key": document_key,
    "OpenAI Endpoint": openai_endpoint,
    "OpenAI Key": openai_key
}

missing_vars = [name for name, value in required_vars.items() if not value]

if not missing_vars:
    try:
        document_processor = DocumentProcessor(document_endpoint, document_key)
        field_extractor = FieldExtractor(openai_endpoint, openai_key, deployment_name, api_version)
        st.session_state.setup_success = True
    except Exception as e:
        st.error(f"Error initializing services: {str(e)}")
        st.session_state.setup_success = False
else:
    st.session_state.setup_success = False

st.set_page_config(
    page_title="Form Field Extractor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.hebrew-text {
    direction: rtl;
    text-align: right;
    font-family: 'Arial', sans-serif;
}
.confidence-high {
    color: green;
    font-weight: bold;
}
.confidence-medium {
    color: orange;
    font-weight: bold;
}
.confidence-low {
    color: red;
    font-weight: bold;
}
.validation-message {
    color: #ff6b6b;
    font-size: 0.8em;
    margin-top: 2px;
}
</style>
""", unsafe_allow_html=True)

def display_json(json_data: Dict[str, Any], validation_messages: Dict[str, str] = None):
    validation_messages = validation_messages or {}
    
    def build_rows(data, prefix="", rows=None):
        if rows is None:
            rows = []
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                build_rows(value, full_key, rows)
            else:
                message = validation_messages.get(full_key, "")
                
                rows.append({
                    "Field": full_key,
                    "Value": str(value),
                    "Validation": message
                })
        
        return rows
    
    df_data = build_rows(json_data)
    if df_data:
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data to display")

def display_confidence(confidence: float):
    if confidence >= 0.7:
        confidence_class = "confidence-high"
    elif confidence >= 0.4:
        confidence_class = "confidence-medium"
    else:
        confidence_class = "confidence-low"
    
    st.markdown(f'<p>Extraction Confidence: <span class="{confidence_class}">{confidence:.2f}</span></p>', unsafe_allow_html=True)

def get_download_link(json_data: Dict[str, Any], filename: str):
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
    b64 = base64.b64encode(json_str.encode("utf-8")).decode()
    href = f'<a href="data:application/json;charset=utf-8;base64,{b64}" download="{filename}">Download JSON</a>'
    return href

def main():
    st.title("National Insurance Form Field Extractor")
    
    if missing_vars:
        st.error(f"Missing environment variables: {', '.join(missing_vars)}")
        st.info("Please set these variables in the .env file and restart the application.")
        return
    
    tab1, tab2, tab3 = st.tabs(["Extract Fields", "View Sample", "Help"])
    
    with tab1:
        st.header("Upload and Extract Form Fields")
        st.write("Upload a PDF or image file of a National Insurance Institute form to extract its fields.")
        
        uploaded_file = st.file_uploader(
            "Choose a file", 
            type=["pdf", "jpg", "jpeg", "png"], 
            accept_multiple_files=False
            )
        
        if uploaded_file is not None:
            file_details = {
                "Filename": uploaded_file.name,
                "File size": f"{uploaded_file.size / 1024:.2f} KB",
                "File type": uploaded_file.type
            }
            st.write("File Details:", file_details)
            
            if uploaded_file.type.startswith("image"):
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            elif uploaded_file.type == "application/pdf":
                st.write("PDF file uploaded. Processing...")
            
            if "extracted_fields" not in st.session_state and st.button("Extract Fields"):
                with st.spinner("Processing the document..."):
                    try:
                        file_extension = uploaded_file.name.split(".")[-1].lower()

                        ocr_result = document_processor.process_document(
                            uploaded_file.getvalue(), 
                            file_extension
                        )

                        extracted_fields = field_extractor.extract_fields(ocr_result)

                        validator = FormValidator()
                        validated_fields, validation_messages = validator.validate_fields(extracted_fields)

                        st.session_state.extracted_fields = extracted_fields
                        st.session_state.validated_fields = validated_fields
                        st.session_state.validation_messages = validation_messages
                        st.session_state.ocr_result = ocr_result

                        st.success("Document processed successfully!")

                    except Exception as e:
                        st.error(f"Error processing document: {str(e)}")
                        return
            
            if hasattr(st.session_state, 'validated_fields'):
                st.subheader("Extracted Fields")
                
                confidence = float(st.session_state.validation_messages.get("_overall_confidence", "0"))
                display_confidence(confidence)
                
                filled_fields = st.session_state.validation_messages.get("_filled_fields", "0/0")
                st.write(f"Fields filled: {filled_fields}")
                
                st.json(st.session_state.validated_fields)
                
                st.markdown(
                    get_download_link(st.session_state.validated_fields, "extracted_fields.json"),
                    unsafe_allow_html=True
                )
                
                with st.expander("Validation Messages"):
                    display_messages = {k: v for k, v in st.session_state.validation_messages.items() 
                                       if not k.startswith("_")}
                    
                    if display_messages:
                        for field, message in display_messages.items():
                            st.markdown(f"**{field}**: {message}")
                    else:
                        st.write("No validation issues found.")
                
                with st.expander("Raw OCR Result"):
                    st.write("Document Content:")
                    st.text(st.session_state.ocr_result.get("content", "No content available"))
                    
                    st.write("Detected Language:", 
                             "Hebrew" if st.session_state.ocr_result.get("language") == "he" else "English")
                    
                    st.write(f"Pages: {len(st.session_state.ocr_result.get('pages', []))}")
                    st.write(f"Tables: {len(st.session_state.ocr_result.get('tables', []))}")
    
    with tab2:
        st.header("Sample Form Structure")
        st.write("This is the expected structure of the extracted form fields:")
        
        lang_tab1, lang_tab2 = st.tabs(["English Schema", "Hebrew Schema"])
        
        with lang_tab1:
            st.json(FORM_SCHEMA_ENGLISH)
        
        with lang_tab2:
            st.markdown('<div class="hebrew-text">', unsafe_allow_html=True)
            st.json(FORM_SCHEMA_HEBREW)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.header("Help & Information")
        st.markdown("""
        ### About this Application
        
        This application extracts information from ביטוח לאומי (National Insurance Institute) forms using:
        - Azure Document Intelligence for OCR (Optical Character Recognition)
        - Azure OpenAI for field extraction and understanding
        
        ### How to Use
        
        1. **Upload** a PDF or image file of a filled National Insurance form
        2. Click **Extract Fields** to process the document
        3. View the extracted fields in JSON format
        4. Download the JSON result if needed
        
        ### Supported Forms
        
        This application is designed to work with National Insurance Institute forms in Israel, in both Hebrew and English.
        
        ### Field Validation
        
        The application performs basic validation on the extracted fields:
        - ID number format checking
        - Date format standardization
        - Phone number format checking
        - Gender value standardization
        
        ### Confidence Score
        
        The confidence score indicates how reliable the extraction is:
        - **High** (green): Most fields were extracted successfully with high confidence
        - **Medium** (orange): Some fields may be missing or uncertain
        - **Low** (red): Many fields are missing or potentially incorrect
        """)

if __name__ == "__main__":
    main()