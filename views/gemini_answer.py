# ─────────────────────────  views/gemini_answer.py  ─────────────────────────
import streamlit as st
import re


def gemini_answer_page() -> None:
    st.title("✨ Your Personalized Schedule")

#
    # Check if schedule has been generated
    if "generated_schedule" not in st.session_state:
        st.error("No schedule has been generated yet. Please go back and generate a schedule first.")
        if st.button("⬅️ Back to Generation"):
            st.session_state.page = "generation"
            st.rerun()
        return

    # Get generated schedule from session state
    schedule = st.session_state.generated_schedule

    # Display the schedule
    st.markdown("### Your Recommended Schedule")

    # Styling container
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

    # Days of the week to extract
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    # Try to split the response by days
    found_any = False
    for day in days:
        # regex to capture day section
        pattern = rf"(?i){day}[:\s]+(.*?)(?=(?:{'|'.join(days)})[:\s]+|\Z)"
        match = re.search(pattern, schedule, re.DOTALL)
        if match:
            found_any = True
            st.markdown(f"#### {day}")
            # split lines into courses
            courses = [line.strip() for line in match.group(1).splitlines() if line.strip()]
            if courses:
                for course in courses:
                    st.markdown(f"<div class='course-item'>{course}</div>", unsafe_allow_html=True)
            else:
                st.write("No classes scheduled")

    # If no day headings found, print raw markdown
    if not found_any:
        st.markdown(schedule)

    # Notes / explanation section
    explanation = re.search(r"(?i)(notes|explanation|recommendations|rationale):(.*)", schedule, re.DOTALL)
    if explanation:
        st.markdown("### Notes")
        st.markdown(explanation.group(2).strip())

    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬅️ Back to Preferences"):
            st.session_state.page = "gemini"
            st.rerun()
    with col2:
        if st.button("🔄 Regenerate Schedule"):
            st.session_state.page = "generation"
            st.rerun()
    with col3:
        if st.button("💾 Save Schedule"):
            # future DB save logic here
            st.success("Schedule saved!")


