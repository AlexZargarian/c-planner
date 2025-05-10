# views/signup.py
import streamlit as st
import time
import logging
from database import create_user, user_exists
from passlib.hash import bcrypt
from authentication.auth_signup import validate_signup, sanitize_input

# Configure logging
logging.basicConfig(
    filename='signup.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def signup_page():
    # Title in black
    st.markdown("<h1 style='color: black !important;'>📝 Sign Up</h1>", unsafe_allow_html=True)

    # Rate limiting for signup attempts
    if "signup_attempts" not in st.session_state:
        st.session_state.signup_attempts = 0
        st.session_state.last_signup_attempt = 0

    # Check if user has made too many signup attempts
    if st.session_state.signup_attempts >= 5:
        time_passed = time.time() - st.session_state.last_signup_attempt
        if time_passed < 300:  # 5 minutes cooldown
            st.markdown(
                f"<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>⚠️ Too many signup attempts. Please try again in {int((300 - time_passed) / 60)} minutes.</p>",
                unsafe_allow_html=True
            )
            if st.button("Back to Sign In"):
                st.session_state.page = "login"
            return
        else:
            # Reset counter after cooldown
            st.session_state.signup_attempts = 0

    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_password")
    password_confirm = st.text_input("Confirm Password", type="password", key="su_password_confirm")

    # Show password requirements
    st.markdown(
        "<p style='color: black !important; font-size: 0.8em;'>Password must be 6-18 characters long</p>",
        unsafe_allow_html=True
    )

    if st.button("Register"):
        # Increment attempt counter and update timestamp
        st.session_state.signup_attempts += 1
        st.session_state.last_signup_attempt = time.time()

        try:
            # Sanitize and validate inputs
            email = sanitize_input(email)

            # Basic validation first
            if not email or not password:
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Please fill in all fields.</p>",
                    unsafe_allow_html=True
                )
                return

            # Check if passwords match
            if password != password_confirm:
                st.markdown(
                    "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Passwords do not match.</p>",
                    unsafe_allow_html=True
                )
                return

            # Validate email and password format
            is_valid, message = validate_signup(email, password)

            if is_valid:
                # Check if user already exists before trying to create
                try:
                    if user_exists(email):
                        st.markdown(
                            "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ An account with this email already exists.</p>",
                            unsafe_allow_html=True
                        )
                        return

                    # Hash password with bcrypt (cost factor 12)
                    pw_hash = bcrypt.using(rounds=12).hash(password)

                    # Create user in database
                    create_user(email, pw_hash)

                    # Success message and redirect
                    st.markdown(
                        "<p style='color: black !important; background-color: #D4EDDA; padding: 10px; border-radius: 5px;'>🎉 Account created! You can now Sign In.</p>",
                        unsafe_allow_html=True
                    )

                    # Reset attempt counter on success
                    st.session_state.signup_attempts = 0

                    # Add delay to prevent timing attacks
                    time.sleep(1)

                    # Redirect to login
                    st.session_state.page = "login"

                except Exception as e:
                    logging.error(f"Error in signup: {e}")
                    st.markdown(
                        "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Error creating account. Please try again later.</p>",
                        unsafe_allow_html=True
                    )
            else:
                # Display validation error message
                st.markdown(
                    f"<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ {message}</p>",
                    unsafe_allow_html=True
                )
        except Exception as e:
            logging.error(f"Unexpected error in signup: {e}")
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ An unexpected error occurred. Please try again later.</p>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    if st.button("Back to Sign In"):
        st.session_state.page = "login"

    # Add CSS to ensure all Streamlit error messages are black
    st.markdown(
        """
        <style>
        /* Target all Streamlit alert messages */
        div.stAlert p {
            color: black !important;
        }
        .st-emotion-cache-16idsys p {
            color: black !important;
        }
        .element-container div[data-testid="stDecoration"] p {
            color: black !important;
        }
        .stException, .stError, .stWarning, .stInfo, .stSuccess {
            color: black !important;
        }
        [data-baseweb="notification"] div {
            color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )