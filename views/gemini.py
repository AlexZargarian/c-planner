# views/gemini.py
import streamlit as st

def gemini_page():
    st.title("🔮 Gemini Page")
    st.write("Welcome to your protected content! 🎉")

    if st.button("Log Out"):
        st.session_state.page = "login"
