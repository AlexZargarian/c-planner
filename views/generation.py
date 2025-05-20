# ──────────────────────────── views/generation.py ───────────────────────────
import streamlit as st
from database import transcript_exists, fetch_all_preferences, get_db_connection
from views.gemini import QUESTIONS

def degree_requirements_exists(user_id: int) -> bool:
    """Return True if the user has a row in degreqs."""
    sql = "SELECT 1 FROM degreqs WHERE user_id = %s LIMIT 1"
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        return cur.fetchone() is not None

def generation_page() -> None:
    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    st.title("🔮 Generating Your Personalized Schedule")
    st.write(
        "Now, Gemini will craft your personalized schedule based on your provided data."
    )
    st.markdown("---")
    st.subheader("Summary of Provided Data")

    mark = lambda ok: "✅" if ok else "➖"

    # Transcript
    tr_ok = transcript_exists(uid)
    st.write(f"{mark(tr_ok)} Transcript")

    # Degree requirements
    deg_ok = degree_requirements_exists(uid)
    st.write(f"{mark(deg_ok)} Degree requirements")

    # Questionnaire
    rows     = fetch_all_preferences(uid)
    answered = {r["question"] for r in rows}
    st.markdown("**Questionnaire Responses:**")
    for q in QUESTIONS[1:]:   # skip QUESTIONS[0]
        st.write(f"{mark(q in answered)} {q}")

    st.markdown("---")

    # Determine where we came from
    prev = st.session_state.get("prev_page", "gemini")

    back_col, gen_col = st.columns([1,1], gap="small")
    with back_col:
        if st.button("⬅️ Back", key="gen_back"):
            # clear the "already submitted" flag so review shows Submit again
            # st.session_state.all_submitted = False
            # return to where we came from
            st.session_state.page = "resume" if prev == "resume" else "gemini"
            st.rerun()

    with gen_col:
        if st.button("🧙‍♂️ Generate my Schedule", key="gen_submit"):
            st.info("✨ Schedule generation coming soon!")