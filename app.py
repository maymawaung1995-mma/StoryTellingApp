import streamlit as st
from openai import OpenAI

# ---------------- Page Config ----------------
st.set_page_config(page_title="The Enchanted Reader", layout="wide")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------- Dark Mode Toggle ----------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

mode_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀ Light Mode"
st.session_state.dark_mode = st.toggle(mode_label, value=st.session_state.dark_mode)

# ---------------- Dynamic CSS ----------------
if st.session_state.dark_mode:
    st.markdown("""
    <style>
    body { background-color: #1e1e1e; }
    .main { background-color: #1e1e1e; }

    .block-container {
        max-width: 650px;
        margin: auto;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #f5f5f5;
        font-family: Georgia, serif;
    }

    .story-box {
        background: #2b2b2b;
        padding: 35px;
        border-radius: 12px;
        font-size: 21px;
        line-height: 1.9;
        font-family: Georgia, serif;
        color: #f5f5f5;
    }

    .stButton>button {
        background-color: #555555;
        color: white;
        font-size: 18px;
        border-radius: 8px;
        padding: 14px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    body { background-color: #f6f1e7; }
    .main { background-color: #f6f1e7; }

    .block-container {
        max-width: 650px;
        margin: auto;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #2e2e2e;
        font-family: Georgia, serif;
    }

    .story-box {
        background: #ffffff;
        padding: 35px;
        border-radius: 12px;
        font-size: 21px;
        line-height: 1.9;
        font-family: Georgia, serif;
        color: #2e2e2e;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }

    .stButton>button {
        background-color: #444444;
        color: white;
        font-size: 18px;
        border-radius: 8px;
        padding: 14px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- Title ----------------
st.title("The Enchanted Reader")
st.markdown("A quiet place for magical stories.")
st.markdown("---")

# ---------------- Story Form ----------------
with st.form("story_form"):
    st.subheader("Story Settings")

    age_group = st.selectbox("Choose Age Group", ["4-6", "7-9"])
    theme = st.text_input("Story Theme (e.g., fairness, courage)")
    character = st.text_input("Main Character Name")

    submit = st.form_submit_button("Begin the Story")

# ---------------- Generate Story ----------------
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

    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
    )

    story = response.choices[0].message.content
    st.session_state.story = story

# ---------------- Display Story ----------------
if "story" in st.session_state:

    st.markdown(f"<div class='story-box'>{st.session_state.story}</div>", unsafe_allow_html=True)

    # -------- Image Generation --------
    image_prompt = f"Children's book illustration of {character} in a playground scene, soft detailed storybook style"
    image = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        size="1024x1024"
    )
    st.image(image.data[0].url, use_column_width=True)

    # -------- Voice Generation --------
    audio = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=st.session_state.story
    )
    st.markdown("Listen to narration:")
    st.audio(audio.content)

    st.markdown("### Continue the Story")

    # -------- Continuation Function --------
    def generate_continuation(choice_label):

        continuation_prompt = f"""
        Continue the following children's story in 150 words.
        Base the continuation on {choice_label}.
        Keep vocabulary simple.
        Story:
        {st.session_state.story}
        """

        continuation = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": continuation_prompt}]
        )

        cont_text = continuation.choices[0].message.content

        st.markdown(f"<div class='story-box'>{cont_text}</div>", unsafe_allow_html=True)

        # New Image for continuation
        cont_image_prompt = "Children's book illustration of the continuation scene, detailed storybook style"
        cont_image = client.images.generate(
            model="gpt-image-1",
            prompt=cont_image_prompt,
            size="1024x1024"
        )
        st.image(cont_image.data[0].url, use_column_width=True)

        # Voice for continuation
        cont_audio = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=cont_text
        )
        st.audio(cont_audio.content)

    if st.button("Continue with Choice 1"):
        generate_continuation("Choice 1")

    if st.button("Continue with Choice 2"):
        generate_continuation("Choice 2")
