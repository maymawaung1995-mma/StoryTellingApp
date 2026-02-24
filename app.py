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

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ---------------- Dark Mode ----------------
mode_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀ Light Mode"
st.session_state.dark_mode = st.toggle(mode_label, value=st.session_state.dark_mode)

# ---------------- Theme Styling ----------------
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
body {{ background-color: {bg}; }}
.main {{ background-color: {bg}; }}

.block-container {{
    max-width: 700px;
    margin: auto;
}}

.story-box {{
    background: {card};
    padding: 35px;
    border-radius: 12px;
    font-size: 20px;
    line-height: 1.9;
    font-family: Georgia, serif;
    color: {text};
}}

.stButton>button {{
    font-size: 16px;
    padding: 12px;
    width: 100%;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- Predefined Structures ----------------

THEMES = [
    "Fairness",
    "Courage",
    "Kindness",
    "Friendship",
    "Responsibility",
    "Environmental Care"
]

TEMPLATES = {
    "Classic Moral Tale": """
1. Warm introduction
2. Clear moral conflict
3. Rising challenge
4. Two decision points (Choice 1 / Choice 2)
5. Positive resolution
6. Explicit moral takeaway
""",
    "Interactive Adventure": """
1. Exciting beginning
2. Unexpected challenge
3. Choice 1 (action-based)
4. Escalation
5. Choice 2 (problem-solving)
6. Satisfying ending
""",
    "Problem-Solving Story": """
1. Everyday situation
2. Problem appears
3. Choice 1 (collaboration)
4. Choice 2 (creative thinking)
5. Resolution
6. Reflection
"""
}

GENDERS = ["Girl", "Boy", "Non-binary", "Prefer not to specify"]

CULTURES = [
    "African",
    "Asian",
    "European",
    "Middle Eastern",
    "Latin American",
    "Indigenous",
    "Mixed",
    "Prefer not to specify"
]

PERSONALITIES = [
    "Brave",
    "Curious",
    "Kind",
    "Shy",
    "Clever",
    "Determined"
]

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":

    st.title("The Enchanted Reader")
    st.markdown("Structured Interactive Storytelling")

    with st.form("story_form"):

        age_group = st.selectbox("Choose Age Group", ["4-6", "7-9", "10-12"])
        theme = st.selectbox("Select Story Theme", THEMES)
        template_choice = st.selectbox("Select Narrative Template", list(TEMPLATES.keys()))

        character_name = st.text_input("Main Character Name")
        gender = st.selectbox("Character Gender", GENDERS)
        culture = st.selectbox("Cultural Background", CULTURES)
        personality = st.selectbox("Personality Trait", PERSONALITIES)

        temperature = st.slider("Creativity Level (Temperature)", 0.2, 1.0, 0.7, 0.1)

        submit = st.form_submit_button("Generate Story")

    if submit and character_name:

        system_prompt = """
You are an expert children's storyteller and developmental psychologist.
You produce age-appropriate, inclusive, culturally sensitive stories.
Maintain narrative coherence and moral clarity.
Avoid stereotypes.
Keep vocabulary aligned with specified age group.
"""

        user_prompt = f"""
Generate a 300-word interactive children's story using the structured inputs below.

Age Group: {age_group}
Theme: {theme}
Narrative Structure:
{TEMPLATES[template_choice]}

Main Character Name: {character_name}
Gender: {gender}
Cultural Background: {culture}
Personality Trait: {personality}

Requirements:
- Exactly 300 words
- Include clearly labeled: "Choice 1:" and "Choice 2:"
- Short sentences
- Age-appropriate vocabulary
- Clear moral resolution
"""

        with st.spinner("Creating your story..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            )

        st.session_state.story = response.choices[0].message.content
        st.session_state.page = "reading"
        st.rerun()

# ---------------- READING PAGE ----------------
elif st.session_state.page == "reading":

    st.title("Your Story")

    st.markdown(
        f"<div class='story-box'>{st.session_state.story}</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    # Continuation Logic
    choice = st.radio("Continue with:", ["Choice 1", "Choice 2"])

    if st.button("Continue Story"):

        continuation_prompt = f"""
Continue this children's story in 150 words based on {choice}.
Keep tone consistent.
Maintain age-appropriate language.
Ensure moral clarity.

Story:
{st.session_state.story}
"""

        with st.spinner("Continuing..."):
            continuation = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.7,
                messages=[{"role": "user", "content": continuation_prompt}]
            )

        st.session_state.story = continuation.choices[0].message.content
        st.rerun()

    st.markdown("---")

    # Text-to-Speech
    if st.button("🎧 Play Narration"):
        with st.spinner("Narrating..."):
            audio = client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=st.session_state.story
            )
        st.audio(audio.content)

    st.markdown("---")

    # PDF Export
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

    st.markdown("---")

    if st.button("Exit Story"):
        st.session_state.page = "home"
        st.session_state.story = None
        st.rerun()
