# ─────────────────────────  views/landing.py  ─────────────────────────
import streamlit as st

def landing_page() -> None:
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
        unsafe_allow_html=False,
    )

    # Center the two buttons
    col1, col2, _ = st.columns([1,1,2])
    with col1:
        if st.button("📝 Sign Up"):
            st.session_state.page = "signup"
            st.rerun()

    with col2:
        if st.button("🔑 Sign In"):
            st.session_state.page = "login"
            st.rerun()
