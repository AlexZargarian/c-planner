# ───────────────────  views/review_skipped.py  ────────────────────
import streamlit as st

def review_skipped_page() -> None:
    """Show skipped questions and let the user jump back in."""
    skipped = st.session_state.get("skipped", [])
    unanswered = [q for i, q in skipped]

    st.write("## You skipped a few questions")
    if unanswered:
        st.markdown(
            "To tailor your semester plan, it helps to answer everything. "
            "Here’s what you skipped:"
        )
        for q in unanswered:
            st.write("•", q)

        if st.button("Answer Remaining Questions"):
            # jump to the *first* skipped question
            first_idx = skipped[0][0]
            st.session_state.current_q = first_idx
            st.session_state.page = "gemini"
            st.session_state.rerun = True
    else:
        st.success("Great! You answered everything 🎉")
        if st.button("Generate my schedule"):
            # TODO: route to the schedule-generation view when ready
            st.info("Scheduler coming soon…")
