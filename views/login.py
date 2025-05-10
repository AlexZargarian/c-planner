# views/login.py
import streamlit as st
from auth import authenticate

def login_page():
    st.markdown("<h1 style='color: black;'>🔐 Sign In</h1>", unsafe_allow_html=True)

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In"):
        if authenticate(email, password):
            st.session_state.page = "gemini"
        else:
            st.error("❌ Invalid email or password.")

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