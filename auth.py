# auth.py
import logging
import mysql.connector
from passlib.hash import bcrypt
from database import get_db_connection

# Configure logging
logging.basicConfig(
    filename='auth.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def authenticate(email: str, password: str) -> bool:
    """
    Securely authenticate a user with parameterized queries.

    Args:
        email: User's email address
        password: User's plaintext password

    Returns:
        bool: True if authentication successful, False otherwise
    """
    if not email or not password:
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # Using parameterized query for security
            query = "SELECT password_hash FROM users WHERE email = %s"
            cursor.execute(query, (email,))

            row = cursor.fetchone()
            cursor.close()

            # Only verify if we found a matching user
            if row and row.get("password_hash"):
                try:
                    return bcrypt.verify(password, row["password_hash"])
                except ValueError as e:
                    # This catches invalid hash format errors
                    logging.error(f"Password hash verification error: {e}")
                    return False
            return False

    except mysql.connector.Error as err:
        # Log the error but don't expose details to user
        logging.error(f"Authentication error: {err}")
        return False