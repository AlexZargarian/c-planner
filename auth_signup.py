# auth_signup.py
import re


def validate_email(email):
    """
    Validates if the provided string is a valid email address.

    Args:
        email (str): The email address to validate

    Returns:
        tuple: (is_valid, message) where is_valid is a boolean and message is a string
    """
    # Check if email is empty
    if not email:
        return False, "Email cannot be empty."

    # Regular expression for validating an Email
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if re.match(email_regex, email):
        return True, "Valid email"
    else:
        return False, "Invalid email format. Please enter a valid email address."


def validate_password(password):
    """
    Validates if the provided password meets the requirements:
    - Minimum 6 characters
    - Maximum 18 characters

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

    return True, "Valid password"


def validate_signup(email, password):
    """
    Validates both email and password for signup.

    Args:
        email (str): The email address to validate
        password (str): The password to validate

    Returns:
        tuple: (is_valid, message) where is_valid is a boolean and message is a string
    """
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