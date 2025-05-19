# views/welcome.py
import streamlit as st

def welcome_page():
    st.title("🎉 You're in — Welcome aboard!")
    st.write("""
        Now let’s build your personalized semester planner together. 🚀
        We’ll guide you through a few quick and easy steps — it’ll take less than a minute, 
        and by the end, you’ll have a custom course plan tailored just for you.
        Ready to make your next semester your best one yet? Let’s go! 👇
    """)
    if st.button("Next"):
        st.session_state.page = "session_choice"
