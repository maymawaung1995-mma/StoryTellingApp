import streamlit as st
from openai import OpenAI
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ---------------- Page Config ----------------
st.set_page_config(page_title="The Enchanted Reader", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

MAX_TURNS = 3

# ---------------- Session State ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "pages" not in st.session_state:
    st.session_state.pages = []

if "page_index" not in st.session_state:
    st.session_state.page_index = 0

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# ---------------- Reset Function ----------------
def reset_story():
    st.session_state.page = "home"
    st.session_state.pages = []
    st.session_state.page_index = 0
    st.session_state.turn_count = 0


# ---------------- System Role (V3) ----------------
system_role = """
You are a children's educational storyteller.
Follow structured narrative logic.
Maintain moral clarity.
Use age-appropriate vocabulary.
Do not repeat earlier content.
Ensure branching consistency.
"""

# ---------------- Dark Mode ----------------
mode_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀ Light Mode"
st.session_state.dark_mode = st.toggle(mode_label, value=st.session_state.dark_mode)

if st.session_state.dark_mode:
    bg = "#1e1e1e"
    text = "#f5f5f5"
    card = "#2b2b2b"
else:
    bg = "#f6f1e7"
    text = "#2e2e2e"
    card = "#ffffff"

st.markdown(f"""
<style>
.block-container {{
    max-width: 700px;
    margin: auto;
}}

.story-box {{
    background: {card};
    padding: 35px;
    border-radius: 12px;
    font-size: 20px;
    line-height: 1.8;
    font-family: Georgia, serif;
    color: {text};
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":

    st.title("The Enchanted Reader")
    st.markdown("Structured Interactive Storytelling")

    with st.form("story_form"):

        age_group = st.selectbox("Age Group", ["4-6", "7-9", "10-12"])
        theme = st.selectbox("Theme", ["Fairness", "Kindness", "Courage"])
        character_name = st.text_input("Main Character Name")
        temperature = st.slider("Creativity Level", 0.2, 1.0, 0.7, 0.1)

        submit = st.form_submit_button("Generate Story")

    if submit and character_name:

        user_prompt = f"""
Write exactly 300 words.

Create an interactive story for children aged {age_group}.
Theme: {theme}
Main character: {character_name}

Structure:
- Opening paragraph
- Clear moral problem
- Rising tension
- Clearly labeled Choice 1:
- Clearly labeled Choice 2:

Use short sentences.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": user_prompt}
            ],
        )

        st.session_state.pages = [response.choices[0].message.content]
        st.session_state.page_index = 0
        st.session_state.turn_count = 1
        st.session_state.page = "reading"
        st.rerun()

# ---------------- READING PAGE ----------------
elif st.session_state.page == "reading":

    # Exit Button at Top
    col_exit, col_title = st.columns([1, 4])
    with col_exit:
        if st.button("🏠 Exit to Main Menu"):
            reset_story()
            st.rerun()

    with col_title:
        st.title("Your Story")

    current_text = st.session_state.pages[st.session_state.page_index]

    st.markdown(
        f"<div class='story-box'>{current_text}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ---------------- Back Button ----------------
    if st.session_state.page_index > 0:
        if st.button("⬅ Back"):
            st.session_state.page_index -= 1
            st.rerun()

    # ---------------- Continue Logic ----------------
    if st.session_state.turn_count < MAX_TURNS:

        col1, col2 = st.columns(2)

        with col1:
            choice1_clicked = st.button("Continue with Choice 1")

        with col2:
            choice2_clicked = st.button("Continue with Choice 2")

        if choice1_clicked or choice2_clicked:

            selected_choice = "Choice 1" if choice1_clicked else "Choice 2"

            st.session_state.pages = st.session_state.pages[:st.session_state.page_index + 1]

            is_final_turn = (st.session_state.turn_count + 1 == MAX_TURNS)

            if not is_final_turn:
                continuation_prompt = f"""
Continue ONLY from {selected_choice}.
Do NOT restart the story.
Write about 150 words.

Include new:
Choice 1:
Choice 2:

Previous page:
{current_text}
"""
            else:
                continuation_prompt = f"""
Continue ONLY from {selected_choice}.
Do NOT restart the story.
Write about 150 words.

Conclude clearly.
Do NOT include new choices.
End with a positive moral.

Previous page:
{current_text}
"""

            continuation = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": continuation_prompt}
                ],
            )

            st.session_state.pages.append(
                continuation.choices[0].message.content
            )

            st.session_state.page_index = len(st.session_state.pages) - 1
            st.session_state.turn_count += 1
            st.rerun()

    # ---------------- Ending ----------------
    if st.session_state.turn_count >= MAX_TURNS and \
       st.session_state.page_index == len(st.session_state.pages) - 1:

        st.markdown("### 🌟 The End")

    st.markdown("---")

    # ---------------- TTS ----------------
    if st.button("🎧 Play Narration"):
        full_story = "\n\n".join(st.session_state.pages)
        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=full_story
        )
        st.audio(audio.content)

    # ---------------- PDF Export ----------------
    if st.button("Download Story as PDF"):

        full_story = "\n\n".join(st.session_state.pages)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        style = styles["Normal"]

        elements.append(
            Paragraph(full_story.replace("\n", "<br/>"), style)
        )
        elements.append(Spacer(1, 12))
        doc.build(elements)
        buffer.seek(0)

        st.download_button(
            label="Download PDF",
            data=buffer,
            file_name="story.pdf",
            mime="application/pdf"
        )
