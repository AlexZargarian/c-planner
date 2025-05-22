# ─────────────────────────  views/final_view.py  ─────────────────────────


import streamlit as st
import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
from database import get_schedule
from api_logic.gemini_api import process_with_gemini

def parse_schedule(text):
    """
    Parses the AI-generated schedule string into structured course data.

    Args:
        text (str): Schedule string containing course names, meeting days/times, and instructors.

    Returns:
        list: A list of dictionaries, each containing:
            - name (str): Course name.
            - sessions (list): List of tuples (day, time_range).
            - instructor (str): Instructor's name.
    """
    courses = []
    lines = text.strip().split('\n')

    for line in lines:
        if not line.strip():
            continue  # Skip empty lines

        # Match pattern: Course Name (MON 3:30pm-4:20pm, Instructor Name)
        match = re.match(r'(.+?)\s\((.+?)\)', line)
        if not match:
            continue

        name, details = match.groups()
        parts = [p.strip() for p in details.split(',')]
        
        sessions = []
        instructor = ""

        for part in parts:
            if re.match(r'^[A-Z]{3}', part):  # It's a day/time session
                day, time = part.split(' ', 1)
                sessions.append((day.upper(), time))
            else:
                instructor = part  # Remaining part is instructor

        courses.append({
            "name": name.strip(),
            "sessions": sessions,
            "instructor": instructor.strip()
        })

    return courses

def time_str_to_datetime(time_str, day):
    """
    Converts a time range string and day abbreviation to datetime objects for the upcoming week.

    Args:
        time_str (str): Time range (e.g., '3:30pm-4:20pm').
        day (str): Three-letter day abbreviation (e.g., 'MON').

    Returns:
        tuple: A tuple containing:
            - start_datetime (datetime): Start time.
            - end_datetime (datetime): End time.
    """
    day_map = {
        'MON': 0, 'TUE': 1, 'WED': 2,
        'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
    }

    start_time, end_time = time_str.split('-')
    dt_format = "%I:%M%p"
    start_dt = datetime.strptime(start_time.strip().lower(), dt_format)
    end_dt = datetime.strptime(end_time.strip().lower(), dt_format)

    today = datetime.today()
    # Calculate the next occurrence of the given day
    start_date = today + timedelta(days=(day_map[day] - today.weekday()) % 7)
    start_datetime = datetime.combine(start_date.date(), start_dt.time())
    end_datetime = datetime.combine(start_date.date(), end_dt.time())

    return start_datetime, end_datetime

def create_ics_bytes(courses):
    """
    Creates an .ics calendar file in byte format from a list of structured courses.

    Args:
        courses (list): List of dictionaries with keys 'name', 'sessions', and 'instructor'.

    Returns:
        bytes: Byte representation of the calendar file (.ics format).
    """
    cal = Calendar()
    cal.add('prodid', '-//University Course Planner//Gemini AI//')
    cal.add('version', '2.0')

    timezone = pytz.timezone('Asia/Yerevan')

    for course in courses:
        for day, time in course['sessions']:
            start_dt, end_dt = time_str_to_datetime(time, day)

            event = Event()
            event.add('summary', course['name'])
            event.add('description', f"Instructor: {course['instructor']}")
            event.add('dtstart', timezone.localize(start_dt))
            event.add('dtend', timezone.localize(end_dt))
            event.add('rrule', {'freq': 'weekly'})
            event.add('location', 'University Campus')
            cal.add_component(event)

    return cal.to_ical()

def final_view_page():
    st.title("🎓 Your Personalized Semester Plan is Ready!")
    st.write("""
        Congratulations! 🎉

        Your custom semester schedule has been generated based on your preferences, degree requirements, and academic history.
        
        Below you’ll find your recommended schedule—and a verified, regex‐friendly version to power the calendar export.
    """)

    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    # 1) Fetch the raw saved schedule from the DB
    raw_schedule = get_schedule(uid) or ""
    if not raw_schedule.strip():
        st.error("No saved schedule found. Please generate one first.")
        if st.button("⬅️ Back to Generation"):
            st.session_state.page = "generation"
            st.rerun()
        return

    # 2) Show the raw version
    st.markdown("### Original Schedule Text")
    st.markdown(f"<pre>{raw_schedule}</pre>", unsafe_allow_html=True)

    # 3) Ask Gemini to reformat strictly for our regex parser
    with st.spinner("🔍 Verifying & reformatting schedule…"):
        verify_prompt = f"""
You are a precise formatter. 
Take the following schedule and output **only** lines in this exact pattern:

Course Name (DAY TIME-RANGE, Instructor)

- DAY must be a three-letter uppercase abbreviation (e.g. MON, TUE, WED, THU, FRI).
- Keep each day of the class as a seperate record. Do not write for example MWF or TTH.
- TIME-RANGE in 12-hour format with am/pm, e.g. 3:30pm-4:20pm.
- Instructor name after the comma.
- Do NOT add any extra text, numbering, or bullets—just one course per line.

Schedule to reformat:
{raw_schedule}
"""
        verified = process_with_gemini(verify_prompt).strip()

    # 4) Display the Gemini‐verified version
    st.markdown("### Reformatted Schedule (for parsing)")
    st.code(verified)

    # 5) Parse and build the .ics file
    courses = parse_schedule(verified)
    if not courses:
        st.error("Could not parse any courses—please check your schedule format.")
    else:
        ics_bytes = create_ics_bytes(courses)

        st.markdown("---")
        st.download_button(
            label="📥 Import to Calendar",
            data=ics_bytes,
            file_name="semester_schedule.ics",
            mime="text/calendar"
        )

        # 6) Navigation
    st.markdown("---")
    col1, _ = st.columns(2, gap="small")

    with col1:
        if st.button("⬅️ Back to home"):
            st.session_state.page = "session_choice"
            st.rerun()

