# ──────────────────────────── views/session_choice.py ───────────────────────────
import streamlit as st
from database import transcript_exists, pref_count, delete_user_data, get_schedule

def session_choice_page() -> None:
    """
    Offer new users a single Start-from-scratch path,
    and returning users both Continue and scratch with confirmation.
    """
    uid = st.session_state.get("user_id")
    if not uid:
        st.error("⚠️ Please sign in again.")
        return

    # confirmation flag
    st.session_state.setdefault("confirm_scratch", False)

    has_transcript = transcript_exists(uid)
    has_prefs      = pref_count(uid) > 0
    has_progress   = has_transcript or has_prefs

    # ── Confirmation overlay ───────────────────────────────────────────
    if st.session_state.confirm_scratch:
        st.warning(
            "⚠️ All your saved data (transcript, preferences, degree requirements) "
            "will be permanently deleted. This cannot be undone."
        )
        col1, col2 = st.columns(2, gap="small")
        with col1:
            if st.button("Yes, start from scratch", key="confirm_yes"):
                delete_user_data(uid)
                # clear session state
                for k in ("answers", "saved", "skipped", "current_q", "all_submitted"):
                    st.session_state.pop(k, None)
                # reset flag & navigate
                st.session_state.confirm_scratch = False
                st.session_state.page = "transcript_intro"
                st.rerun()
        with col2:
            if st.button("Cancel", key="confirm_no"):
                st.session_state.confirm_scratch = False
                st.rerun()
        return  # hide the normal choices underneath

    # ── No confirmation yet ────────────────────────────────────────────
    if not has_progress:
        # Brand‐new user (no data)
        st.header("🚀 Ready to kick-start your semester adventure?")
        st.write(
            """
            🎓 We noticed you're new here, so let’s build from scratch!

            ✅ All steps are optional—you can skip the transcript upload ⏭️ and skip any question ⏭️, 
            but the more you share, the more personalized your planner will be!
            """
        )
        if st.button("🆕 Start from scratch", key="scratch_new"):
            # no DB to clear, go straight
            st.session_state.page = "transcript_intro"
            st.rerun()

    else:
        # Returning user (has data)
        st.header("👋 Welcome back!")
        st.write(
            """
            💾 We’ve saved your info from your last session.  
            Would you like to continue where you left off,  
            or start fresh and build a brand-new plan?
            """
        )
        col1, col2 = st.columns(2, gap="large")
        with col1:
            if st.button("🔄 Continue previous session", key="cont_prev"):
                st.session_state.page = "resume"
                st.rerun()
        with col2:
            if st.button("🌱 Start from scratch", key="scratch_ret"):
                # trigger the confirmation overlay above
                st.session_state.confirm_scratch = True
                st.rerun()

    st.divider()
    if st.button("⬅️ Back to Welcome", key="back_home"):
        st.session_state.page = "welcome"
        st.rerun()
    if get_schedule(uid) and st.button("🎉 View final schedule"):
        st.session_state.page = "final_view"
        st.rerun()   
