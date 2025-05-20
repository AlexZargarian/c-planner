# ─────────────────────────  views/resume.py  ─────────────────────────
import streamlit as st

from api_logic.gemini_api import process_pdf_with_gemini
from views.gemini         import extract_text_from_pdf, QUESTIONS, PROGRAM_OPTIONS
from database             import (
    transcript_exists,
    fetch_transcript,
    upsert_transcript,
    fetch_all_preferences,  # returns [{'question':..., 'answer':...}, ...]
    save_preference,        # (user_id, question_text, answer)
)

# ─── initialize session state keys ─────────────────────────────────
def _init_state():
    st.session_state.setdefault("resume_dirty", {})   # question_text → new answer
    st.session_state.setdefault("saved_q", set())     # set of question_text saved
    st.session_state.setdefault("skipped_q", set())   # set of question_text skipped
    st.session_state.setdefault("edit_mode", False)
    st.session_state.setdefault("upload_mode", False)
    st.session_state.setdefault("edited_tr", "")

# ─── transcript editor block ────────────────────────────────────
def _transcript_block(uid: int):
    """Transcript editor: view, edit text, or upload new PDF in edit mode."""
    s = st.session_state
    st.subheader("📄 Transcript")

    # Initialize flags
    s.setdefault("resume_dirty", {})     # track that transcript was saved
    s.setdefault("edit_mode", False)
    s.setdefault("upload_mode", False)

    # Fetch from DB once
    db_txt = fetch_transcript(uid) or ""

    # On fresh entry into read-only, sync in-memory to DB value unless we’ve saved
    if not (s.edit_mode or s.upload_mode) and not s.resume_dirty.get("transcript"):
        s.edited_tr = db_txt

    # Determine whether we have “some transcript” (DB or staged)
    has_any = bool(db_txt) or s.resume_dirty.get("transcript", False)

    # ─── READ-ONLY WITH “Change” ────────────────────────────────────
    if not s.edit_mode and not s.upload_mode:
        if has_any:
            st.success("Transcript saved ✅")
            st.text_area(
                "Your classes (read-only):",
                s.edited_tr,
                height=200,
                disabled=True,
            )
            if st.button("✏️ Change current transcript", key="tr_change"):
                s.edit_mode = True
                st.rerun()
        else:
            st.info("No transcript uploaded yet.")
            if st.button("📤 Upload new transcript", key="tr_start_upload"):
                s.upload_mode = True
                st.rerun()

    # ─── EDIT MODE: text + optional PDF upload ──────────────────────
    elif s.edit_mode:
        st.info("📋 Edit your transcript below (or upload a new PDF):")

        # allow PDF upload here too
        uploaded = st.file_uploader("Replace with PDF (optional)", type="pdf", key="tr_replace_file")
        if uploaded:
            txt = process_pdf_with_gemini(extract_text_from_pdf(uploaded))
            if txt:
                s.edited_tr = txt
                st.success("✅ PDF processed; edit below if needed.")
            else:
                st.error("⚠️ No text extracted; edit manually.")

        # editable textarea
        s.edited_tr = st.text_area(
            "Transcript text:",
            value=s.edited_tr,
            height=200,
            key="tr_edit_area",
        )

        # Save / Cancel row
        disabled = not s.edited_tr.strip()
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("💾 Save changes", key="tr_save_edit", disabled=disabled):
                if disabled:
                    st.warning("Transcript cannot be blank.")
                else:
                    upsert_transcript(uid, s.edited_tr)
                    s.resume_dirty["transcript"] = True
                    st.success("Transcript updated!")
                    s.edit_mode = False
                    st.rerun()
        with c2:
            if st.button("❌ Cancel", key="tr_cancel_edit"):
                s.edit_mode = False
                st.rerun()

    # ─── UPLOAD MODE: first-time or “Start Upload” ─────────────────
    elif s.upload_mode:
        st.info("📤 Upload your transcript PDF:")
        uploaded = st.file_uploader("Select PDF", type="pdf", key="tr_upload_file")
        if uploaded:
            txt = process_pdf_with_gemini(extract_text_from_pdf(uploaded))
            if txt:
                s.edited_tr = txt
                st.success("✅ PDF processed; you can edit below.")
            else:
                st.error("⚠️ No text extracted; edit below manually.")

        # editable textarea after processing
        s.edited_tr = st.text_area(
            "Transcript text:",
            value=s.edited_tr,
            height=200,
            key="tr_upload_area",
        )

        # Save / Cancel row
        disabled_new = not s.edited_tr.strip()
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("💾 Save new transcript", key="tr_save_upload", disabled=disabled_new):
                if disabled_new:
                    st.warning("Transcript cannot be blank.")
                else:
                    upsert_transcript(uid, s.edited_tr)
                    s.resume_dirty["transcript"] = True
                    st.success("New transcript saved!")
                    s.upload_mode = False
                    st.rerun()
        with c2:
            if st.button("❌ Cancel", key="tr_cancel_upload"):
                s.upload_mode = False
                st.rerun()

    st.divider()



