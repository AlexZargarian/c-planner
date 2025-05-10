# views/signup.py
import streamlit as st
from database import create_user
from passlib.hash import bcrypt

def signup_page():
    st.title("📝 Sign Up")

    email    = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_password")

    if st.button("Register"):
        if email and password:
            pw_hash = bcrypt.hash(password)
            try:
                create_user(email, pw_hash)
                st.success("🎉 Account created! You can now Sign In.")
                st.session_state.page = "login"
            except Exception as e:
                st.error(f"Error creating account: {e}")
        else:
            st.error("Please fill in both fields.")

    st.markdown("---")
    if st.button("Back to Sign In"):
        st.session_state.page = "login"
