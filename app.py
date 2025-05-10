import streamlit as st
from views.login import login_page
from views.signup import signup_page
from views.gemini import gemini_page


def main():
    st.set_page_config(page_title="My App", layout="centered")

    st.markdown(
        """
        <style>
        /* Hide only the sidebar toggle and main menu */
        [data-testid="stSidebar"] { visibility: hidden; }
        #MainMenu { visibility: hidden; }

        /* White background for main content, dark blue header */
        html, body {
          background-color: white !important;
        }

        /* Main content area explicitly white */
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        .block-container,
        .stApp {
          background-color: white !important;
        }

        /* Dark blue header (matching Image 2) */
        [data-testid="stHeader"] {
          background-color: #0A3049 !important;
        }

        /* Make sure header elements are white */
        [data-testid="stHeader"] button, 
        [data-testid="stHeader"] span,
        [data-testid="stHeader"] svg {
          color: white !important;
        }

        /* Black text for ALL text elements except header and footer */
        .main p, .main span, .main label, .main div, 
        .stMarkdown, .stMarkdown p, .stText, .stMarkdown span,
        input, textarea, .stTextInput, .stTextArea {
          color: black !important;
        }

        /* Explicitly target input labels to ensure they're black */
        .stTextInput label, .stTextArea label, 
        [data-testid="stTextInput"] label,
        .css-pkbazv, .css-10trblm, .st-be, .st-bq, .st-br, .st-bs, .st-bt {
          color: black !important;
        }

        /* Make sure all input text is black */
        .stTextInput input, 
        .stTextArea textarea {
          color: black !important;
        }

        /* Light page titles - blue */
        h1 {
          color: #548CA5 !important;
        }

        /* Transparent text & password inputs with improved specificity */
        .stTextInput > div > div > input,
        .stTextInput > div > div > textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stTextInput"] textarea,
        .stTextArea textarea {
          background-color: transparent !important;
          border: 1px solid black !important;
          border-radius: 8px !important;
          padding: 0.5em 0.75em !important;
          color: black !important;
        }

        /* Also make sure the container around inputs is transparent */
        .stTextInput > div, 
        .stTextInput > div > div,
        [data-testid="stTextInput"] > div,
        [data-testid="stTextInput"] > div > div {
          background-color: transparent !important;
        }

        /* Remove any default background colors from input containers */
        div[data-baseweb="base-input"] {
          background-color: transparent !important;
        }

        /* Transparent buttons */
        .stButton > button {
          background-color: transparent !important;
          color: #013B5B !important;
          border: 1px solid #013B5B !important;
          border-radius: 8px !important;
          padding: 0.4em 1.2em !important;
        }
        .stButton > button:hover {
          background-color: rgba(1, 59, 91, 0.1) !important;
        }

        /* Footer styling */
        footer {
          background-color: #356B85 !important;
          color: white !important;
          padding: 1em 0 !important;
        }
        footer a {
          color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Initialize session state for page navigation
    if "page" not in st.session_state:
        st.session_state.page = "login"

    # Route to the appropriate page based on the session state
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    else:
        gemini_page()


if __name__ == "__main__":
    main()