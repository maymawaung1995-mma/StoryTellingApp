import streamlit as st
from openai import OpenAI
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ---------------- Page Config ----------------
st.set_page_config(page_title="The Enchanted Reader", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------- Session State ----------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "story" not in st.session_state:
    st.session_state.story = None

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

MAX_TURNS = 3

system_role = """
You are a children's educational storyteller.
Follow strict narrative structure.
Ensure moral clarity.
Keep language age-appropriate.
Avoid repeating choices.
Maintain coherence across continuations.
"""

# ---------------- Dark Mode ----------------
mode_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀ Light Mode"
st.session_state.dark_mode = st.toggle(mode_label, value=st.session_state.dark_mode)

# ---------------- Styling ----------------
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

# ---------------- Home Page ----------------
if st.session_state.page == "home":

    st.title("The Enchanted Reader")
    st.markdown("Structured Interactive Storytelling")

    with st.form("story_form"):

        age_group = st.selectbox("Choose Age Group", ["4-6", "7-9", "10-12"])
        theme = st.selectbox("Theme", ["Fairness", "Kindness", "Courage"])
        character_name = st.text_input("Main Character Name")
        temperature = st.slider("Creativity Level", 0.2, 1.0, 0.7, 0.1)

        submit = st.form_submit_button("Generate Story")

    if submit and character_name:

        st.session_state.turn_count = 1


        # ----------- V3 USER PROMPT -----------
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
Ensure educational value.
"""

        with st.spinner("Creating your story..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": user_prompt}
                ],
            )

        st.session_state.story = response.choices[0].message.content
        st.session_state.page = "reading"
        st.rerun()

# ---------------- Reading Page ----------------
elif st.session_state.page == "reading":

    st.title("Your Story")

    st.markdown(
        f"<div class='story-box'>{st.session_state.story}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ----------- Continuation Logic -----------
    if st.session_state.turn_count < MAX_TURNS:

        col1, col2 = st.columns(2)

        with col1:
            choice1_clicked = st.button("Continue with Choice 1")

        with col2:
            choice2_clicked = st.button("Continue with Choice 2")

        if choice1_clicked or choice2_clicked:

            selected_choice = "Choice 1" if choice1_clicked else "Choice 2"
            is_final_turn = (st.session_state.turn_count + 1 == MAX_TURNS)

            if not is_final_turn:
                continuation_prompt = f"""
Continue the story following the events described in {selected_choice}.

Develop consequences of that decision.
Include clearly labeled:
Choice 1:
Choice 2:

Maintain age-appropriate language.
"""
            else:
                continuation_prompt = f"""
Continue the story following the events described in {selected_choice}.

Conclude clearly.
Do NOT include new choices.
End with a positive moral resolution.
"""

            with st.spinner("Continuing story..."):
                continuation = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": system_role},
                        {"role": "user", "content": continuation_prompt + "\n\n" + st.session_state.story}
                    ]
                )

            st.session_state.story = continuation.choices[0].message.content
            st.session_state.turn_count += 1
            st.rerun()

    else:
        st.markdown("### 🌟 The End")
        if st.button("Start New Story"):
            st.session_state.page = "home"
            st.session_state.story = None
            st.session_state.turn_count = 0
            st.rerun()

    st.markdown("---")

    # ----------- Text to Speech -----------
    if st.button("🎧 Play Narration"):
        audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=st.session_state.story
        )
        st.audio(audio.content)

    # ----------- PDF Export -----------
    if st.button("Download Story as PDF"):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        style = styles["Normal"]

        elements.append(Paragraph(st.session_state.story.replace("\n", "<br/>"), style))
        elements.append(Spacer(1, 12))
        doc.build(elements)
        buffer.seek(0)

        st.download_button(
            label="Download PDF",
            data=buffer,
            file_name="story.pdf",
            mime="application/pdf"
        )

