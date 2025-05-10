# database.py
import os, mysql.connector, logging
from dotenv import load_dotenv
from mysql.connector.pooling import MySQLConnectionPool
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    filename='database.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Create a connection pool instead of single connections
try:
    pool = MySQLConnectionPool(
        pool_name="app_pool",
        pool_size=5,
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )
except mysql.connector.Error as err:
    logging.error(f"Error creating connection pool: {err}")
    # Don't re-raise the exception to avoid exposing error details
    # Instead, the get_connection function will handle errors

@contextmanager
def get_db_connection():
    """
    Context manager for database connections that ensures proper closing
    even if an exception occurs.
    """
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
    except mysql.connector.Error as err:
        logging.error(f"Database connection error: {err}")
        raise Exception("Database connection error occurred")
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_connection():
    """
    Legacy function for backward compatibility.
    Prefer using get_db_connection() context manager instead.
    """
    try:
        return pool.get_connection()
    except mysql.connector.Error as err:
        logging.error(f"Error getting connection from pool: {err}")
        raise Exception("Could not connect to database")

def create_user(email: str, password_hash: str):
    """
    Securely creates a new user with parameterized queries.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Using parameterized query for security
            query = "INSERT INTO users (email, password_hash) VALUES (%s, %s)"
            cursor.execute(query, (email, password_hash))
            conn.commit()
            cursor.close()
            return True
    except mysql.connector.Error as err:
        logging.error(f"Error creating user: {err}")
        if err.errno == 1062:  # Duplicate entry error code
            raise Exception("A user with this email already exists")
        else:
            raise Exception("Error creating user account")

def user_exists(email: str) -> bool:
    """
    Safely check if a user exists without exposing error details.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT COUNT(*) as count FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            cursor.close()
            return result and result['count'] > 0
    except mysql.connector.Error as err:
        logging.error(f"Error checking if user exists: {err}")
        raise Exception("Error checking user records")