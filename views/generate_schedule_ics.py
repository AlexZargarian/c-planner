import re
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz

# --- Part 1: Parse the Gemini AI Response ---
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

# --- Part 2: Convert to .ics File ---
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

def create_ics_file(courses, filename='schedule.ics'):
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
            event.add('location', 'Your University')
            cal.add_component(event)

    with open(filename, 'wb') as f:
        f.write(cal.to_ical())

    print(f".ics file saved as: {filename}")

# --- Part 3: Run All Together ---
if __name__ == '__main__':
    gemini_text = """
    CHSS111 Introduction to Ethics (MON 3:30pm-4:20pm, WED 3:30pm-4:20pm, FRI 3:30pm-4:20pm, Arshak Balayan)
    BUS177 Business Communications, A (MON 10:30am-11:20am, WED 10:30am-11:20am, FRI 10:30am-11:20am, Kristine Sargsyan)
    CS110 Introduction to Computer Science, A (TUE 9:00am-10:20am, THU 9:00am-10:20am, Khachatur Virabyan)
    """

    courses = parse_schedule(gemini_text)
    create_ics_file(courses)
