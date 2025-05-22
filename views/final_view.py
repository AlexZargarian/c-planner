import streamlit as st
import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
from database import get_schedule

def parse_schedule(text):
    courses = []
    lines = text.strip().split('\n')

    for line in lines:
        if not line.strip():
            continue

        match = re.match(r'(.+?)\s\((.+?)\)', line)
        if not match:
            continue

        name, details = match.groups()
        parts = [p.strip() for p in details.split(',')]
        
        sessions = []
        instructor = ""

        for part in parts:
            # Day + Time e.g. MON 3:30pm-4:20pm
            if re.match(r'^[A-Z]{3}', part):
                day, time = part.split(' ', 1)
                sessions.append((day.upper(), time))
            else:
                instructor = part

        courses.append({
            "name": name.strip(),
            "sessions": sessions,
            "instructor": instructor.strip()
        })

    return courses

def time_str_to_datetime(time_str, day):
    day_map = {
        'MON': 0, 'TUE': 1, 'WED': 2,
        'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
    }

    start_time, end_time = time_str.split('-')
    dt_format = "%I:%M%p"
    start_dt = datetime.strptime(start_time.strip().lower(), dt_format)
    end_dt = datetime.strptime(end_time.strip().lower(), dt_format)

    today = datetime.today()
    start_date = today + timedelta(days=(day_map[day] - today.weekday()) % 7)
    start_datetime = datetime.combine(start_date.date(), start_dt.time())
    end_datetime = datetime.combine(start_date.date(), end_dt.time())

    return start_datetime, end_datetime

def create_ics_bytes(courses):
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
        - Import this schedule into your calendar.

        We wish you a successful and fulfilling semester ahead!  
        If you need further assistance, feel free to reach out to your academic advisor.

        _Thank you for using C-Planner!_
    """)

    if st.button("⬅️ Go back to home"):
        st.session_state.page = "session_choice"

    # Create a downloadable ICS file from the schedule text
    courses = parse_schedule(schedule)
    ics_bytes = create_ics_bytes(courses)

    st.download_button(
        label="📥 Import to Calendar",
        data=ics_bytes,
        file_name="semester_schedule.ics",
        mime="text/calendar"
    )
