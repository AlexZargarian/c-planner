# ─────────────────────────  views/gemini_answer.py  ─────────────────────────
import streamlit as st
import re
import pandas as pd
from pathlib import Path

from database import transcript_exists, fetch_all_preferences
from views.generation import (
    generate_schedule,
    get_transcript_text,
    get_degree_requirements,
    degree_requirements_exists,
)

def gemini_answer_page() -> None:
    st.title("✨ Your Personalized Schedule")

    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    # 1) Ensure we actually have a generated schedule
    if "generated_schedule" not in st.session_state:
        st.error("No schedule has been generated yet. Please go back and generate one first.")
        if st.button("⬅️ Back to Generation"):
            st.session_state.page = "generation"
            st.rerun()
        return

    schedule = st.session_state.generated_schedule

    # 2) Display the schedule broken out by day if possible
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

    if not found_any:
        st.markdown(schedule)

    # 3) Show any final notes/rationale
    notes_match = re.search(r"(?i)(notes|explanation|recommendations|rationale):(.*)", schedule, re.DOTALL)
    if notes_match:
        st.markdown("### Notes")
        st.markdown(notes_match.group(2).strip())

    st.markdown("---")

    # 4) Action buttons
    col1, col2, col3 = st.columns(3, gap="small")

    # Back
    with col1:
        if st.button("⬅️ Back to Preferences"):
            st.session_state.page = "gemini"
            st.rerun()

    # Regenerate in place
    with col2:
        if st.button("🔄 Regenerate Schedule"):
            with st.spinner("🔮 Regenerating your schedule…"):
                # 1. courses.csv
                courses_file = Path("data") / "courses.csv"
                if not courses_file.exists():
                    st.error("Courses catalog not found!")
                    return
                courses_text = pd.read_csv(courses_file).to_csv(index=False)

                # 2. transcript
                tr_ok = transcript_exists(uid)
                transcript_text = get_transcript_text(uid) if tr_ok else ""

                # 3. degree reqs
                deg_ok = degree_requirements_exists(uid)
                degree_req = get_degree_requirements(uid) if deg_ok else ""

                # 4. preferences
                rows = fetch_all_preferences(uid)
                preferences = {
                    r["question"]: r.get("answer", "Not provided") for r in rows
                }

                # call the same generator
                new_schedule = generate_schedule(
                    courses_text,
                    transcript_text,
                    degree_req,
                    preferences
                )
                st.session_state.generated_schedule = new_schedule

            # re-render the page with the new schedule
            st.rerun()

    # Save or update in DB
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
