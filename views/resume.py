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
    st.session_state.setdefault("resume_dirty", {})   # idx → new answer
    st.session_state.setdefault("saved_q", set())     # indices user clicked Save
    st.session_state.setdefault("skipped_q", set())   # indices user clicked Skip
    st.session_state.setdefault("edit_mode", False)
    st.session_state.setdefault("upload_mode", False)
    st.session_state.setdefault("edited_tr", "")

# ─── transcript editor block ────────────────────────────────────────
def _transcript_block(uid: int):
    st.subheader("📄 Transcript")

    has_tr = transcript_exists(uid)
    current_txt = fetch_transcript(uid) or ""

    # reset edited_tr when not editing/uploading
    if not (st.session_state.edit_mode or st.session_state.upload_mode):
        st.session_state.edited_tr = current_txt

    # --- read-only view ---
    if not st.session_state.edit_mode and not st.session_state.upload_mode:
        if has_tr:
            st.text_area(
                "Current transcript (read-only):",
                current_txt,
                height=200,
                disabled=True,
            )
        else:
            st.info("No transcript uploaded yet.")

        col1, col2 = st.columns(2, gap="small")
        with col1:
            if has_tr and st.button("✏️ Edit current transcript", key="tr_edit"):
                st.session_state.edit_mode = True
        with col2:
            if st.button("📤 Upload new transcript", key="tr_upload"):
                st.session_state.upload_mode = True

    # --- edit existing transcript ---
    elif st.session_state.edit_mode:
        st.info("📋 Editing your current transcript:")
        st.session_state.edited_tr = st.text_area(
            "Edit transcript text:",
            value=st.session_state.edited_tr,
            height=200,
            key="tr_edit_area",
        )
        save_col, cancel_col = st.columns(2, gap="small")
        with save_col:
            if st.button("💾 Save changes", key="tr_save_edit"):
                upsert_transcript(uid, st.session_state.edited_tr)
                st.session_state.resume_dirty["transcript"] = True
                st.success("Transcript updated!")
                st.session_state.edit_mode = False
        with cancel_col:
            if st.button("❌ Cancel", key="tr_cancel_edit"):
                st.session_state.edit_mode = False

    # --- upload & replace transcript ---
    elif st.session_state.upload_mode:
        st.info("📤 Upload new transcript PDF:")
        uploaded = st.file_uploader("Select PDF", type="pdf", key="tr_upload_file")
        if uploaded:
            txt = process_pdf_with_gemini(extract_text_from_pdf(uploaded))
            if txt:
                st.session_state.edited_tr = txt
                st.success("✅ PDF processed; you can edit below.")
            else:
                st.error("⚠️ No text extracted; edit below manually.")

        st.session_state.edited_tr = st.text_area(
            "Transcript text:",
            value=st.session_state.edited_tr,
            height=200,
            key="tr_upload_area",
        )
        save_col, cancel_col = st.columns(2, gap="small")
        with save_col:
            if st.button("💾 Save new transcript", key="tr_save_upload"):
                upsert_transcript(uid, st.session_state.edited_tr)
                st.session_state.resume_dirty["transcript"] = True
                st.success("New transcript saved!")
                st.session_state.upload_mode = False
        with cancel_col:
            if st.button("❌ Cancel", key="tr_cancel_upload"):
                st.session_state.upload_mode = False

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
            # Write only those questions the user clicked Save on
            for question, ans in st.session_state.resume_dirty.items():
                save_preference(uid, question, ans)

            if st.session_state.resume_dirty:
                st.success("🎉 All your changes have been saved to the database!")
                # Clear the staging buffers
                st.session_state.resume_dirty.clear()
                st.session_state.saved_q.clear()
                st.session_state.skipped_q.clear()
            else:
                st.info("No changes to submit.")