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
    Ensure exactly one row per user: delete any existing transcript, then insert the new one.
    """
    delete_sql = "DELETE FROM transcripts WHERE user_id = %s"
    insert_sql = """
        INSERT INTO transcripts (user_id, transcript)
        VALUES (%s, %s)
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # remove old
            cur.execute(delete_sql, (user_id,))
            # insert new
            cur.execute(insert_sql, (user_id, transcript_text))
            conn.commit()
            cur.close()
        return True
    except mysql.connector.Error as err:
        logging.error(f"Error saving transcript: {err}")
        raise Exception("Could not save transcript")



def save_degree_requirements(user_id: int, major: str, text: str) -> None:
    """
    Ensure exactly one row per user: delete any existing, then insert the new major & requirements.
    """
    delete_sql = "DELETE FROM degreqs WHERE user_id = %s"
    insert_sql = """
      INSERT INTO degreqs (user_id, major, requirements)
      VALUES (%s, %s, %s)
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # remove old
            cur.execute(delete_sql, (user_id,))
            # insert new
            cur.execute(insert_sql, (user_id, major, text))
            conn.commit()
    except mysql.connector.Error as err:
        logging.error(f"Error saving degree requirements: {err}")
        raise Exception("Could not save degree requirements")



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
        # delete schedules
        cur.execute("DELETE FROM schedules WHERE user_id = %s", (user_id,))
        conn.commit()


# Add these functions to your database.py file

def get_transcript_text(user_id: int) -> str:
    """
    Retrieve the transcript text for a specific user.

    Args:
        user_id: The user's ID in the database

    Returns:
        The transcript text or empty string if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT transcript FROM transcripts WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            result = cursor.fetchone()
            return result['transcript'] if result else ""
    except Exception as e:
        print(f"Error retrieving transcript: {e}")
        return ""


def save_generated_schedule(user_id: int, schedule_text: str) -> bool:
    """
    Insert or update the generated schedule for this user.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            # see if this user already has a schedule
            cur.execute("SELECT id FROM schedules WHERE user_id = %s LIMIT 1", (user_id,))
            row = cur.fetchone()
            if row:
                # update existing
                sched_id = row[0]
                cur.execute(
                    """
                    UPDATE schedules
                    SET schedule_text = %s,
                        created_at = NOW()
                    WHERE id = %s
                    """,
                    (schedule_text, sched_id)
                )
            else:
                # insert new
                cur.execute(
                    """
                    INSERT INTO schedules (user_id, schedule_text, created_at)
                    VALUES (%s, %s, NOW())
                    """,
                    (user_id, schedule_text)
                )
            conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error saving/updating schedule: {e}")
        return False

def get_schedule(user_id: int) -> str:
    """
    Retrieve the previous schedule for a specific user.

    Args:
        user_id: The user's ID in the database

    Returns:
        The schedule text or empty string if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT schedule_text FROM schedules WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
            result = cursor.fetchone()
            return result['schedule_text'] if result else ""
    except Exception as e:
        print(f"Error retrieving schedule: {e}")
        return ""

# # ─── Onboarding check used in login.py ─────────────────────────────
# def has_completed_onboarding(user_id: int) -> bool:
#     """
#     Consider onboarding complete if a transcript exists AND
#     at least one preference row is stored.
#     """
#     return transcript_exists(user_id) and pref_count(user_id) > 0




