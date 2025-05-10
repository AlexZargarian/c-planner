# auth_signup.py
import re
import html
import logging

# Configure logging
logging.basicConfig(
    filename='auth_signup.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def sanitize_input(input_string):
    """
    Sanitize input to prevent XSS and other injection attacks.

    Args:
        input_string (str): String to sanitize

    Returns:
        str: Sanitized string
    """
    if not isinstance(input_string, str):
        return ""

    # Convert to string, strip whitespace, and escape HTML
    sanitized = html.escape(str(input_string).strip())
    return sanitized


def validate_email(email):
    """
    Validates if the provided string is a valid email address.

    Args:
        email (str): The email address to validate

    Returns:
        tuple: (is_valid, message) where is_valid is a boolean and message is a string
    """
    # Sanitize input first
    email = sanitize_input(email)

    # Check if email is empty
    if not email:
        return False, "Email cannot be empty."

    # More strict regular expression for validating an Email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Limit length to prevent DOS attacks
    if len(email) > 255:
        return False, "Email is too long."

    if re.match(email_regex, email):
        return True, "Valid email"
    else:
        return False, "Invalid email format. Please enter a valid email address."


def validate_password(password):
    """
    Validates if the provided password meets the requirements:
    - Minimum 6 characters
    - Maximum 18 characters
    - Does not contain SQL injection or script patterns

    Args:
        password (str): The password to validate

    Returns:
        tuple: (is_valid, message) where is_valid is a boolean and message is a string
    """
    # Check if password is empty
    if not password:
        return False, "Password cannot be empty."

    # Check password length
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if len(password) > 18:
        return False, "Password cannot exceed 18 characters."

    # Check for potentially malicious patterns
    dangerous_patterns = [
        "'--", "/*", "*/", "@@", "char(", "exec(", "eval(",
        "SELECT", "UNION", "DROP", "<script>", "javascript:"
    ]

    for pattern in dangerous_patterns:
        if pattern.lower() in password.lower():
            return False, "Password contains invalid characters or patterns."

    return True, "Valid password"


def validate_signup(email, password):
    """
    Validates both email and password for signup with extra security measures.

    Args:
        email (str): The email address to validate
        password (str): The password to validate

    Returns:
        tuple: (is_valid, message) where is_valid is a boolean and message is a string
    """
    try:
        # Sanitize inputs first
        email = sanitize_input(email)
        # Note: We don't sanitize password as it might contain special characters

        # Validate email
        email_valid, email_message = validate_email(email)
        if not email_valid:
            return False, email_message

        # Validate password
        password_valid, password_message = validate_password(password)
        if not password_valid:
            return False, password_message

        # Both are valid
        return True, "Valid credentials"

    except Exception as e:
        logging.error(f"Validation error: {e}")
        return False, "An error occurred during validation. Please try again."