"""
Common validation functions
"""

def validate_indian_mobile(mobile: str) -> str:
    """
    Validate and normalize Indian mobile number

    Args:
        mobile: Phone number in various formats

    Returns:
        Normalized mobile number with +91 country code

    Raises:
        ValueError: If mobile number is invalid

    Accepted formats:
        - 9876543210
        - +919876543210
        - 91 9876543210
        - 91-9876-543-210
        - (91) 9876543210

    Returns: +919876543210
    """
    if not mobile or mobile.strip() == "":
        return ""  # Optional field

    # Remove common formatting characters
    cleaned = mobile.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")

    # Handle country code
    if cleaned.startswith("91") and len(cleaned) == 12:
        # Has country code: 919876543210
        mobile_number = cleaned[2:]
    elif len(cleaned) == 10:
        # No country code: 9876543210
        mobile_number = cleaned
    else:
        raise ValueError("Mobile number must be 10 digits (with or without +91 country code)")

    # Validate Indian mobile number format
    # Must start with 6, 7, 8, or 9
    if mobile_number[0] not in ['6', '7', '8', '9']:
        raise ValueError("Indian mobile number must start with 6, 7, 8, or 9")

    # Must be exactly 10 digits
    if len(mobile_number) != 10 or not mobile_number.isdigit():
        raise ValueError("Mobile number must be exactly 10 digits")

    # Return normalized format with country code
    return f"+91{mobile_number}"
