import streamlit as st
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List, Dict
from gtts import gTTS
import base64
import io
import json

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Pydantic models for structured output
class VocabularyWord(BaseModel):
    word: str = Field(description="The vocabulary word")
    definition: str = Field(description="Simple definition suitable for 5th graders")

class ReadingPassage(BaseModel):
    passage: str = Field(description="The reading passage content (100 words)")
    vocabulary: List[VocabularyWord] = Field(description="List of 3-5 new vocabulary words with definitions")

class ComprehensionQuestions(BaseModel):
    questions: List[str] = Field(description="List of 3 comprehension questions about the passage")

class QuizOption(BaseModel):
    option: str = Field(description="Multiple choice option")
    is_correct: bool = Field(description="Whether this option is correct")

class VocabularyQuizQuestion(BaseModel):
    question: str = Field(description="The quiz question")
    options: List[QuizOption] = Field(description="4 multiple choice options")

class VocabularyQuiz(BaseModel):
    questions: List[VocabularyQuizQuestion] = Field(description="List of 3 vocabulary quiz questions")

# Initialize LangChain LLM
llm = ChatOpenAI(model="gpt-4o-mini",temperature=0.7, openai_api_key=openai_api_key)

# Create structured output models
passage_model = llm.with_structured_output(ReadingPassage)
questions_model = llm.with_structured_output(ComprehensionQuestions)
quiz_model = llm.with_structured_output(VocabularyQuiz)

# Page configuration
st.set_page_config(page_title="English Reading Adventure", page_icon="📚")
st.title("📚 English Reading Adventure for 8th Graders")

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

# Simplified prompt templates for structured output
passage_prompt = PromptTemplate(
    input_variables=["grade_level"],
    template="""Generate a short, engaging reading passage suitable for a {grade_level} grader. 
    The passage should be fun, use simple vocabulary, and include 3-5 new words a 5th grader might not know.
    Return the passage and vocabulary words with their definitions."""
)

question_prompt = PromptTemplate(
    input_variables=["passage"],
    template="""Generate 3 comprehension questions based on the following passage:
    {passage}
    
    Return exactly 3 questions that test understanding of the passage."""
)

quiz_prompt = PromptTemplate(
    input_variables=["passage", "vocabulary"],
    template="""Generate a vocabulary quiz with 3 multiple-choice questions based on the vocabulary words from the following passage:
    Passage: {passage}
    Vocabulary: {vocabulary}
    
    Each question should have 4 options with only one correct answer.
    Focus on testing the meaning and usage of the vocabulary words."""
)

# Updated function to generate passage and vocabulary
def generate_passage():
    try:
        response = passage_model.invoke(passage_prompt.format(grade_level="5th"))
        return response.passage, {word.word: word.definition for word in response.vocabulary}
    except Exception as e:
        st.error(f"Error generating passage: {e}")
        # Fallback to simple passage
        return "This is a sample passage for testing.", {"sample": "example word"}

# Updated function to generate comprehension questions
def generate_questions(passage):
    try:
        response = questions_model.invoke(question_prompt.format(passage=passage))
        return response.questions
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return ["Sample question 1?", "Sample question 2?", "Sample question 3?"]

# Updated function to generate vocabulary quiz
def generate_quiz(passage, vocab_dict):
    try:
        vocab_str = ", ".join([f"{word}: {definition}" for word, definition in vocab_dict.items()])
        response = quiz_model.invoke(quiz_prompt.format(passage=passage, vocabulary=vocab_str))
        return response.questions
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        return []

# Function for text-to-speech
def text_to_speech(text):
    tts = gTTS(text=text, lang="en")
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    audio_b64 = base64.b64encode(audio_file.read()).decode()
    audio_html = f'<audio controls><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>'
    return audio_html

# Function to split text into sentences
def split_into_sentences(text):
    import re
    # Simple sentence splitting using regex
    sentences = re.split(r'[.!?]+', text)
    # Clean up sentences and remove empty ones
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
    return sentences

# Main app logic
st.header("Start Your Reading Adventure!")
if st.button("Get a New Reading Passage"):
    passage, vocab_dict = generate_passage()
    st.session_state.passage = passage
    st.session_state.vocab_dict = vocab_dict
    st.session_state.questions = generate_questions(passage)
    st.session_state.quiz = generate_quiz(passage, vocab_dict)
    st.session_state.passages_completed += 1
    st.session_state.points += 10  # Award points for starting a passage

# Display passage if available
if "passage" in st.session_state:
    st.subheader("Reading Passage")
    
    # Split passage into sentences for individual audio
    sentences = split_into_sentences(st.session_state.passage)
    
    for i, sentence in enumerate(sentences, 1):
        col1, col2 = st.columns([1, 10])
        with col1:
            if st.button(f"🔊 {i}", key=f"sentence_{i}", help=f"Listen to sentence {i}"):
                st.markdown(text_to_speech(sentence), unsafe_allow_html=True)
        with col2:
            st.write(sentence + ".")
    
    # Option to play full passage
    st.write("---")
    col1, col2 = st.columns([2, 8])
    with col1:
        if st.button("🔊 Full Passage", key="full_passage"):
            st.markdown(text_to_speech(st.session_state.passage), unsafe_allow_html=True)
    with col2:
        st.write("Play the entire passage")

    # Vocabulary section
    st.subheader("New Words")
    for word, definition in st.session_state.vocab_dict.items():
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button(f"🔊 {word}", key=f"word_{word}"):
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
    if st.session_state.quiz:
        with st.form("quiz_form"):
            quiz_answers = []
            for i, quiz_question in enumerate(st.session_state.quiz[:3], 1):
                options = [opt.option for opt in quiz_question.options]
                answer = st.radio(f"Q{i}: {quiz_question.question}", options, key=f"quiz_q{i}")
                quiz_answers.append(answer)
            quiz_submitted = st.form_submit_button("Submit Quiz")
            if quiz_submitted:
                # Check answers and calculate score
                correct_answers = 0
                for i, quiz_question in enumerate(st.session_state.quiz[:3]):
                    selected_option = quiz_answers[i]
                    correct_option = next((opt.option for opt in quiz_question.options if opt.is_correct), None)
                    if selected_option == correct_option:
                        correct_answers += 1
                
                score_points = correct_answers * 5
                st.session_state.points += score_points
                st.success(f"Great! You got {correct_answers}/3 correct and earned {score_points} points!")

# Rewards section
st.header("Your Rewards")
if st.session_state.points >= 50:
    st.balloons()
    st.write("🎉 Congratulations! You've unlocked a new badge!")
if st.session_state.points >= 100:
    st.write("🏆 Super Reader! You've earned the Master Reader title!")