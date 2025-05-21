import streamlit as st

from database import get_schedule

def final_view_page():
    st.title("🎓 Your Personalized Semester Plan is Ready!")
    st.write("""
        Congratulations! 🎉

        Your custom semester schedule has been generated based on your preferences, degree requirements, and academic history.
        
        Here is your recommended schedule:""")
    schedule = get_schedule(st.session_state.get("user_id"))
    st.markdown(
        f"""
        <div style="background-color:#c0c0c0; padding:16px; border-radius:8px; margin-bottom:16px;">
            <pre style="font-size: 1.1em; color: black !important;">{schedule}</pre>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("""   
        **What’s next?**
        - Review your recommended courses and schedule below.
        - Import this schedule in your calendar.

        We wish you a successful and fulfilling semester ahead!  
        If you need further assistance, feel free to reach out to your academic advisor.

        _Thank you for using C-Planner!_
    """)
    if st.button("⬅️ Go back to home"):
        st.session_state.page = "session_choice"
    if st.button("📥 Import to Calendar"):
        st.session_state.page = "final_view"