import json
import logging
from typing import Dict, Any, List

import openai

FORM_SCHEMA_ENGLISH = {
    "lastName": "",
    "firstName": "",
    "idNumber": "",
    "gender": "",
    "dateOfBirth": {
        "day": "",
        "month": "",
        "year": ""
    },
    "address": {
        "street": "",
        "houseNumber": "",
        "entrance": "",
        "apartment": "",
        "city": "",
        "postalCode": "",
        "poBox": ""
    },
    "landlinePhone": "",
    "mobilePhone": "",
    "jobType": "",
    "dateOfInjury": {
        "day": "",
        "month": "",
        "year": ""
    },
    "timeOfInjury": "",
    "accidentLocation": "",
    "accidentAddress": "",
    "accidentDescription": "",
    "injuredBodyPart": "",
    "signature": "",
    "formFillingDate": {
        "day": "",
        "month": "",
        "year": ""
    },
    "formReceiptDateAtClinic": {
        "day": "",
        "month": "",
        "year": ""
    },
    "medicalInstitutionFields": {
        "healthFundMember": "",
        "natureOfAccident": "",
        "medicalDiagnoses": ""
    }
}

FORM_SCHEMA_HEBREW = {
    "שם משפחה": "",
    "שם פרטי": "",
    "מספר זהות": "",
    "מין": "",
    "תאריך לידה": {
        "יום": "",
        "חודש": "",
        "שנה": ""
    },
    "כתובת": {
        "רחוב": "",
        "מספר בית": "",
        "כניסה": "",
        "דירה": "",
        "ישוב": "",
        "מיקוד": "",
        "תא דואר": ""
    },
    "טלפון קווי": "",
    "טלפון נייד": "",
    "סוג העבודה": "",
    "תאריך הפגיעה": {
        "יום": "",
        "חודש": "",
        "שנה": ""
    },
    "שעת הפגיעה": "",
    "מקום התאונה": "",
    "כתובת מקום התאונה": "",
    "תיאור התאונה": "",
    "האיבר שנפגע": "",
    "חתימה": "",
    "תאריך מילוי הטופס": {
        "יום": "",
        "חודש": "",
        "שנה": ""
    },
    "תאריך קבלת הטופס בקופה": {
        "יום": "",
        "חודש": "",
        "שנה": ""
    },
    "למילוי ע\"י המוסד הרפואי": {
        "חבר בקופת חולים": "",
        "מהות התאונה": "",
        "אבחנות רפואיות": ""
    }
}

FIELD_TRANSLATION = {
    "שם משפחה": "lastName",
    "שם פרטי": "firstName",
    "מספר זהות": "idNumber",
    "מין": "gender",
    "תאריך לידה": "dateOfBirth",
    "יום": "day",
    "חודש": "month",
    "שנה": "year",
    "כתובת": "address",
    "רחוב": "street",
    "מספר בית": "houseNumber",
    "כניסה": "entrance",
    "דירה": "apartment",
    "ישוב": "city",
    "מיקוד": "postalCode",
    "תא דואר": "poBox",
    "טלפון קווי": "landlinePhone",
    "טלפון נייד": "mobilePhone",
    "סוג העבודה": "jobType",
    "תאריך הפגיעה": "dateOfInjury",
    "שעת הפגיעה": "timeOfInjury",
    "מקום התאונה": "accidentLocation",
    "כתובת מקום התאונה": "accidentAddress",
    "תיאור התאונה": "accidentDescription",
    "האיבר שנפגע": "injuredBodyPart",
    "חתימה": "signature",
    "תאריך מילוי הטופס": "formFillingDate",
    "תאריך קבלת הטופס בקופה": "formReceiptDateAtClinic",
    "למילוי ע\"י המוסד הרפואי": "medicalInstitutionFields",
    "חבר בקופת חולים": "healthFundMember",
    "מהות התאונה": "natureOfAccident",
    "אבחנות רפואיות": "medicalDiagnoses"
}

