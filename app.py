import streamlit as st
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key="OPENAI_API_KEY")

st.title("Interactive AI Story Builder")

st.sidebar.header("Story Settings")

age_group = st.sidebar.selectbox(
    "Select Age Group",
    ["4-6", "7-9"]
)

theme = st.sidebar.text_input("Theme (e.g., fairness, courage)")
character = st.sidebar.text_input("Main Character Name")

def generate_prompt(age, theme, character):
    return f"""
Write exactly 300 words.
Write an interactive story for children aged {age} about {theme}.
The main character is {character}.
In the story, {character} notices that some children are not allowed to join a playground game.
Include two clearly labeled sections: "Choice 1:" and "Choice 2:".
Use simple vocabulary suitable for early primary school children.
Keep sentences short and easy to understand.
Do not exceed 300 words.
"""

if st.button("Generate Story"):
    if theme and character:
        prompt = generate_prompt(age_group, theme, character)

        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        story = response.choices[0].message.content
        st.subheader("Generated Story")
        st.write(story)

    else:

        st.warning("Please enter both theme and character name.")
        st.write(st.secrets)

