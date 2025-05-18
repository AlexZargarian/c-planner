import io
import streamlit as st
import PyPDF2

from api_logic.gemini_api import process_pdf_with_gemini  # import your API logic
from database import save_transcript                         # ← new import

def extract_text_from_pdf(uploaded_file) -> str:
    """Extract raw text from an uploaded PDF."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def gemini_page():
    """Main questionnaire page with PDF→Gemini→Text‐area on question #1."""

    # ─── CSS for styling inputs, notifications & uploader ─────────────
    st.markdown("""
    <style>
    /* Text inputs & areas */
    .stTextInput input, .stTextArea textarea {
        background-color: white !important;
        color: black !important;
    }
    /* Notifications (success, error, info, warning) */
    .stSuccess, .stError, .stWarning, .stInfo, .stException,
    div.stAlert, [data-baseweb="notification"] div {
        color: black !important;
    }
    /* FileUploader container & button */
    div[data-testid="stFileUploader"] {
        background-color: white !important;
        color: black !important;
        border: 1px solid #ccc !important;
        padding: 10px !important;
    }
    div[data-testid="stFileUploader"] button {
        background-color: white !important;
        color: black !important;
        border: 1px solid #999 !important;
    }
    /* Uploaded file name & size */
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] p {
        background-color: white !important;
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # ─── Define your questions ───────────────────────────────────────
    questions = [
        "1. Please insert the classes you have taken:",
        "2. Which faculty are you from?",
        "3. What year are you in (e.g., 2nd year)?",
        "4. Are there any specific courses you would like to take?",
        "5. Are there any instructors you want to avoid?",
        "6. Are there any classes you definitely do not want?",
        "7. At what times do you prefer to have classes (are evenings okay)?",
        "8. How many classes would you like to take this term?",
        "9. Do you prefer more classes on MWF or TTH?"
    ]
    total_q = len(questions)

    # ─── Session-state init ───────────────────────────────────────────
    if "current_q" not in st.session_state:
        st.session_state.current_q = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    curr = min(st.session_state.current_q, total_q - 1)
    key  = f"answer_{curr}"
    if key not in st.session_state:
        st.session_state[key] = st.session_state.answers.get(curr, "")

    # ─── Show current question ────────────────────────────────────────
    st.write(questions[curr])

    # ─── Q1: PDF uploader + processing ──────────────────────────────
    if curr == 0:
        def _on_upload():
            pdf = st.session_state.uploaded_file
            if pdf is not None:
                with st.spinner("Processing PDF…"):
                    raw     = extract_text_from_pdf(pdf)
                    cleaned = process_pdf_with_gemini(raw)
                    st.session_state[key]       = cleaned
                    st.session_state.answers[0] = cleaned
                    st.success(f"✅ Processed {pdf.name}")

        st.file_uploader(
            "Upload your transcript (PDF)",
            type="pdf",
            key="uploaded_file",
            on_change=_on_upload
        )

        user_text = st.text_area(
            "Your classes (edit if needed):",
            key=key,
            height=200
        )
        st.session_state.answers[0] = user_text

    else:
        # ─── Other questions ────────────────────────────────────────
        answer = st.text_input("Your answer:", key=key)
        st.session_state.answers[curr] = answer

    # ─── Navigation buttons ─────────────────────────────────────────
    back_col, next_col = st.columns(2)
    if curr > 0 and back_col.button("Back", key=f"back_{curr}"):
        st.session_state.current_q = curr - 1
    if curr < total_q - 1:
        if next_col.button("Submit", key=f"next_{curr}"):
            # ── Save transcript early if we're on Q1 ─────────────
            if curr == 0:
                final_transcript = st.session_state.answers.get(0, "").strip()
                user_id = st.session_state.get("user_id")
                if user_id:
                    try:
                        save_transcript(user_id, final_transcript)
                        st.success("✅ Transcript saved.")
                    except Exception as e:
                        st.error(f"Error saving transcript: {e}")
                else:
                    st.error("No user in session; please log in again.")
            # ───────────────────────────────────────────────────────
            st.session_state.current_q = curr + 1
    else:
        if next_col.button("Finish", key="finish"):
            # 1) grab the cleaned transcript text
            final_transcript = st.session_state.answers.get(0, "").strip()
            # 2) get the logged-in user’s ID
            user_id = st.session_state.get("user_id")
            if not user_id:
                st.error("No user in session—please log in again.")
            else:
                try:
                    save_transcript(user_id, final_transcript)
                    st.success("✅ Your transcript has been saved.")
                except Exception as e:
                    st.error(f"Error saving transcript: {e}")

    # ─── Log Out ───────────────────────────────────────────────────
    if st.button("Log Out"):
        st.session_state.clear()
        st.session_state.page = "login"
