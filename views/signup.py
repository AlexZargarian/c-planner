# views/signup.py
import streamlit as st
from database import create_user
from passlib.hash import bcrypt
from auth_signup import validate_signup  # Import the validation function


def signup_page():
    # Title in black
    st.markdown("<h1 style='color: black !important;'>📝 Sign Up</h1>", unsafe_allow_html=True)

    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_password")

    if st.button("Register"):
        if email and password:
            # Validate email and password
            is_valid, message = validate_signup(email, password)

            if is_valid:
                pw_hash = bcrypt.hash(password)
                try:
                    create_user(email, pw_hash)
                    # Using markdown instead of st.success to control color
                    st.markdown(
                        "<p style='color: black !important; background-color: #D4EDDA; padding: 10px; border-radius: 5px;'>🎉 Account created! You can now Sign In.</p>",
                        unsafe_allow_html=True)
                    st.session_state.page = "login"
                except Exception as e:
                    st.markdown(
                        f"<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Error creating account: {e}</p>",
                        unsafe_allow_html=True)
            else:
                # Display validation error message
                st.markdown(
                    f"<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ {message}</p>",
                    unsafe_allow_html=True)
        else:
            st.markdown(
                "<p style='color: black !important; background-color: #F8D7DA; padding: 10px; border-radius: 5px;'>❌ Please fill in both fields.</p>",
                unsafe_allow_html=True)

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