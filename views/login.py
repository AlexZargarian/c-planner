# views/login.py
import streamlit as st
from auth import authenticate

def login_page():
    st.title("🔐 Sign In")

    email    = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In"):
        if authenticate(email, password):
            st.session_state.page = "gemini"
        else:
            st.error("❌ Invalid email or password.")

    st.markdown("---")
    if st.button("Go to Sign Up"):
        st.session_state.page = "signup"
