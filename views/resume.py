# ─────────────────────────  views/resume.py  ─────────────────────────
import streamlit as st

from api_logic.gemini_api import process_pdf_with_gemini
from views.gemini         import extract_text_from_pdf, QUESTIONS, PROGRAM_OPTIONS, DEGREE_DIR
from database             import (
    transcript_exists,
    fetch_transcript,
    fetch_all_preferences,  # returns [{'question':..., 'answer':...}, ...]
    save_preference,        # (user_id, question_text, answer)
    save_degree_requirements,
    get_db_connection,      # new import so we can DELETE/INSERT transcripts
)

# ─── initialize session state keys ─────────────────────────────────
def _init_state():
    st.session_state.setdefault("resume_dirty", {})   # key → new value (str), special key "transcript"
    st.session_state.setdefault("saved_q", set())     # question_text keys the user clicked Save on
    st.session_state.setdefault("skipped_q", set())   # question_text keys the user clicked Skip on
    st.session_state.setdefault("edit_mode", False)   # transcript edit mode
    st.session_state.setdefault("upload_mode", False) # transcript upload mode
    st.session_state.setdefault("edited_tr", "")      # staged transcript text

# ─── transcript editor block ────────────────────────────────────
def _transcript_block(uid: int):
    s = st.session_state
    st.subheader("📄 Transcript")

    # Fetch from DB once
    db_txt = fetch_transcript(uid) or ""

    # On first render (not editing/uploading, and no staged change), seed edited_tr from DB
    if not (s.edit_mode or s.upload_mode) and "transcript" not in s.resume_dirty:
        s.edited_tr = db_txt

    has_content = bool(db_txt) or ("transcript" in s.resume_dirty)

    # ─── read-only view ───────────────────────────────────────────
    if not s.edit_mode and not s.upload_mode:
        if has_content:
            st.success("Transcript provided ✅")
            st.text_area(
                "Your transcript (read-only):",
                s.edited_tr,
                height=200,
                disabled=True,
            )
            if st.button("✏️ Change transcript", key="tr_change"):
                s.edit_mode = True
                st.rerun()
        else:
            st.info("No transcript uploaded yet.")
            if st.button("📤 Upload transcript", key="tr_start_upload"):
                s.upload_mode = True
                st.rerun()

    # ─── edit existing transcript ───────────────────────────────────
    elif s.edit_mode:
        st.info("📋 Edit your transcript below (or upload new PDF):")
        uploaded = st.file_uploader(
            "Replace with PDF (optional)", type="pdf", key="tr_replace_file"
        )
        if uploaded:
            txt = process_pdf_with_gemini(extract_text_from_pdf(uploaded))
            if txt:
                s.edited_tr = txt
                st.success("✅ PDF processed; you can edit further below.")
            else:
                st.error("⚠️ No text extracted; edit manually.")

        s.edited_tr = st.text_area(
            "Transcript text:",
            value=s.edited_tr,
            height=200,
            key="tr_edit_area",
        )

        disabled = not s.edited_tr.strip()
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("💾 Stage changes", key="tr_save_edit", disabled=disabled):
                if disabled:
                    st.warning("Transcript cannot be blank.")
                else:
                    s.resume_dirty["transcript"] = s.edited_tr
                    st.success("Transcript staged for saving!")
                    s.edit_mode = False
                    st.rerun()
        with c2:
            if st.button("❌ Cancel", key="tr_cancel_edit"):
                s.edit_mode = False
                st.rerun()

    # ─── first-time upload mode ─────────────────────────────────────
    elif s.upload_mode:
        st.info("📤 Upload your transcript PDF:")
        uploaded = st.file_uploader(
            "Select PDF", type="pdf", key="tr_upload_file"
        )
        if uploaded:
            txt = process_pdf_with_gemini(extract_text_from_pdf(uploaded))
            if txt:
                s.edited_tr = txt
                st.success("✅ PDF processed; you can edit below.")
            else:
                st.error("⚠️ No text extracted; edit manually.")

        s.edited_tr = st.text_area(
            "Transcript text:",
            value=s.edited_tr,
            height=200,
            key="tr_upload_area",
        )

        disabled_new = not s.edited_tr.strip()
        c1, c2 = st.columns(2, gap="small")
        with c1:
            if st.button("💾 Stage upload", key="tr_save_upload", disabled=disabled_new):
                if disabled_new:
                    st.warning("Transcript cannot be blank.")
                else:
                    s.resume_dirty["transcript"] = s.edited_tr
                    st.success("Transcript staged for saving!")
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
    try:
        rows = fetch_all_preferences(uid)
    except Exception:
        st.error("⚠️ Could not load your saved answers. Try again later.")
        return

    saved_map = {r["question"]: (r["answer"] or "") for r in rows}
    edits     = st.session_state.resume_dirty
    saved_q   = st.session_state.saved_q
    skipped_q = st.session_state.skipped_q

    for idx in range(1, len(QUESTIONS)):
        q = QUESTIONS[idx]
        st.markdown(f"**{q}**")

        if q in skipped_q:
            st.write("_(skipped)_")
            if st.button("↩️ Undo Skip", key=f"unskip_{idx}"):
                skipped_q.remove(q)
                st.rerun()
            st.markdown("---")
            continue

        if q in saved_q:
            st.write(edits.get(q, saved_map.get(q, "")))
            if st.button("✏️ Change", key=f"change_{idx}"):
                saved_q.remove(q)
                edits.pop(q, None)
                st.rerun()
            st.markdown("---")
            continue

        current = edits.get(q, saved_map.get(q, ""))
        if idx == 1:
            val = st.selectbox(
                "",
                PROGRAM_OPTIONS,
                index=(PROGRAM_OPTIONS.index(current)
                       if current in PROGRAM_OPTIONS else 0),
                key=f"input_{idx}",
            )
        else:
            val = st.text_input("", value=current, key=f"input_{idx}")

        col_s, col_k = st.columns([1,1], gap="small")
        with col_s:
            if st.button("💾 Save", key=f"save_{idx}"):
                if not val.strip():
                    st.warning("Cannot save a blank answer.")
                else:
                    edits[q] = val
                    saved_q.add(q)
                    st.success("Saved!")
                    st.rerun()
        with col_k:
            if st.button("⏭️ Skip", key=f"skip_{idx}"):
                if val.strip():
                    st.warning("Please clear the answer to skip.")
                else:
                    skipped_q.add(q)
                    edits.pop(q, None)
                    st.info("Marked as skipped.")
                    st.rerun()

        st.markdown("---")

