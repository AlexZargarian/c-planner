# app.py
import streamlit as st
from views.login   import login_page
from views.signup  import signup_page
from views.gemini  import gemini_page

# 1) Must be the first Streamlit call
st.set_page_config(page_title="My App", layout="centered")

# 2) Hide sidebar, menu, footer
st.markdown(
    """
    <style>
      [data-testid="stSidebar"] {visibility: hidden;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# 3) Initialize page state
if "page" not in st.session_state:
    st.session_state.page = "login"

# 4) Dispatch
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()
else:
    gemini_page()
