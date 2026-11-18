import re
from datetime import date

from errors import bad_request


def require_object(data):
    if not isinstance(data, dict):
        raise bad_request("a JSON object is required")


def is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def validate_text_fields(data, fields):
    for field in fields:
        if field in data and not is_nonempty_string(data[field]):
            raise bad_request(f"{field} must be a nonempty string")


def is_valid_email(value):
    return isinstance(value, str) and re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value) is not None


def is_valid_isbn(value):
    if not isinstance(value, str):
        return False
    digits = value.replace("-", "")
    return digits.isdigit() and len(digits) in (10, 13)


def is_valid_date(value):
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return True
