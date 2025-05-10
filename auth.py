# auth.py
from database import get_connection
from passlib.hash import bcrypt

def authenticate(email: str, password: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    return bool(row and bcrypt.verify(password, row["password_hash"]))
