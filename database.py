# database.py
import os
import time
import logging
import mysql.connector
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

# ── CONNECTION POOL WITH RETRIES ────────────────────────────────────
pool = None
max_retries = 10
for attempt in range(1, max_retries + 1):
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
        logging.info("Database connection pool created.")
        break
    except mysql.connector.Error as err:
        logging.error(f"Attempt {attempt}/{max_retries} — pool creation error: {err}")
        if attempt < max_retries:
            time.sleep(3)   # wait before retrying
        else:
            logging.error("Exceeded max retries for DB pool creation.")
            pool = None

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
    

def save_transcript(user_id: int, transcript_text: str) -> bool:
    """
    Inserts a finalized transcript for a given user into the transcripts table.
    Returns True on success.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO transcripts (user_id, transcript) 
                VALUES (%s, %s)
            """
            cursor.execute(query, (user_id, transcript_text))
            conn.commit()
            cursor.close()
        return True
    except mysql.connector.Error as err:
        logging.error(f"Error saving transcript: {err}")
        raise Exception("Could not save transcript")


def save_degree_requirements(user_id: int, major: str, text: str) -> None:
    """
    Insert or update this user’s degree requirements & chosen major.
    One row per user is kept.
    """
    sql = """
      INSERT INTO degreqs (user_id, major, requirements)
      VALUES (%s, %s, %s)
      ON DUPLICATE KEY UPDATE
          major        = VALUES(major),
          requirements = VALUES(requirements)
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (user_id, major, text))
        conn.commit()


def save_preference(user_id: int, question: str, answer: str | None) -> None:
    sql = """
      INSERT INTO preferences (user_id, question, answer)
      VALUES (%s, %s, %s)
      ON DUPLICATE KEY UPDATE
        answer = VALUES(answer),
        recorded_at = CURRENT_TIMESTAMP
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (user_id, question, answer))
        conn.commit()


# ─── Transcript helpers ────────────────────────────────────────────
def transcript_exists(user_id: int) -> bool:
    sql = "SELECT 1 FROM transcripts WHERE user_id = %s LIMIT 1"
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            return cur.fetchone() is not None
    except mysql.connector.Error as err:
        logging.error(f"Error checking transcript existence: {err}")
        raise

def fetch_transcript(user_id: int) -> str | None:        # ← name used by resume.py
    sql = "SELECT transcript FROM transcripts WHERE user_id = %s LIMIT 1"
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return row[0] if row else None
    except mysql.connector.Error as err:
        logging.error(f"Error fetching transcript: {err}")
        raise

def upsert_transcript(user_id: int, text: str) -> None:  # ← needed by resume.py
    sql = """
        INSERT INTO transcripts (user_id, transcript)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE transcript = VALUES(transcript)
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id, text))
    except mysql.connector.Error as err:
        logging.error(f"Error upserting transcript: {err}")
        raise


# ─── Preferences helpers ───────────────────────────────────────────
def fetch_all_preferences(user_id: int) -> list[dict]:
    """
    Return rows like {"question": str, "answer": str | None}.
    """
    sql = "SELECT question, answer FROM preferences WHERE user_id = %s"
    try:
        with get_db_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, (user_id,))
            return cur.fetchall()
    except mysql.connector.Error as err:
        logging.error(f"Error fetching preferences: {err}")
        raise



def pref_count(user_id: int) -> int:
    sql = "SELECT COUNT(*) FROM preferences WHERE user_id = %s"
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            (cnt,) = cur.fetchone()
            return int(cnt)
    except mysql.connector.Error as err:
        logging.error(f"Error counting preferences: {err}")
        raise


def delete_user_data(user_id: int) -> None:
    """
    Remove all of this user’s transcripts, preferences, and degree requirements.
    """
    with get_db_connection() as conn:
        cur = conn.cursor()
        # delete preferences first (it’s many rows)
        cur.execute("DELETE FROM preferences WHERE user_id = %s", (user_id,))
        # delete transcript
        cur.execute("DELETE FROM transcripts WHERE user_id = %s", (user_id,))
        # delete degree requirements
        cur.execute("DELETE FROM degreqs WHERE user_id = %s", (user_id,))
        conn.commit()




# # ─── Onboarding check used in login.py ─────────────────────────────
# def has_completed_onboarding(user_id: int) -> bool:
#     """
#     Consider onboarding complete if a transcript exists AND
#     at least one preference row is stored.
#     """
#     return transcript_exists(user_id) and pref_count(user_id) > 0