class FieldExtractor:    
    def __init__(self, endpoint: str, key: str, deployment_name: str, api_version: str):
        self.endpoint = endpoint
        self.key = key
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        openai.api_type = "azure"
        openai.api_key = key
        openai.api_base = endpoint
        openai.api_version = api_version
        
    
    def extract_fields(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        try:
            language = ocr_result.get("language", "en") # default value is english
            
            schema = FORM_SCHEMA_HEBREW if language == "he" else FORM_SCHEMA_ENGLISH
            
            all_text = ocr_result["content"]
            
            
            page_content = []
            for page in ocr_result["pages"]:
                page_text = f"Page {page['page_number']}:\n"
                for line in page["lines"]:
                    page_text += f"{line['content']}\n"
                page_content.append(page_text)
            
            prompt = self._create_extraction_prompt(all_text, page_content, language, schema)
            
            response = openai.ChatCompletion.create(
                engine=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert in extracting information from document forms, particularly National Insurance Institute forms in Israel."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, # better as 0.1 for low randomness 
                max_tokens=4000
            )
            
            extracted_json = self._process_openai_response(response)
            
            if language == "he":
                extracted_json = self._translate_schema_hebrew_to_english(extracted_json)
            return extracted_json
            
        except Exception as e:
            print(f"Error extracting fields: {str(e)}")
            return schema  # Return empty schema if extraction fails
    
    def _create_extraction_prompt(self, all_text: str, page_content: List[str], language: str, schema: Dict[str, Any]) -> str:
        if language == "he":
            instruction = """
            אתה מומחה בחילוץ מידע מטפסי ביטוח לאומי. יש לחלץ את כל השדות מהטקסט המצורף ולמלא אותם בפורמט JSON המסופק.
            עבור שדות שלא ניתן למצוא בטקסט, השאר מחרוזת ריקה.
            בדוק היטב תאריכים ומספרים, והפרד אותם לפי הדרישה (יום/חודש/שנה).
            תן את התוצאה כ-JSON בלבד, ללא הסברים נוספים.
            """
        else:
            instruction = """
            You are an expert in extracting information from National Insurance Institute forms in Israel. 
            Extract all fields from the provided text and fill them into the provided JSON format.
            For fields that cannot be found in the text, leave an empty string.
            Pay careful attention to dates and numbers, separating them as required (day/month/year).
            Return ONLY the JSON result, with no additional explanations.
            """
        
        prompt = f"{instruction}\n\n"
        prompt += f"Form Text:\n{all_text[:4000]}\n\n"
        
        prompt += "Page-by-Page Content:\n"
        for page_text in page_content:
            prompt += f"{page_text[:1000]}\n"
        
        prompt += f"\nJSON Schema to Fill (provide only the filled JSON as response):\n{json.dumps(schema, indent=2, ensure_ascii=False)}"

        return prompt
    
    def _process_openai_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        try:
            content = response["choices"][0]["message"]["content"]
            
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                extracted_json = json.loads(json_str)
                return extracted_json
            else:
                print("No valid JSON found in OpenAI response")
                return FORM_SCHEMA_ENGLISH  
                
        except Exception as e:
            print(f"Error processing OpenAI response: {str(e)}")
            return FORM_SCHEMA_ENGLISH 
    
    def _translate_schema_hebrew_to_english(self, hebrew_schema: Dict[str, Any]) -> Dict[str, Any]:
        english_schema = {}
        
        try:
            for key, value in hebrew_schema.items():
                english_key = FIELD_TRANSLATION.get(key, key)
                
                if isinstance(value, dict):
                    english_value = {}
                    for sub_key, sub_value in value.items():
                        english_sub_key = FIELD_TRANSLATION.get(sub_key, sub_key)
                        english_value[english_sub_key] = sub_value
                    english_schema[english_key] = english_value
                else:
                    english_schema[english_key] = value
            
            for key, value in FORM_SCHEMA_ENGLISH.items():
                if key not in english_schema:
                    english_schema[key] = value
                    
            return english_schema
                
        except Exception as e:
            print(f"Error translating schema: {str(e)}")
            return FORM_SCHEMA_ENGLISH