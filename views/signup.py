# views/signup.py
import streamlit as st
import time
import logging

from database import create_user, user_exists, get_db_connection
from passlib.hash import bcrypt
from authentication.auth_signup import validate_signup, sanitize_input

# Configure logging
logging.basicConfig(
    filename='signup.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def signup_page():
    # 0) Quick DB connectivity check
    try:
        with get_db_connection() as conn:
            pass
    except Exception:
        st.error("❌ Database not available. Please try again later.")
        return

    # 1) Title in black
    st.markdown("<h1 style='color: black !important;'>📝 Sign Up</h1>", unsafe_allow_html=True)

    # 2) Rate limiting for signup attempts
    if "signup_attempts" not in st.session_state:
        st.session_state.signup_attempts = 0
        st.session_state.last_signup_attempt = 0

    if st.session_state.signup_attempts >= 5:
        time_passed = time.time() - st.session_state.last_signup_attempt
        if time_passed < 300:  # 5 minutes cooldown
            mins = int((300 - time_passed) / 60)
            st.markdown(
                f"<p style='color: black !important; "
                f"background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>"
                f"⚠️ Too many signup attempts. Try again in {mins} minute(s).</p>",
                unsafe_allow_html=True
            )
            if st.button("Back to Sign In"):
                st.session_state.page = "login"
            return
        else:
            st.session_state.signup_attempts = 0

    # 3) Input fields
    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_password")
    password_confirm = st.text_input("Confirm Password", type="password", key="su_password_confirm")

    # 4) Password hint
    st.markdown(
        "<p style='color: black !important; font-size: 0.8em;'>"
        "Password must be 6–18 characters long</p>",
        unsafe_allow_html=True
    )

    # 5) Register button
    if st.button("Register"):
        st.session_state.signup_attempts += 1
        st.session_state.last_signup_attempt = time.time()

        # basic empty‐field check
        if not email or not password:
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; "
                "padding: 10px; border-radius: 5px;'>❌ Please fill in all fields.</p>",
                unsafe_allow_html=True
            )
            return

        # password match
        if password != password_confirm:
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; "
                "padding: 10px; border-radius: 5px;'>❌ Passwords do not match.</p>",
                unsafe_allow_html=True
            )
            return

        # sanitize and validate
        email = sanitize_input(email)
        is_valid, message = validate_signup(email, password)
        if not is_valid:
            st.markdown(
                f"<p style='color: black !important; background-color: #F8D7DA; "
                f"padding: 10px; border-radius: 5px;'>❌ {message}</p>",
                unsafe_allow_html=True
            )
            return

        # now attempt DB operations
        try:
            # user exists?
            if user_exists(email):
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; "
                    "padding: 10px; border-radius: 5px;'>❌ An account with this email already exists.</p>",
                    unsafe_allow_html=True
                )
                return

            # hash & create
            pw_hash = bcrypt.using(rounds=12).hash(password)
            create_user(email, pw_hash)

            # success
            st.markdown(
                "<p style='color: black !important; background-color: #D4EDDA; "
                "padding: 10px; border-radius: 5px;'>🎉 Account created! You can now Sign In.</p>",
                unsafe_allow_html=True
            )
            st.session_state.signup_attempts = 0
            time.sleep(1)
            st.session_state.page = "login"

        except Exception as e:
            logging.error(f"Error in signup: {e}")
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; "
                "padding: 10px; border-radius: 5px;'>❌ Error creating account. Please try again later.</p>",
                unsafe_allow_html=True
            )

    # 6) Back link
    st.markdown("---")
    if st.button("Back to Sign In"):
        st.session_state.page = "login"

    # 7) CSS for error/success text
    st.markdown(
        """
        <style>
        /* Ensure all alerts are black text */
        div.stAlert p, .stException, .stError,
        .stWarning, .stInfo, .stSuccess,
        [data-baseweb="notification"] div {
          color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
