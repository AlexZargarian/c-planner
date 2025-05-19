# views/transcript_intro.py
import streamlit as st

def transcript_intro_page():
    st.header("➡️ Upload Your Transcript (Optional)")
    st.write("""
        To automatically detect your completed courses, please upload the official PDF 
        transcript downloaded from your AUA student account of the website
        auasonis.jenzabarcloud.com (General → Bio → Transcript → Download).
        Our AI will extract the list of completed courses for you. 
        You’ll then have a chance to review and correct any extracted information if needed.
    """)

    # ─── Bottom nav: Back / Upload / Skip ─────────────────────────────
    back_col, upload_col, skip_col = st.columns([1,1,1], gap="medium")

    with back_col:
        if st.button("⬅️ Back"):
            st.session_state.page = "welcome"

    with upload_col:
        if st.button("➡️ Upload Transcript"):
            st.session_state.skip_transcript = False
            st.session_state.page = "gemini"

    with skip_col:
        if st.button("⏭️ Skip"):
            st.session_state.skip_transcript = True
            st.session_state.page = "gemini"
