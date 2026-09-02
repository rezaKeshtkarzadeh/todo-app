import re


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to a canonical format.
    Removes all non-digit characters except leading +.
    For this project, we keep it simple - just digits.
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Handle leading + or 00
    if phone.startswith('+'):
        digits = '+' + digits
    elif phone.startswith('00'):
        digits = '+' + digits[2:]
    
    return digits


def validate_phone_number(phone: str) -> bool:
    """
    Basic phone number validation.
    Must have at least 10 digits after normalization.
    """
    normalized = normalize_phone_number(phone)
    # Remove leading + for digit count
    digits_only = normalized.lstrip('+')
    return len(digits_only) >= 10 and len(digits_only) <= 15