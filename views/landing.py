# ─────────────────────────  views/landing.py  ─────────────────────────
import streamlit as st

def landing_page() -> None:
    """
    Display the landing (home) page for the Personalized Course Planner.

    This page introduces the application and presents two options:
    - Sign Up for new users
    - Sign In for returning users

    It also outlines the key features of the app.
    """
    # Render the welcome message and feature list using Markdown
    st.markdown(
        """
        # 🎓 Personalized Course Planner

        Welcome to the **Personalized Course Planner** –  
        a little helper that turns your transcript, program
        requirements and personal preferences into an optimized
        semester schedule.

        **What you can do here**

        1. **Upload** your latest transcript  
        2. **Tell us** your program, course wishes & constraints  
        3. **Generate** a schedule you can actually follow

        ---
        """,
        unsafe_allow_html=False,  # Keeps default Markdown sanitization
    )

    # Display "Sign Up" and "Sign In" buttons side-by-side
    col1, col2, _ = st.columns([1, 1, 2])  # Create columns with spacing
    with col1:
        if st.button("📝 Sign Up"):
            # Navigate to the sign-up page when clicked
            st.session_state.page = "signup"
            st.rerun()

    with col2:
        if st.button("🔑 Sign In"):
            # Navigate to the login page when clicked
            st.session_state.page = "login"
            st.rerun()
