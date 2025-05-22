# ─────────────────────────  views/gemini_answer.py  ─────────────────────────

import streamlit as st
import re
import pandas as pd
from pathlib import Path
import time

# Database helpers
from database import transcript_exists, fetch_all_preferences, get_schedule
from views.generation import (
    generate_schedule,
    get_transcript_text,
    get_degree_requirements,
    degree_requirements_exists,
)

# Constants and utilities
from views.gemini import QUESTIONS
from views.gemini import save_preference

def gemini_answer_page() -> None:
    """
    Streamlit page: Displays the AI-generated personalized schedule,
    allows regenerating, saving, and providing feedback.

    Flow:
    1. Validates session and generated schedule.
    2. Displays the schedule broken down by day.
    3. Provides options to regenerate, save, or go back.
    4. Offers additional input field for user comments/preferences.
    """
    st.title("✨ Your Personalized Schedule")

    # Ensure user is logged in
    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    # 1) Ensure a schedule has been generated
    if "generated_schedule" not in st.session_state:
        st.error("No schedule has been generated yet. Please go back and generate one first.")
        if st.button("⬅️ Back to Generation"):
            st.session_state.page = "generation"
            st.rerun()
        return

    # Retrieve the generated schedule
    schedule = st.session_state.generated_schedule

    # 2) Display schedule broken out by weekday sections
    st.markdown("### Your Recommended Schedule")
    st.markdown("""
    <style>
    .course-item {
        padding: 5px 0;
        border-left: 3px solid rgba(255, 255, 255, 0.3);
        padding-left: 10px;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    found_any = False

    # Use regex to extract blocks of courses for each weekday
    for day in days:
        pattern = rf"(?i){day}[:\s]+(.*?)(?=(?:{'|'.join(days)})[:\s]+|\Z)"
        match = re.search(pattern, schedule, re.DOTALL)
        if match:
            found_any = True
            st.markdown(f"#### {day}")
            for line in match.group(1).splitlines():
                txt = line.strip()
                if txt:
                    st.markdown(f"<div class='course-item'>{txt}</div>", unsafe_allow_html=True)

    # Fallback: display full schedule as-is if pattern fails
    if not found_any:
        st.markdown(schedule)

    # 3) Display notes, rationale, or explanation if included in the schedule
    notes_match = re.search(r"(?i)(notes|explanation|recommendations|rationale):(.*)", schedule, re.DOTALL)
    if notes_match:
        st.markdown("### Notes")
        st.markdown(notes_match.group(2).strip())

    st.markdown("---")

    # 4) Action buttons (Back, Regenerate, Save, View Final)
    col1, col2, col3, col4 = st.columns(4, gap="small")

    # Go back to preferences input page
    with col1:
        if st.button("⬅️ Back to Preferences"):
            st.session_state.page = "gemini"
            st.rerun()

    # Regenerate schedule in-place using current data
    with col2:
        if st.button("🔄 Regenerate Schedule"):
            with st.spinner("🔮 Regenerating your schedule…"):
                # Load course catalog CSV
                courses_file = Path("data") / "courses.csv"
                if not courses_file.exists():
                    st.error("Courses catalog not found!")
                    return
                courses_text = pd.read_csv(courses_file).to_csv(index=False)

                # Fetch user transcript, if available
                tr_ok = transcript_exists(uid)
                transcript_text = get_transcript_text(uid) if tr_ok else ""

                # Fetch degree requirements, if uploaded
                deg_ok = degree_requirements_exists(uid)
                degree_req = get_degree_requirements(uid) if deg_ok else ""

                # Load user preferences
                rows = fetch_all_preferences(uid)
                preferences = {
                    r["question"]: r.get("answer", "Not provided") for r in rows
                }

                # Re-run the AI schedule generator
                new_schedule = generate_schedule(
                    courses_text,
                    transcript_text,
                    degree_req,
                    preferences,
                    get_schedule(uid)
                )

                # Update session with regenerated schedule
                st.session_state.generated_schedule = new_schedule

            # Re-render page
            st.rerun()

    # Save current schedule to database
    with col3:
        if st.button("💾 Save Schedule"):
            if not schedule.strip():
                st.error("Nothing to save.")
            else:
                from database import save_generated_schedule
                ok = save_generated_schedule(uid, schedule)
                if ok:
                    st.success("🎉 Schedule saved to your account!")
                else:
                    st.error("❌ Failed to save schedule. Try again later.")

    # Navigate to final formatted view
    with col4:
        if get_schedule(uid) and st.button("🎉 View final schedule"):
            st.session_state.page = "final_view"
            st.rerun()                

    st.markdown("---")

    # 5) Allow user to submit additional comments or preferences
    with st.expander("➕ Provide Additional Details"):
        additional_details = st.text_input(
            "Add any comments, preferences, or make changes for your schedule:",
            key="additional_details"
        )

        if st.button("Submit Details", key="submit_details"):
            st.success("Your additional details have been submitted!")
            time.sleep(3)

            # Save this as an additional user preference (under the last question)
            uid = st.session_state.get("user_id")
            last_question = QUESTIONS[-1]
            save_preference(uid, last_question, additional_details)

            # Reload same page
            st.session_state.page = "gemini_answer"
            st.rerun()
