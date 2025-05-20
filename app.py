# app.py
import streamlit as st
import base64
from pathlib import Path

####### new
from views.generation import generation_page


from views.session_choice  import session_choice_page      # ← NEW
from views.resume          import resume_page              # ← NEW

from views.landing         import landing_page           # already imported
from views.login            import login_page
from views.signup           import signup_page
from views.welcome          import welcome_page
from views.transcript_intro import transcript_intro_page
from views import gemini                                  # brings in the module once
gemini_page = gemini.gemini_page


# ─── Helper to embed your PNG logo into the header bar ──────────────
def get_image_as_base64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


# ─── Main entrypoint ────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="My App", layout="centered")

    #  (header-logo & css are unchanged)  --------------------------------
    image_path = "/Users/alex/PycharmProjects/chat/img/ChatGPT Image May 10, 2025, 08_48_16 PM.png"
    if Path(image_path).exists():
        img64 = get_image_as_base64(image_path)
        st.markdown(
            f"""
            <style>
              [data-testid="stHeader"] {{
                position: relative;
                height: 80px !important;
              }}
              [data-testid="stHeader"]::before {{
                content: "";
                position: absolute;
                left: 16px; top: 50%;
                width: 80px; height: 80px;
                background-image: url("data:image/png;base64,{img64}");
                background-size: contain;
                background-repeat: no-repeat;
                transform: translateY(-50%);
                z-index: 1000;
              }}
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <style>
          body, .block-container, .stMarkdown, .stText,
          h1,h2,h3,h4,h5,h6, input, textarea, button {
            color: white !important;
          }
          .stButton>button#logout_btn {
            background-color: rgba(255,255,255,0.9) !important;
            color: #0A3049 !important;
            border: 1px solid #0A3049 !important;
            border-radius: 6px !important;
            padding: 0.35em 1.1em !important;
          }
          .stButton>button#logout_btn:hover {
            background-color: #ffffff !important;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 4️⃣  Navigation state – default to **landing**
    if "page" not in st.session_state:
        st.session_state.page = "landing"           # ← UPDATED

    # 5️⃣  Log-Out button only on authenticated/inner pages
    if st.session_state.page not in ("login", "signup", "landing"):  # ← UPDATED
        spacer, logout_col = st.columns([8, 1])
        with logout_col:
            if st.button("Log Out", key="logout_btn"):
                st.session_state.clear()
                st.session_state.page = "landing"
                st.rerun()

    # 6️⃣  Page router
    match st.session_state.page:
        case "landing":          landing_page()     # ← NEW
        case "login":            login_page()
        case "signup":           signup_page()
        case "session_choice":   session_choice_page()   # ← NEW
        case "resume":           resume_page()           # ← NEW
        case "welcome":          welcome_page()
        case "transcript_intro": transcript_intro_page()
        case "generation":       generation_page()
        case _:                  gemini_page()      # default to questionnaire

# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()

