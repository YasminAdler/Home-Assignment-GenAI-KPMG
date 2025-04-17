import re
from datetime import datetime
from typing import Dict, Any, Tuple

class FormValidator:
    def validate_fields(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        validated = data.copy()
        messages = {}
        current_year = datetime.now().year

        id_number = data.get("idNumber", "")
        if id_number:
            clean = re.sub(r'\D', '', id_number)
            if len(clean) != 9:
                messages["idNumber"] = f"ID must be 9 digits, got {len(clean)}"
            else:
                validated["idNumber"] = clean

        for field in ["landlinePhone", "mobilePhone"]:
            phone = data.get(field, "")
            if phone:
                clean = re.sub(r'[^\d+]', '', phone)
                if not 9 <= len(clean) <= 15:
                    messages[field] = f"Phone length is unusual: {len(clean)}"
                validated[field] = clean

        for field in ["dateOfBirth", "dateOfInjury", "formFillingDate", "formReceiptDateAtClinic"]:
            date = data.get(field, {})
            if not isinstance(date, dict):
                messages[field] = "Expected a date dictionary"
                continue

            day, month, year = date.get("day", ""), date.get("month", ""), date.get("year", "")

            for unit, min_val, max_val in [("day", 1, 31), ("month", 1, 12)]:
                val = date.get(unit, "")
                if val:
                    try:
                        n = int(val)
                        if not min_val <= n <= max_val:
                            messages[f"{field}.{unit}"] = f"{unit.capitalize()} out of range: {val}"
                        validated[field][unit] = f"{n:02d}"
                    except:
                        messages[f"{field}.{unit}"] = f"Invalid {unit}: {val}"

            if year:
                try:
                    y = int(year)
                    if y < 100:
                        y += 2000 if y <= 30 else 1900
                    if field == "dateOfBirth":
                        if not (1900 <= y <= current_year):
                            messages[f"{field}.year"] = f"Unrealistic birth year: {y}"
                    else:
                        if not (2000 <= y <= current_year):
                            messages[f"{field}.year"] = f"Year not in valid range: {y}"
                    validated[field]["year"] = str(y)
                except:
                    messages[f"{field}.year"] = f"Invalid year: {year}"

        gender = data.get("gender", "").lower()
        if gender:
            if gender in ["m", "male", "זכר", "ז"]:
                validated["gender"] = "Male"
            elif gender in ["f", "female", "נקבה", "נ"]:
                validated["gender"] = "Female"
            else:
                messages["gender"] = f"Unknown gender: {gender}"

        time = data.get("timeOfInjury", "")
        if time:
            match = re.search(r'(\d{1,2})[:.h](\d{2})', time)
            if match:
                h, m = map(int, match.groups())
                if 0 <= h <= 23 and 0 <= m <= 59:
                    validated["timeOfInjury"] = f"{h:02d}:{m:02d}"
                else:
                    messages["timeOfInjury"] = f"Time out of range: {h}:{m}"
            else:
                messages["timeOfInjury"] = f"Unrecognized time format: {time}"

        address = data.get("address", {})
        if isinstance(address, dict) and address.get("city") and not address.get("postalCode"):
            messages["address.postalCode"] = "Postal code is missing"


        total = self._count_fields(data)
        filled = self._count_filled_fields(data)
        confidence = max(0, filled / total - min(0.5, len(messages) * 0.05)) if total > 0 else 0

        messages["_overall_confidence"] = f"{confidence:.2f}"
        messages["_filled_fields"] = f"{filled}/{total}"

        print(f"Validation complete — confidence: {confidence:.2f}, filled: {filled}/{total}")
        return validated, messages

    def _count_fields(self, data: Dict[str, Any]) -> int:
        return sum(self._count_fields(v) if isinstance(v, dict) else 1 for v in data.values())

    def _count_filled_fields(self, data: Dict[str, Any]) -> int:
        return sum(self._count_filled_fields(v) if isinstance(v, dict) else bool(v) for v in data.values())
