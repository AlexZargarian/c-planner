# views/gemini.py
import streamlit as st


def gemini_page():
    questions = [
        "1. Which faculty are you from?",
        "2. What year are you in (e.g., 2nd year)?",
        "3. Are there any specific courses you would like to take?",
        "4. Are there any instructors you want to avoid?",
        "5. Are there any classes you definitely do not want?",
        "6. At what times do you prefer to have classes (are evenings okay)?",
        "7. How many classes would you like to take this term?",
        "8. Do you prefer more classes on MWF or TTH?"
    ]
    n = len(questions)

    # 1) Init current question index
    if "current_q" not in st.session_state:
        st.session_state.current_q = 0

    # Initialize answers dictionary if it doesn't exist
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    curr = st.session_state.current_q

    # Always show questions (no summary screen)
    # Ensure curr is within valid range
    curr = min(curr, n - 1)

    key = f"answer_{curr}"

    # Initialize answer slot if missing
    if key not in st.session_state:
        # Try to get from saved answers
        st.session_state[key] = st.session_state.answers.get(curr, "")

    # Show the question with the existing answer pre-populated
    user_input = st.text_input(questions[curr], key=key)

    # Save the answer to our persistent answers dictionary
    st.session_state.answers[curr] = user_input

    # Navigation buttons
    back, nxt = st.columns([1, 1])

    if curr > 0 and back.button("Back", key=f"back_{curr}"):
        # Save current answer before going back
        st.session_state.answers[curr] = st.session_state[key]
        st.session_state.current_q = curr - 1

    # Only show Submit button if not on last question
    if curr < n - 1:
        if nxt.button("Submit", key=f"next_{curr}"):
            # Save current answer before going forward
            st.session_state.answers[curr] = st.session_state[key]
            st.session_state.current_q = curr + 1
    else:
        # On the last question, show Finish button but it doesn't do anything
        nxt.button("Finish", key=f"next_{curr}", disabled=False)

    # Always show Log Out button
    if st.button("Log Out"):
        # Clear answers when logging out
        if "answers" in st.session_state:
            del st.session_state.answers
        st.session_state.page = "login"