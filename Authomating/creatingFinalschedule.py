#!/usr/bin/env python3
"""
full_schedule_builder.py

Reads 'jenzabar_courses_all_pages.csv', cleans and transforms
the course titles to extract course codes, levels, types, prerequisites, and
then writes out 'final_schedule.csv' with columns in the specified order.
"""

import pandas as pd
import re
import sys
import os

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

def get_course_level(code: str) -> str:
    m = re.search(r'(\d+)', str(code))
    if not m:
        return 'Unknown'
    first_digit = m.group(1)[0]
    return {'1':'Lower level','2':'Upper level','3':'Masters level'}.get(first_digit, 'Unknown')

def get_course_type(code: str) -> str:
    m = re.match(r'^([A-Za-z]+)', str(code))
    if not m:
        return 'Unknown'
    return MAJOR_MAP.get(m.group(1).upper(), 'Unknown')

def main():
    input_csv = 'jenzabar_courses_all_pages.csv'
    output_csv = 'final_schedule.csv'
    if not os.path.isfile(input_csv):
        print(f"Error: cannot find '{input_csv}'", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_csv)

    # clean title
    df['course_title'] = (
        df['course_title'].astype(str)
        .str.replace(r'\(Prerequisite\)', '', regex=True)
        .str.strip()
    )

    # extract code
    df['course_code'] = df['course_title'].str.extract(r'\(([^)]*)\)\s*$', expand=False)

    # strip off the parentheses from title
    df['course_title'] = (
        df['course_title']
        .str.replace(r'\s*\([^)]*\)\s*$', '', regex=True)
        .str.strip()
    )

    # level & type
    df['course_level'] = df['course_code'].apply(get_course_level)
    df['course_type']  = df['course_code'].apply(get_course_type)

    # prerequisites
    col = 'prerequisites'
    if col not in df:
        df[col] = DEFAULT_PREREQ
    else:
        df[col] = df[col].fillna('').astype(str).apply(
            lambda x: x if x.strip() else DEFAULT_PREREQ
        )

    # reorder columns
    desired_order = [
        'course_title',
        'course_code',
        'prerequisites',
        'section',
        'session',
        'campus',
        'instructor',
        'times',
        'location',
        'course_description',
        'themes',
        'restriction',
        'course_level',
        'course_type'
    ]
    # keep only the intersection in case some columns are missing
    cols_to_save = [c for c in desired_order if c in df.columns]
    df = df[cols_to_save]

    df.to_csv(output_csv, index=False)
    print(f"Wrote final_schedule.csv with columns: {', '.join(cols_to_save)}")

if __name__ == '__main__':
    main()
