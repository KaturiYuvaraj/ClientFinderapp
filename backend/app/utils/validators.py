import re

def normalize_string(text: str) -> str:
    if not text:
        return ""
    # Lowercase, replace non-alphanumerics with space, condense spaces
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return " ".join(cleaned.split())

def normalize_phone(phone: str) -> str:
    if not phone:
        return ""
    # Extract only digits
    digits = re.sub(r"\D", "", phone)
    # Strip leading country code 91 or 1 if standard 10 digit local phone
    if len(digits) > 10 and (digits.startswith("91") or digits.startswith("1")):
        return digits[-10:]
    return digits

def sanitize_text(text: str, max_length: int = 2000) -> str:
    if not text:
        return ""
    # Basic trim and slice
    return text.strip()[:max_length]
