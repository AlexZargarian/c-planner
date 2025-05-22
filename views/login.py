# ─────────────────────────  views/login.py  ─────────────────────────
import streamlit as st
import time
import logging
from authentication.auth import authenticate
from authentication.auth_signup import sanitize_input
from database import get_db_connection
from views.gemini import TOTAL_Q  

# Configure logging to record login-related errors
logging.basicConfig(
    filename='login.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def login_page():
    """
    Renders the login (sign-in) interface where users can input their email and password.
    
    Features:
    - Login form with validation
    - Session lockout after 5 failed attempts (5-minute cooldown)
    - Session expiration after 30 minutes of inactivity
    - On successful login, redirects user to the welcome page
    """

    # Page title
    st.markdown("<h1 style='color: black;'>🔐 Sign In</h1>", unsafe_allow_html=True)

    # Track login attempts and last attempt time in session state
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
        st.session_state.last_attempt_time = 0

    # Lock user out for 5 minutes after 5 failed attempts
    if st.session_state.login_attempts >= 5:
        time_passed = time.time() - st.session_state.last_attempt_time
        if time_passed < 300:
            st.markdown(
                f"<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>⚠️ Too many failed login attempts. Try again in {int((300 - time_passed) / 60)} minutes.</p>",
                unsafe_allow_html=True
            )
            if st.button("Go to Sign Up"):
                st.session_state.page = "signup"
            return
        else:
            # Reset lockout counter after cooldown
            st.session_state.login_attempts = 0

    # Track and expire session after 30 minutes of inactivity
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()
    elif time.time() - st.session_state.last_activity > 1800:
        # Clear all session keys except page
        for key in list(st.session_state.keys()):
            if key != "page":
                del st.session_state[key]
        st.session_state.page = "login"
        st.markdown(
            "<p style='color: black !important; background-color: #FFF3CD; padding: 10px; border-radius: 5px;'>ℹ️ Your session has expired. Please log in again.</p>",
            unsafe_allow_html=True
        )

    # Update last activity timestamp
    st.session_state.last_activity = time.time()

    # Login form fields
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    login_clicked = st.button("Sign In")

    if login_clicked:
        try:
            # Sanitize email input to prevent injection attacks
            email = sanitize_input(email)

            # Track the login attempt
            st.session_state.login_attempts += 1
            st.session_state.last_attempt_time = time.time()

            # Delay to reduce timing attack risk
            time.sleep(1)

            # Input validation
            if not email or not password:
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Please enter both email and password.</p>",
                    unsafe_allow_html=True
                )

            # Authenticate credentials
            elif authenticate(email, password):
                # Reset login attempts on success
                st.session_state.login_attempts = 0

                # Fetch user ID from DB
                with get_db_connection() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    user_row = cursor.fetchone()

                # Store user session info
                st.session_state.user_id = user_row["id"]
                st.session_state.user_email = email
                st.session_state.authenticated = True
                st.session_state.login_time = time.time()

                # Redirect to welcome page
                st.session_state.page = "welcome"

            # Authentication failed
            else:
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Invalid email or password.</p>",
                    unsafe_allow_html=True
                )

        except Exception as e:
            # Log unexpected errors and show error message
            logging.error(f"Login error: {e}")
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ An error occurred during login. Please try again.</p>",
                unsafe_allow_html=True
            )

    # Option to redirect to Sign Up page
    st.markdown("---")
    if st.button("Go to Sign Up"):
        st.session_state.page = "signup"

    # Custom CSS to ensure all error text appears in black
    st.markdown(
        """
        <style>
        div.stAlert p {
            color: black !important;
        }
        .st-emotion-cache-16idsys p {
            color: black !important;
        }
        .element-container div[data-testid="stDecoration"] p {
            color: black !important;
        }
        .stException, .stError, .stWarning, .stInfo {
            color: black !important;
        }
        [data-baseweb="notification"] div {
            color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
