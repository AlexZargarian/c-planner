#!/usr/bin/env python3
"""
cleanAndmerger.py

Reads 'automated_scrape_jenzabar.csv', cleans and transforms
course data, adds year and semester, and writes out 'final_schedule.csv'.
"""

import pandas as pd
import re
import sys
import os
from datetime import datetime, timedelta

DEFAULT_PREREQ = "No restrictions, except that any prerequisites must already be completed"

MAJOR_MAP = {
    "BSN": "Nursing Program's core or track elective course",
    "BUS": "Business Program's core or track elective course",
    "CHSS": "General Education course",
    "CS": "Computer Science Program's core or track elective course",
    "DS": "Data Science Program's core or track elective course",
    "CSE": "General Education course",
    "EC": "English and Communications Program's core or track elective course",
    "ECM": "ECM Program's core or track elective course",
    "ECON": "Economics Program's core or track elective course",
    "ENGS": "Engineering Sciences Program's core or track elective course",
    "ENV": "Environmental and Sustainability Sciences Program's core or track elective course",
    "ESS": "Environmental and Sustainability Sciences Program's core or track elective course",
    "FND": "General Education course",
    "HHM": "HHM Program's core or track elective course",
    "HRSJ": "Human Rights and Social Justice Program's core or track elective course",
    "IESM": "Industrial Engineering and Systems Management Program's core or track elective course",
    "IRD": "International Relations and Diplomacy Program's core or track elective course",
    "LAW": "Laws Program's core or track elective course",
    "MGMT": "MGMT Program's core or track elective course",
    "PA": "Public Affairs Program's core or track elective course",
    "PEER": "Peer Mentoring course",
    "PG": "Politics and Governance Program's core or track elective course",
    "PH": "Public Health Program's core or track elective course",
    "PSIA": "Political Science and International Affairs Program's core or track elective course",
    "TEFL": "Teaching English as a Foreign Language Program's core or track elective course",
    "CBE": "CBE Program's core or track elective course"
}

def get_school_year_and_semester():
    """
    Compute current academic year string and semester code:
      - 1: Fall
      - 2: Spring
      - 3: Summer
    """
    today = datetime.now().date()
    year = today.year
    # Academic year starting in fall
    start = year if today.month >= 8 else year - 1
    school_year_str = f"{start}{str(start + 1)[2:]}"

    # Determine semester by month:
    # Aug(8)–Dec(12) → Fall (1)
    # Jan(1)–Apr(4) → Spring (2)
    # May(5)–Jul(7) → Summer (3)
    month = today.month
    if 8 <= month <= 12:
        sem_value = 1
    elif 1 <= month <= 4:
        sem_value = 2
    else:
        sem_value = 3

    return school_year_str, sem_value

def get_course_level(code: str) -> str:
    m = re.search(r'(\d+)', str(code))
    if not m:
        return 'Unknown'
    first_digit = m.group(1)[0]
    return {'1': 'Lower level', '2': 'Upper level', '3': 'Masters level'}.get(first_digit, 'Unknown')

def get_course_type(code: str) -> str:
    m = re.match(r'^([A-Za-z]+)', str(code))
    if not m:
        return 'Unknown'
    return MAJOR_MAP.get(m.group(1).upper(), 'Unknown')

def main():
    input_csv = 'automated_scrape_jenzabar.csv'
    output_csv = 'final_schedule.csv'

    if not os.path.isfile(input_csv):
        print(f"Error: cannot find '{input_csv}'", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_csv)

    # 1) Clean title
    df['course_title'] = (
        df['course_title'].astype(str)
          .str.replace(r'\(Prerequisite\)', '', regex=True)
          .str.strip()
    )

    # 2) Extract code
    df['course_code'] = df['course_title'].str.extract(r'\(([^)]*)\)\s*$', expand=False)

    # 3) Strip parentheses from title
    df['course_title'] = (
        df['course_title']
          .str.replace(r'\s*\([^)]*\)\s*$', '', regex=True)
          .str.strip()
    )

    # 4) Compute level & type
    df['course_level'] = df['course_code'].apply(get_course_level)
    df['course_type']  = df['course_code'].apply(get_course_type)

    # 5) Populate 'prerequisites'
    col = 'prerequisites'
    if col not in df.columns:
        df[col] = DEFAULT_PREREQ
    else:
        df[col] = df[col].fillna('').astype(str).apply(
            lambda x: x if x.strip() else DEFAULT_PREREQ
        )

    # 6) Fill missing times with "TBD"
    if 'times' in df.columns:
        df['times'] = df['times'].fillna('TBD').astype(str)

    # 7) Add year & semester columns
    year_str, sem_value = get_school_year_and_semester()
    df['year'] = year_str
    df['semester'] = sem_value

    # 8) Reorder columns
    desired_order = [
        'course_title', 'course_code', 'prerequisites', 'section', 'session',
        'campus', 'instructor', 'times', 'location', 'course_description',
        'themes', 'restriction', 'course_level', 'course_type', 'year', 'semester'
    ]
    cols_to_save = [c for c in desired_order if c in df.columns]
    df = df[cols_to_save]

    # 9) Write out
    df.to_csv(output_csv, index=False)
    print(f"Wrote final_schedule.csv with columns: {', '.join(cols_to_save)}")

if __name__ == '__main__':
    main()
