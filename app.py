import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from gtts import gTTS
import base64
import io

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize LangChain LLM
llm = ChatOpenAI(temperature=0.7, openai_api_key=openai_api_key, model_name="gpt-3.5-turbo")

# Page configuration
st.set_page_config(page_title="English Reading Adventure", page_icon="📚")
st.title("📚 English Reading Adventure for 7th Graders")

# Initialize session state for points and progress
if "points" not in st.session_state:
    st.session_state.points = 0
if "passages_completed" not in st.session_state:
    st.session_state.passages_completed = 0
if "vocab_learned" not in st.session_state:
    st.session_state.vocab_learned = []

# Sidebar for progress tracking
with st.sidebar:
    st.header("Your Progress")
    st.write(f"Points: {st.session_state.points}")
    st.write(f"Passages Completed: {st.session_state.passages_completed}")
    st.write(f"Vocabulary Learned: {len(st.session_state.vocab_learned)} words")
    if st.session_state.vocab_learned:
        st.write("Words Learned:")
        for word in st.session_state.vocab_learned:
            st.write(f"- {word}")

# Prompt templates for LangChain
passage_prompt = PromptTemplate(
    input_variables=["grade_level"],
    template="Generate a short, engaging reading passage (100-150 words) suitable for a {grade_level} grader. The passage should be fun, use simple vocabulary, and include 3-5 new words a 7th grader might not know. Provide a list of the new words with their definitions."
)
question_prompt = PromptTemplate(
    input_variables=["passage"],
    template="Generate 3 comprehension questions based on the following passage:\n{passage}"
)
quiz_prompt = PromptTemplate(
    input_variables=["passage"],
    template="Generate a vocabulary quiz with 3 multiple-choice questions based on the new words in the following passage:\n{passage}"
)

# Function to generate passage and vocabulary
def generate_passage():
    response = llm.invoke(passage_prompt.format(grade_level="5th")).content
    print(response)
    passage, vocab = response.split("**Vocabulary:**")
    passage = passage.strip()
    vocab = vocab.strip().split("\n")
    vocab_dict = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in vocab if ":" in line}
    return passage, vocab_dict

# Function to generate comprehension questions
def generate_questions(passage):
    response = llm.invoke(question_prompt.format(passage=passage)).content
    questions = response.split("\n")
    return [q for q in questions if q.strip()]

# Function to generate vocabulary quiz
def generate_quiz(passage):
    response = llm.invoke(quiz_prompt.format(passage=passage)).content
    questions = response.split("\n")
    return [q for q in questions if q.strip()]

# Function for text-to-speech
def text_to_speech(text):
    tts = gTTS(text=text, lang="en")
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    audio_b64 = base64.b64encode(audio_file.read()).decode()
    audio_html = f'<audio autoplay controls><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>'
    return audio_html

# Main app logic
st.header("Start Your Reading Adventure!")
if st.button("Get a New Reading Passage"):
    passage, vocab_dict = generate_passage()
    st.session_state.passage = passage
    st.session_state.vocab_dict = vocab_dict
    st.session_state.questions = generate_questions(passage)
    st.session_state.quiz = generate_quiz(passage)
    st.session_state.passages_completed += 1
    st.session_state.points += 10  # Award points for starting a passage

# Display passage if available
if "passage" in st.session_state:
    st.subheader("Reading Passage")
    st.write(st.session_state.passage)
    st.markdown(text_to_speech(st.session_state.passage), unsafe_allow_html=True)

    # Vocabulary section
    st.subheader("New Words")
    for word, definition in st.session_state.vocab_dict.items():
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(f"Listen: {word}"):
                st.markdown(text_to_speech(word), unsafe_allow_html=True)
        with col2:
            st.write(f"**{word}**: {definition}")
            if word not in st.session_state.vocab_learned:
                st.session_state.vocab_learned.append(word)
                st.session_state.points += 5  # Award points for learning a word

    # Comprehension questions
    st.subheader("Comprehension Questions")
    with st.form("comprehension_form"):
        answers = []
        for i, question in enumerate(st.session_state.questions[:3], 1):
            answer = st.text_input(f"Q{i}: {question}", key=f"q{i}")
            answers.append(answer)
        submitted = st.form_submit_button("Submit Answers")
        if submitted:
            st.session_state.points += 20  # Award points for submitting answers
            st.success("Great job! You earned 20 points for answering the questions!")

    # Vocabulary quiz
    st.subheader("Vocabulary Quiz")
    with st.form("quiz_form"):
        quiz_answers = []
        for i, question in enumerate(st.session_state.quiz[:3], 1):
            options = ["Option A", "Option B", "Option C", "Option D"]  # Simplified for demo
            answer = st.radio(f"Q{i}: {question}", options, key=f"quiz_q{i}")
            quiz_answers.append(answer)
        quiz_submitted = st.form_submit_button("Submit Quiz")
        if quiz_submitted:
            st.session_state.points += 15  # Award points for completing quiz
            st.success("Awesome! You earned 15 points for completing the quiz!")

# Rewards section
st.header("Your Rewards")
if st.session_state.points >= 50:
    st.balloons()
    st.write("🎉 Congratulations! You've unlocked a new badge!")
if st.session_state.points >= 100:
    st.write("🏆 Super Reader! You've earned the Master Reader title!")