# ─── page entrypoint -----------------------------------------------
def resume_page() -> None:
    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    # if continuing and no new edits, allow direct “Go to Generation”
    if (
        not st.session_state.get("resume_dirty")
        and (transcript_exists(uid) or fetch_all_preferences(uid))
    ):
        st.session_state["all_submitted"] = True

    st.session_state.setdefault("all_submitted", False)
    _init_state()
    st.header("🔧 Edit Your Saved Information")

    _transcript_block(uid)
    _question_block(uid)

    back_col, submit_col = st.columns([1,1], gap="small")
    with back_col:
        if st.button("⬅️ Back", key="resume_back"):
            st.session_state.page = "session_choice"
            st.rerun()

    with submit_col:
        if st.button("✅ Submit All Updates", key="resume_submit"):
            # 1) transcript: delete old + insert new
            if "transcript" in st.session_state.resume_dirty:
                new_txt = st.session_state.resume_dirty.pop("transcript")
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "DELETE FROM transcripts WHERE user_id = %s",
                        (uid,)
                    )
                    cur.execute(
                        "INSERT INTO transcripts (user_id, transcript) VALUES (%s, %s)",
                        (uid, new_txt)
                    )
                    conn.commit()

            # 2) program & degreqs
            prog_q = QUESTIONS[1]
            if prog_q in st.session_state.resume_dirty:
                new_prog = st.session_state.resume_dirty.pop(prog_q)
                save_preference(uid, prog_q, new_prog)
                fp = DEGREE_DIR / (
                    new_prog.replace(" ", "_").replace("/", "_") + ".txt"
                )
                if fp.exists():
                    save_degree_requirements(uid, new_prog, fp.read_text("utf-8"))

            # 3) all other prefs
            for question, ans in st.session_state.resume_dirty.items():
                save_preference(uid, question, ans)

            # clear staging
            st.session_state.resume_dirty.clear()
            st.session_state.saved_q.clear()
            st.session_state.skipped_q.clear()
            st.success("🎉 All your changes have been saved!")
            st.session_state.all_submitted = True

    if st.session_state.all_submitted:
        st.divider()
        if st.button("➡️ Go to Generation", key="goto_generation"):
            st.session_state.prev_page = "resume"
            st.session_state.page = "generation"
            st.rerun()
