# ──────────────────────────── views/generation.py ───────────────────────────
import streamlit as st
import pandas as pd
from pathlib import Path
from database import transcript_exists, fetch_all_preferences, get_db_connection
from views.gemini import QUESTIONS


# Check if degree requirements exist for the given user
def degree_requirements_exists(user_id: int) -> bool:
    sql = "SELECT 1 FROM degreqs WHERE user_id = %s LIMIT 1"
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        return cur.fetchone() is not None


# Fetch the degree requirement text for a given user
def get_degree_requirements(user_id: int) -> str:
    sql = "SELECT requirements FROM degreqs WHERE user_id = %s LIMIT 1"
    with get_db_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        return result["requirements"] if result else ""


# Fetch the most recent transcript for the user
def get_transcript_text(user_id: int) -> str:
    sql = (
        "SELECT transcript FROM transcripts WHERE user_id = %s "
        "ORDER BY created_at DESC LIMIT 1"
    )
    with get_db_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        return result["transcript"] if result else ""


# Main page function to display the generation screen
def generation_page() -> None:
    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    st.title("🔮 Generating Your Personalized Schedule")
    st.write("Now, Gemini will craft your personalized schedule based on your provided data.")
    st.markdown("---")
    st.subheader("Summary of Provided Data")

    # Helper to show checkmark if item exists
    mark = lambda ok: "✅" if ok else "➖"

    # Check and show transcript status
    tr_ok = transcript_exists(uid)
    st.write(f"{mark(tr_ok)} Transcript")

    # Check and show degree requirements status
    deg_ok = degree_requirements_exists(uid)
    st.write(f"{mark(deg_ok)} Degree requirements")

    # Check and show questionnaire responses
    rows = fetch_all_preferences(uid)
    answered = {r["question"] for r in rows}
    st.markdown("**Questionnaire Responses:**")
    for q in QUESTIONS[1:]:  # skip first question (likely introductory or hidden)
        st.write(f"{mark(q in answered)} {q}")

    st.markdown("---")

    # Navigation columns
    prev = st.session_state.get("prev_page", "gemini")
    back_col, gen_col = st.columns([1, 1], gap="small")

    # Back button logic
    with back_col:
        if st.button("⬅️ Back", key="gen_back"):
            st.session_state.page = "resume" if prev == "resume" else "gemini"
            st.rerun()

    # Generate button logic
    with gen_col:
        if st.button("🧙‍♂️ Generate my Schedule", key="gen_submit"):
            with st.spinner("✨ Generating your personalized schedule..."):
                try:
                    # Step 1: Load courses.csv file
                    courses_file = Path("data") / "courses.csv"
                    if not courses_file.exists():
                        st.error("Courses data file not found!")
                        return

                    courses_data = pd.read_csv(courses_file)
                    courses_text = courses_data.to_csv(index=False)

                    # Step 2: Fetch transcript (if available)
                    transcript_text = get_transcript_text(uid) if tr_ok else ""

                    # Step 3: Fetch degree requirements (if available)
                    degree_req = get_degree_requirements(uid) if deg_ok else ""

                    # Step 4: Collect user preferences from the questionnaire
                    preferences = {row["question"]: row.get("answer", "Not provided") for row in rows}

                    # Step 5: Generate schedule using Gemini
                    schedule = generate_schedule(
                        courses_text,
                        transcript_text,
                        degree_req,
                        preferences
                    )

                    # Step 6: Save schedule and go to next page
                    st.session_state.generated_schedule = schedule
                    st.session_state.page = "gemini_answer"
                    st.rerun()

                except Exception as e:
                    st.error(f"Error generating schedule: {e}")


# Main function to build prompt and call Gemini API
def generate_schedule(courses_data, transcript_text, degree_requirements, preferences, prev_schedule=None):
    """
    This function builds a comprehensive prompt using:
    - The available courses
    - Student’s past transcript
    - Degree requirements
    - Student’s time/preferences
    - (Optionally) Previous schedule
    It sends the prompt to Gemini and returns its response.
    """
    from api_logic.gemini_api import process_with_gemini

    # Prompt construction for Gemini
    prompt = f"""
You are an expert academic advisor. Below is all the data you need.

AVAILABLE COURSES:
{courses_data}

ALREADY TAKEN:
{transcript_text or 'None'}

DEGREE REQUIREMENTS:
{degree_requirements or 'None'}

STUDENT PREFERENCES:
"""
    if preferences:
        for question, answer in preferences.items():
            prompt += f"- {question.strip('👉 ')}: {answer}\n"
    prompt += "\n"

    # Required format and strict instructions for Gemini output
    prompt += f"""
IMPORTANT - YOUR RESPONSE MUST FOLLOW THIS EXACT FORMAT:

1. **Your Recommended Schedule**
2. **Factors Considered:**
* Fulfils degree requirements
* Adheres to time preferences
* Considers courses available in the current semester
* Avoids courses already taken
* Ensures no time conflicts between selected courses
* For courses with multiple sections, select the section that best fits the student's schedule; do not offer multiple options.
* Include day abbreviations (e.g., MON, TUE, WED, THU, FRI) before times.
* Adheres as closely as possible to student preferences

3. **Schedule**
List each recommended course on its own bullet line. Do NOT merge alternatives into one line; pick only one course or section.

Example format:
* CS310 Theory of Computing (TT, 10:30am-11:20am, Suren Khachatryan) - Core
* CS340 Machine Learning (MWF, 10:30am-11:20am, Monika Stepanyan) - Core

General guidelines:
1. Don't recommend courses already taken.
2. Prioritize degree requirements.
3. Respect time preferences and constraints.
4. Ensure no time conflicts.
5. Pick one course per requirement; no combined choices.
6. For courses with multiple sections, choose the best fitting section.
7. Include day abbreviations before times.
8. Balance course load appropriately.
"""

    # If there's a previous schedule, ask Gemini to improve on it
    if prev_schedule:
        prompt += f"\nConsider following schedule provided by you.:\n{prev_schedule}\n"
        prompt += f"\nMake sure to follow user preferences to create a new schedule.\n"

    # Call Gemini API with the constructed prompt
    return process_with_gemini(prompt)
