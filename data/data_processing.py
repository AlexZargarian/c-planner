"""
data_processing.py

Loads raw course data from JSON, cleans and transforms it, and enriches with:
  - Default filling for key fields
  - Extraction of enrollment restrictions
  - Assignment of course levels (Lower/Upper/Masters/Other)
  - Mapping of course codes to full course-type descriptions

Finally, writes the fully enriched table out to courses.csv.
"""

import json
import pandas as pd
import re
import ast
from typing import List, Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
json_path = DATA_DIR / "courses.json"

def load_and_clean_courses(json_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load courses from a JSON file, compute missing-value summary,
    fill default texts, drop unwanted columns, transform themes into
    human-readable sentences (in-place), and return cleaned DataFrame
    plus the missing-value summary DataFrame.
    """
    # load & normalize
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.json_normalize(data)

    # empty strings → NA
    df = df.replace('', pd.NA)

    # missing-value summary
    missing_counts = df.isna().sum()
    missing_pct = (missing_counts / len(df) * 100).round(2)
    missing_df = (
        pd.DataFrame({
            'column': missing_counts.index,
            'missing_count': missing_counts.values,
            'missing_pct':   missing_pct.values
        })
        .sort_values('missing_pct', ascending=False)
        .reset_index(drop=True)
    )

    # fill defaults
    df['prerequisites']      = df['prerequisites'].fillna("No prerequisite(s) for this course")
    df['session']            = df['session'].fillna("Not specified")
    df['times']              = df['times'].fillna("Not specified")
    df['location']           = df['location'].fillna("Not specified")
    df['course_description'] = df['course_description'].fillna("Not specified")

    # cast types
    # df["credits"]   = df["credits"].astype(int)
    df["year"]      = df["year"].astype(int)
    df["semester"]  = df["semester"].astype(int)

    # drop unwanted columns
    df = df.drop(columns=['taken_seats', 'spaces_waiting', 'delivery_method', 'dist_learning'],
                 errors='ignore')

    # transform themes column in-place
    def describe_themes(cell):
        # parse string repr if needed
        lst = ast.literal_eval(cell) if isinstance(cell, str) else cell
        if not lst:
            return "Not part of any theme"
        if len(lst) == 1:
            return f"This course belongs to theme {lst[0]}."
        return f"This course belongs to themes {', '.join(map(str, lst))}."

    df['themes'] = df['themes'].apply(describe_themes)

    return df, missing_df




def extract_restrictions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scans df['course_description'] for true restriction clauses (e.g. "Not open to…",
    "[not open to…]", or full sentences containing 'not'), filters out false-positives,
    extracts the relevant snippet into a new column 'restriction', and fills in
    'No restriction' where nothing was found.
    """
    # 1) Work on a copy so we don’t modify the original
    out = df.copy()

    # 2) Build mask of rows that contain a standalone "not"
    has_not = out['course_description'].str.contains(
        r'\bnot\b', flags=re.IGNORECASE, na=False, regex=True
    )

    # 3) Exclude generic 'not' phrases that aren’t real restrictions
    exclusions = [
        r'\bNot specified\b',
        r'Note:',
        r'\bnot limited\b',
        r'\bnot covered by other\b',
        r'\bnot necessarily\b',
        r'\bshaped not\b',
        r'does not meet'
    ]
    excl_pattern = "|".join(exclusions)
    is_false_positive = out['course_description'].str.contains(
        excl_pattern, flags=re.IGNORECASE, na=False, regex=True
    )

    # 4) Final boolean mask of rows to examine
    mask = has_not & ~is_false_positive

    # 5) Define regexes to capture the usual restriction patterns
    patterns = [
        # full clause around "not as a general education course", etc.
        re.compile(r'([^.]*\bnot as [^.\)\]]+\b[^.]*)', re.IGNORECASE),
        # classic "Not open to …" or "Not available to …"
        re.compile(r'(Not open to [^.\)\]]+)(?:[.\)\]]|$)', re.IGNORECASE),
        re.compile(r'(Not available to [^.\)\]]+)(?:[.\)\]]|$)', re.IGNORECASE),
        # bracketed "[not open to …]"
        re.compile(r'\[([^\]]*not open to[^\]]*)\]', re.IGNORECASE),
    ]

    # 6) Loop through each description, extract the first matching snippet
    restrictions: list[Optional[str]] = []
    for desc, keep in zip(out['course_description'].fillna(""), mask):
        if not keep:
            restrictions.append(None)
            continue

        snippet: Optional[str] = None
        # 6a) Try each pattern in turn
        for pat in patterns:
            m = pat.search(desc)
            if m:
                # Prefer the first capture group if present
                snippet = m.group(1) if m.lastindex else m.group(0)
                snippet = snippet.strip()
                break

        # 6b) Fallback: grab the entire sentence containing ' not ' if nothing matched
        if snippet is None:
            for sentence in re.split(r'(?<=[.?!])\s+', desc):
                if (re.search(r'\bnot\b', sentence, flags=re.IGNORECASE)
                    and not re.search(excl_pattern, sentence, flags=re.IGNORECASE)):
                    snippet = sentence.strip()
                    break

        restrictions.append(snippet)

    # 7) Append to DataFrame
    out['restriction'] = restrictions

    # 8) Fill all None/NaN with "No restriction"
    out['restriction'] = out['restriction'].fillna("No restrictions, except that any prerequisites must already be completed")

    return out




def assign_course_level(code: str) -> str:
    """
    Determine the Course Level based on the first digit in the course code:
      - "Lower level"   if the first digit is 1
      - "Upper level"   if the first digit is 2
      - "Masters level" if the first digit is 3
      - "Other"         if the first digit is 0
      - "Corequisite level" if the code equals "Corequisite" (case-insensitive)
      - "Unknown level" otherwise
    """
    if not isinstance(code, str):
        return "Unknown level"

    # Special case: Corequisite
    if code.strip().lower() == "corequisite":
        return "Corequisite level"

    # Find the first digit in the code
    m = re.search(r'\d', code)
    if not m:
        return "Unknown level"
    first_digit = m.group(0)

    # Map first digit to level
    level_map = {
        '0': "Other",
        '1': "Lower level",
        '2': "Upper level",
        '3': "Masters level"
    }
    return level_map.get(first_digit, "Unknown level")


def assign_course_type(code: str) -> str:
    """
    Extract the alphabetic prefix of the course code and map it to its full major name.
    If the prefix is not in the mapping, return the prefix itself.
    """
    if not isinstance(code, str):
        return "Unknown major"

    # ── Handle Corequisite explicitly ──────────────────────
    if code.strip().lower() == "corequisite":
        return "Corequisite course"
    
    # Extract leading letters
    m = re.match(r'^([A-Za-z]+)', code)
    prefix = m.group(1).upper() if m else code.upper()

    # Mapping of prefix → full major name
    major_map = {
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

    return major_map.get(prefix, prefix)



def enrich_courses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes a cleaned DataFrame, appends 'restriction', 'Course Level', and 'Major',
    and returns the enriched copy.
    """
    df2 = extract_restrictions(df)
    df2['course_level']  = df2['course_code'].apply(assign_course_level)
    df2['course_type']   = df2['course_code'].apply(assign_course_type)
    return df2


output_csv = DATA_DIR / "courses.csv"

df_clean, missing = load_and_clean_courses(json_path)
df_final = enrich_courses(df_clean)

df_final.to_csv(output_csv, index=False, encoding='utf-8')