# ─── questionnaire editor block ────────────────────────────────────
def _question_block(uid: int):
    st.subheader("📝 Questionnaire answers")

    # Fetch saved preferences: list of {'question': ..., 'answer': ...}
    try:
        rows = fetch_all_preferences(uid)
    except Exception:
        st.error("⚠️ Could not load your saved answers. Try again later.")
        return

    # Map question_text → existing answer
    saved_map = {r["question"]: (r["answer"] or "") for r in rows}
    edits     = st.session_state.resume_dirty
    saved_q   = st.session_state.saved_q
    skipped_q = st.session_state.skipped_q

    # Loop through QUESTIONS by index, but key state by question text
    for idx in range(1, len(QUESTIONS)):
        q_text = QUESTIONS[idx]
        st.markdown(f"**{q_text}**")

        # --- already skipped ---
        if q_text in skipped_q:
            st.write("_(skipped)_")
            if st.button("↩️ Undo Skip", key=f"unskip_{idx}"):
                skipped_q.remove(q_text)
                st.rerun()
            st.markdown("---")
            continue

        # --- already saved ---
        if q_text in saved_q:
            answer = edits.get(q_text, saved_map.get(q_text, ""))
            st.write(answer)
            if st.button("✏️ Change", key=f"change_{idx}"):
                saved_q.remove(q_text)
                edits.pop(q_text, None)
                st.rerun()
            st.markdown("---")
            continue

        # --- input + Save / Skip ---
        # Pre-fill from edits buffer or DB
        current = edits.get(q_text, saved_map.get(q_text, ""))

        if idx == 1:
            val = st.selectbox(
                "", PROGRAM_OPTIONS,
                index=PROGRAM_OPTIONS.index(current) if current in PROGRAM_OPTIONS else 0,
                key=f"input_{idx}"
            )
        else:
            val = st.text_input(
                "", value=current, key=f"input_{idx}"
            )

        col_s, col_k = st.columns([1,1], gap="small")
        with col_s:
            if st.button("💾 Save", key=f"save_{idx}"):
                if not val.strip():
                    st.warning("Cannot save a blank answer.")
                else:
                    edits[q_text] = val
                    saved_q.add(q_text)
                    st.success("Saved!")
                    st.rerun()
        with col_k:
            if st.button("⏭️ Skip", key=f"skip_{idx}"):
                if val.strip():
                    st.warning("Please clear the answer to skip.")
                else:
                    skipped_q.add(q_text)
                    edits.pop(q_text, None)
                    st.info("Marked as skipped.")
                    st.rerun()

        st.markdown("---")

# ─── page entrypoint -----------------------------------------------
def resume_page() -> None:
    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return
    
    # If user just continued from a prior session (they have saved data),
    # immediately enable the "Go to Generation" button.
    # We only set this if resume_dirty is empty (i.e. no new edits staged).
    if not st.session_state.get("resume_dirty") and (
        transcript_exists(uid) or fetch_all_preferences(uid)
    ):
        st.session_state["all_submitted"] = True

    # make sure our "all_submitted" flag exists
    st.session_state.setdefault("all_submitted", False)

    _init_state()
    st.header("🔧 Edit Your Saved Information")

    _transcript_block(uid)
    _question_block(uid)

    # bottom-row: Back | Submit All Updates
    back_col, submit_col = st.columns([1,1], gap="small")
    with back_col:
        if st.button("⬅️ Back", key="resume_back"):
            st.session_state.page = "session_choice"
            st.rerun()

    with submit_col:
        if st.button("✅ Submit All Updates", key="resume_submit"):
            # Persist only the answers the user explicitly saved
            for question, ans in st.session_state.resume_dirty.items():
                save_preference(uid, question, ans)

            if st.session_state.resume_dirty:
                st.success("🎉 All your changes have been saved to the database!")
                # Clear the staging buffers
                st.session_state.resume_dirty.clear()
                st.session_state.saved_q.clear()
                st.session_state.skipped_q.clear()
                # mark completion so we can show the Generation button
                st.session_state.all_submitted = True
            else:
                st.info("No changes to submit.")

    # show the Generation button after successful submit
    if st.session_state.all_submitted:
        st.divider()
        if st.button("➡️ Go to Generation", key="goto_generation"):
            st.session_state.prev_page = "resume"
            st.session_state.page = "generation"
            st.rerun()
