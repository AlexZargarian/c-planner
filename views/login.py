# views/login.py
import streamlit as st
import time
import logging
from authentication.auth import authenticate
from authentication.auth_signup import sanitize_input
from database import get_db_connection

# Configure logging
logging.basicConfig(
    filename='login.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def login_page():
    st.markdown("<h1 style='color: black;'>🔐 Sign In</h1>", unsafe_allow_html=True)

    # Initialize session state for login attempts and timeout
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0
        st.session_state.last_attempt_time = 0

    # Check if the user is temporarily locked out
    if st.session_state.login_attempts >= 5:
        time_passed = time.time() - st.session_state.last_attempt_time
        if time_passed < 300:  # 5 minutes lockout
            st.markdown(
                f"<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>⚠️ Too many failed login attempts. Try again in {int((300 - time_passed) / 60)} minutes.</p>",
                unsafe_allow_html=True
            )
            if st.button("Go to Sign Up"):
                st.session_state.page = "signup"
            return
        else:
            # Reset attempt counter after lockout period
            st.session_state.login_attempts = 0

    # Initialize session activity tracking
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()
    elif time.time() - st.session_state.last_activity > 1800:  # 30 minute timeout
        # Clear any existing session data for security
        for key in list(st.session_state.keys()):
            if key != "page":
                del st.session_state[key]
        st.session_state.page = "login"
        st.markdown(
            "<p style='color: black !important; background-color: #FFF3CD; padding: 10px; border-radius: 5px;'>ℹ️ Your session has expired. Please log in again.</p>",
            unsafe_allow_html=True
        )

    # Update last activity time
    st.session_state.last_activity = time.time()

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    login_clicked = st.button("Sign In")

    if login_clicked:
        try:
            # Sanitize input (only email, not password)
            email = sanitize_input(email)

            # Increment login attempt counter
            st.session_state.login_attempts += 1
            st.session_state.last_attempt_time = time.time()

            # Add a small delay to prevent timing attacks
            time.sleep(1)

            if not email or not password:
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Please enter both email and password.</p>",
                    unsafe_allow_html=True
                )
            elif authenticate(email, password):
                # Reset login attempts on success
                st.session_state.login_attempts = 0

                # fetch the row for this email so we can pull out its id
                with get_db_connection() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    user_row = cursor.fetchone()
                st.session_state.user_id = user_row["id"]

                # Set session data
                st.session_state.user_email = email
                st.session_state.authenticated = True
                st.session_state.login_time = time.time()
                # Redirect to main page
                st.session_state.page = "gemini"
            else:
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Invalid email or password.</p>",
                    unsafe_allow_html=True
                )

        except Exception as e:
            logging.error(f"Login error: {e}")
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ An error occurred during login. Please try again.</p>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    if st.button("Go to Sign Up"):
        st.session_state.page = "signup"

    # Inject CSS to make error messages black
    st.markdown(
        """
        <style>
        /* Target error messages specifically */
        div.stAlert p {
            color: black !important;
        }
        .st-emotion-cache-16idsys p {
            color: black !important;
        }
        /* Additional selectors to ensure coverage of error messages */
        .element-container div[data-testid="stDecoration"] p {
            color: black !important;
        }
        .stException, .stError, .stWarning, .stInfo {
            color: black !important;
        }
        /* Target the text inside error containers */
        [data-baseweb="notification"] div {
            color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )