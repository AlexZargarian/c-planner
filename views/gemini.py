import io
from pathlib import Path
from typing import Dict

import PyPDF2
import streamlit as st

from api_logic.gemini_api import process_pdf_with_gemini
from database import save_transcript, save_preference, save_degree_requirements

# Directory where degree requirement files are stored
DEGREE_DIR = Path("data") / "Degree Requirements"

# ──────────────────────────────
# Utility: Extracts plain text from uploaded PDF
# ──────────────────────────────
def extract_text_from_pdf(uploaded_file) -> str:
    try:
        rdr = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return "\n".join(p.extract_text() or "" for p in rdr.pages)
    except Exception as e:
        st.error(f"PDF-extract error: {e}")
        return ""

# ──────────────────────────────
# Predefined list of academic programs shown in dropdown
# ──────────────────────────────
PROGRAM_OPTIONS = [
    "BA in Business", "BS in Economics", "BA in English and Communications",
    "BA in Politics and Governance", "BS in Computer Science",
    "BS in Data Science", "BS in Engineering Sciences",
    "BS in Environmental and Sustainability Sciences", "BS in Nursing",
    "BS in Environmental Studies", "BS in Gender Studies",
    "BS in Genocide Studies and Human Rights", "BS in Philosophy",
    "BS in Philosophy, Politics, and Economics",
    "Master of Business Administration",
    "Master of Science in Management and Analytics",
    "Master of Science in Economics",
    "Master of Arts in Teaching English as a Foreign Language",
    "Master of Laws",
    "Master of Arts in Human Rights and Social Justice",
    "Master of Arts in International Relations and Diplomacy",
    "Master of Public Affairs",
    "Master of Arts in Multiplatform Journalism",
    "Master of Public Health",
    "Master of Engineering in Industrial Engineering and Systems Management",
    "Master of Science in Computer and Information Science",
]

# ──────────────────────────────
# Interview-like questions asked to the user
# ──────────────────────────────
QUESTIONS = [
    "👉 Please upload the PDF version of your official transcript...",
    "👉 What is your current academic program? (Select from the dropdown)",
    "👉 Which year of your studies are you currently in? ...",
    "👉 Are there any specific courses you’re hoping to take this semester?",
    "👉 Are there any instructors you'd prefer to avoid?",
    "👉 Are there any courses you definitely don’t want to take?",
    "👉 What time of day do you prefer having classes?",
    "👉 How many courses would you like to take this semester?",
    "👉 Do you prefer having classes mostly on MWF or TTH?",
    "👉 Is there any additional information you’d like to share?",
]
TOTAL_Q = len(QUESTIONS)

# ──────────────────────────────
# Dark theme overrides for widgets
# ──────────────────────────────
CSS = """
<style>
textarea, input {
    background:#242424 !important;
    color:white !important;
    caret-color:white !important;
}
div[data-testid="stSelectbox"] div[data-baseweb="select"],
div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
div[data-testid="stSelectbox"] span{
    background:#242424 !important;
    color:white !important;
}
</style>
"""

# ──────────────────────────────
# Save all answers from local session into the database
# ──────────────────────────────
def _persist_all_answers(uid: str, answers: Dict[int, str]) -> None:
    tr = answers.get(0)
    if tr:
        save_transcript(uid, tr)

    for idx, ans in answers.items():
        if idx == 0:
            continue
        txt = ans.strip() if ans else None
        save_preference(uid, QUESTIONS[idx], txt)
        if idx == 1 and txt:
            fp = DEGREE_DIR / (txt.replace(" ", "_").replace("/", "_") + ".txt")
            if fp.exists():
                save_degree_requirements(uid, txt, fp.read_text("utf-8"))

# ──────────────────────────────
# Final review page after all questions
# ──────────────────────────────
def review_page() -> None:
    s = st.session_state
    skipped = sorted(s.get("skipped", set()))
    saved   = sorted(s.get("saved", set()))

    st.header("📋 Review Your Responses")

    # Show skipped questions
    if skipped:
        st.warning("You skipped these questions:")
        st.markdown("\n".join(f"* {QUESTIONS[i]}" for i in skipped))
    else:
        st.success("All questions answered (or deliberately skipped).")

    c1, c2 = st.columns(2, gap="small")
    
    # Navigate to first skipped question
    with c1:
        if st.button("🔄 Go to skipped", key="goto_skipped", disabled=not skipped):
            s.current_q = skipped[0]
            st.rerun()

    # Submit all answers to DB
    with c2:
        if saved and not s.get("all_submitted"):
            if st.button("✅ Submit All Responses", key="submit_all"):
                uid = s.get("user_id")
                if not uid:
                    st.error("⚠️ Please sign in again.")
                else:
                    for idx in saved:
                        if idx == 0:
                            tr = s.answers.get(0)
                            if tr:
                                save_transcript(uid, tr)
                        else:
                            txt = s.answers.get(idx, "").strip() or None
                            save_preference(uid, QUESTIONS[idx], txt)
                            if idx == 1 and txt:
                                fp = DEGREE_DIR / (txt.replace(" ", "_").replace("/", "_") + ".txt")
                                if fp.exists():
                                    save_degree_requirements(uid, txt, fp.read_text("utf-8"))
                    s.all_submitted = True
                    st.success("🎉 All saved!")
                    st.balloons()
                    s.saved.clear()

        elif not saved and not s.get("all_submitted"):
            if st.button("➡️ Go to Generation (no data)", key="empty_gen"):
                s.prev_page = "gemini"
                s.page = "generation"
                st.rerun()

    # After submission, allow transition to generation
    if s.get("all_submitted"):
        st.divider()
        if st.button("➡️ Go to Generation", key="goto_generation"):
            s.prev_page = "gemini"
            s.page = "generation"
            st.rerun()

# ──────────────────────────────
# Main Gemini Questionnaire Page
# ──────────────────────────────
def gemini_page() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    s = st.session_state

    # Initialize session state variables
    s.setdefault("current_q", 0)
    s.setdefault("answers",   {})
    s.setdefault("saved",     set())
    s.setdefault("skipped",   set())
    s.setdefault("all_submitted", False)

    # Skip transcript if flagged
    if s.get("skip_transcript") and s.current_q == 0:
        s.current_q = 1

    # If done, go to review
    if s.current_q >= TOTAL_Q:
        review_page()
        return

    # Current question
    idx = s.current_q
    readonly = idx in s.saved
    key = f"A_{idx}"

    st.write(f"### {QUESTIONS[idx]}")

    # Question 0: Upload transcript
    if idx == 0 and not s.get("skip_transcript"):
        if readonly:
            st.success("Transcript uploaded ✅")
        else:
            def _on_upload():
                file = s.uploaded_file
                if file:
                    txt = process_pdf_with_gemini(extract_text_from_pdf(file))
                    if txt:
                        s.answers[0] = txt
                        st.success("✅ Transcript extracted.")
                    else:
                        st.error("⚠️ Couldn’t extract any text from the PDF.")
            st.file_uploader(
                "Upload your transcript (PDF)",
                type="pdf",
                key="uploaded_file",
                on_change=_on_upload,
            )
        s.answers[0] = st.text_area(
            "Your classes (edit if needed):",
            value=s.answers.get(0, ""),
            key=key,
            height=240,
            disabled=readonly,
        )

    # Question 1: Program dropdown
    elif idx == 1:
        if readonly:
            st.write(f"**{s.answers[1] or '_(skipped)_'}**")
        else:
            s.answers[1] = st.selectbox(
                "Select your program:", PROGRAM_OPTIONS,
                index=PROGRAM_OPTIONS.index(
                    s.answers.get(1, PROGRAM_OPTIONS[0])
                ) if s.answers.get(1) else 0,
                key=key,
            )

    # All other questions: Text input
    else:
        if readonly:
            st.write(s.answers.get(idx) or "_(skipped)_")
        else:
            s.answers[idx] = st.text_input(
                "Your answer:",
                value=s.answers.get(idx, ""),
                key=key,
            )

    # Navigation buttons
    back, save_col, next_col, change, skip = st.columns(5, gap="small")

    # Back button
    with back:
        if st.button("⬅️ Back", key=f"back_{idx}"):
            if idx == 0:
                s.page = "transcript_intro"
                s.current_q = 0
            else:
                if idx == 1 and s.get("skip_transcript"):
                    s.page = "transcript_intro"
                    s.current_q = 0
                else:
                    s.current_q -= 1
            st.rerun()

    # Save answer
    with save_col:
        if not readonly and st.button("💾 Save", key=f"save_{idx}"):
            if idx >= 2 and not s.answers.get(idx, "").strip():
                st.warning("Answer cannot be blank — type something or skip.")
            else:
                s.saved.add(idx)
                s.skipped.discard(idx)
                s.all_submitted = False
                st.success("Saved!")
                st.rerun()

    # Next question
    with next_col:
        disabled_next = idx not in s.saved
        if st.button("➡️ Next", key=f"next_{idx}", disabled=disabled_next):
            s.current_q += 1
            st.rerun()

    # Edit saved answer
    with change:
        if readonly and st.button("✏️ Change", key=f"chg_{idx}"):
            s.saved.discard(idx)
            s.all_submitted = False
            st.rerun()

    # Skip question
    with skip:
        if idx != 0 and not readonly and st.button("⏭️ Skip", key=f"skip_{idx}"):
            s.answers.pop(idx, None)
            s.skipped.add(idx)
            s.current_q += 1
            st.rerun()
