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

if "history" not in st.session_state:
    st.session_state.history = []

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ---------------- Dark Mode Toggle ----------------
mode_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀ Light Mode"
st.session_state.dark_mode = st.toggle(mode_label, value=st.session_state.dark_mode)

# ---------------- Dynamic CSS ----------------
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
    max-width: 650px;
    margin: auto;
    padding-top: 2rem;
    padding-bottom: 3rem;
}}

h1, h2, h3 {{
    color: {text};
    font-family: Georgia, serif;
}}

.story-box {{
    background: {card};
    padding: 35px;
    border-radius: 12px;
    font-size: 21px;
    line-height: 1.9;
    font-family: Georgia, serif;
    color: {text};
}}

.stButton>button {{
    background-color: #444444;
    color: white;
    font-size: 18px;
    border-radius: 8px;
    padding: 14px;
    width: 100%;
}}
</style>
""", unsafe_allow_html=True)

# ---------------- HOME PAGE ----------------
if st.session_state.page == "home":

    st.title("The Enchanted Reader")
    st.markdown("A quiet place for magical stories.")
    st.markdown("---")

    with st.form("story_form"):
        age_group = st.selectbox("Choose Age Group", ["4-6", "7-9"])
        theme = st.text_input("Story Theme (e.g., fairness, courage)")
        character = st.text_input("Main Character Name")

        submit = st.form_submit_button("Begin the Story")

    if submit and theme and character:

        prompt = f"""
        Write exactly 300 words.
        Write an interactive story for children aged {age_group} about {theme}.
        The main character is {character}.
        In the story, {character} notices that some children are not allowed to join a playground game.
        Include two clearly labeled sections: "Choice 1:" and "Choice 2:".
        Use simple vocabulary suitable for early primary school children.
        Keep sentences short and easy to understand.
        Do not exceed 300 words.
        """

        with st.spinner("Opening the storybook..."):
            response = client.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": prompt}],
            )

        story = response.choices[0].message.content
        st.session_state.story = story
        st.session_state.history.append(story)
        st.session_state.page = "reading"
        st.rerun()

# ---------------- READING PAGE ----------------
elif st.session_state.page == "reading":

    st.title("Your Story")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Story", "Illustration", "Narration", "Continue", "History", "Exit"]
    )

    # -------- STORY TAB --------
    with tab1:
        word_count = len(st.session_state.story.split())
        progress = min(word_count / 300, 1.0)
        st.progress(progress)
        st.caption(f"{word_count} / 300 words")

        st.markdown(
            f"<div class='story-box'>{st.session_state.story}</div>",
            unsafe_allow_html=True
        )

        # PDF Download
        if st.button("Download as PDF"):
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

    # -------- IMAGE TAB --------
    with tab2:
        if st.button("Generate Illustration"):
            with st.spinner("Illustrating the scene..."):
                image = client.images.generate(
                    model="gpt-image-1",
                    prompt="Children's book illustration of this story scene, storybook style",
                    size="1024x1024"
                )
            st.image(image.data[0].url, use_column_width=True)

    # -------- AUDIO TAB --------
    with tab3:
        if st.button("Play Narration"):
            with st.spinner("Narrating..."):
                audio = client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice="alloy",
                    input=st.session_state.story
                )
            st.audio(audio.content)

    # -------- CONTINUE TAB --------
    with tab4:
        st.subheader("Choose how the story continues")

        if st.button("Continue with Choice 1"):
            with st.spinner("Turning the page..."):
                continuation = client.chat.completions.create(
                    model="gpt-5.2",
                    messages=[{
                        "role": "user",
                        "content": f"Continue the following story in 150 words based on Choice 1:\n{st.session_state.story}"
                    }]
                )
            cont_text = continuation.choices[0].message.content
            st.markdown(
                f"<div class='story-box'>{cont_text}</div>",
                unsafe_allow_html=True
            )

        if st.button("Continue with Choice 2"):
            with st.spinner("Turning the page..."):
                continuation = client.chat.completions.create(
                    model="gpt-5.2",
                    messages=[{
                        "role": "user",
                        "content": f"Continue the following story in 150 words based on Choice 2:\n{st.session_state.story}"
                    }]
                )
            cont_text = continuation.choices[0].message.content
            st.markdown(
                f"<div class='story-box'>{cont_text}</div>",
                unsafe_allow_html=True
            )

    # -------- HISTORY TAB --------
    with tab5:
        st.subheader("Story History")
        if st.session_state.history:
            for i, past_story in enumerate(st.session_state.history[::-1]):
                st.markdown(f"### Story {len(st.session_state.history)-i}")
                st.markdown(
                    f"<div class='story-box'>{past_story}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.write("No previous stories yet.")

    # -------- EXIT TAB --------
    with tab6:
        st.warning("Return to story settings?")
        if st.button("Exit Story"):
            st.session_state.page = "home"
            st.session_state.story = None
            st.rerun()
