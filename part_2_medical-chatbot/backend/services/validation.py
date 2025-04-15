import re
import logging
from typing import Dict, Any, Tuple, Optional

from config import settings

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for validating user inputs"""
    
    @staticmethod
    def validate_id_number(id_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Israeli ID number using the check digit algorithm.
        
        Args:
            id_number: 9-digit ID number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic format check
            if not id_number or not isinstance(id_number, str):
                return False, "ID number is required"
            
            # Remove any whitespace
            id_number = id_number.strip()
            
            # Check if it's 9 digits
            if not id_number.isdigit() or len(id_number) != 9:
                return False, "ID number must be exactly 9 digits"
            
            # Israeli ID check digit validation
            # The algorithm: multiply each digit by 1 or 2 alternately,
            # sum the digits of the results, and check if the total is divisible by 10
            total = 0
            for i in range(8):
                digit = int(id_number[i])
                if i % 2 == 0:
                    total += digit
                else:
                    doubled = digit * 2
                    total += doubled if doubled < 10 else doubled - 9
            
            check_digit = (10 - (total % 10)) % 10
            if check_digit != int(id_number[8]):
                return False, "Invalid ID number (check digit validation failed)"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating ID number: {str(e)}")
            return False, "Error validating ID number"
    
    @staticmethod
    def validate_hmo_card_number(card_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate HMO card number.
        
        Args:
            card_number: 9-digit card number
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Basic format check
            if not card_number or not isinstance(card_number, str):
                return False, "HMO card number is required"
            
            # Remove any whitespace
            card_number = card_number.strip()
            
            # Check if it's 9 digits
            if not card_number.isdigit() or len(card_number) != 9:
                return False, "HMO card number must be exactly 9 digits"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating HMO card number: {str(e)}")
            return False, "Error validating HMO card number"
    
    @staticmethod
    def validate_age(age: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate user age.
        
        Args:
            age: User age
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to convert to integer
            try:
                age_int = int(age)
            except (ValueError, TypeError):
                return False, "Age must be a number"
            
            # Check range
            if age_int < 0 or age_int > 120:
                return False, "Age must be between 0 and 120"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating age: {str(e)}")
            return False, "Error validating age"
    
    @staticmethod
    def validate_hmo(hmo: str) -> Tuple[bool, Optional[str]]:
        """
        Validate HMO name.
        
        Args:
            hmo: HMO name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not hmo or not isinstance(hmo, str):
                return False, "HMO name is required"
            
            valid_hmos = settings.HMO_OPTIONS
            if hmo not in valid_hmos:
                return False, f"HMO must be one of: {', '.join(valid_hmos)}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating HMO: {str(e)}")
            return False, "Error validating HMO"
    
    @staticmethod
    def validate_insurance_tier(tier: str) -> Tuple[bool, Optional[str]]:
        """
        Validate insurance tier.
        
        Args:
            tier: Insurance tier
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not tier or not isinstance(tier, str):
                return False, "Insurance tier is required"
            
            valid_tiers = settings.TIER_OPTIONS
            if tier not in valid_tiers:
                return False, f"Insurance tier must be one of: {', '.join(valid_tiers)}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating insurance tier: {str(e)}")
            return False, "Error validating insurance tier"
    
    @staticmethod
    def validate_name(name: str, field_name: str = "name") -> Tuple[bool, Optional[str]]:
        """
        Validate name.
        
        Args:
            name: Name to validate
            field_name: Field name for error message
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not name or not isinstance(name, str):
                return False, f"{field_name} is required"
            
            # Remove whitespace
            name = name.strip()
            
            if len(name) < 1:
                return False, f"{field_name} cannot be empty"
            
            if len(name) > 50:
                return False, f"{field_name} is too long (maximum 50 characters)"
            
            # Allow letters, spaces, hyphens and apostrophes
            # This regex supports both English and Hebrew names
            if not re.match(r'^[\u0590-\u05FFa-zA-Z\s\-\']+$', name):
                return False, f"{field_name} contains invalid characters"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating {field_name}: {str(e)}")
            return False, f"Error validating {field_name}"