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
from datetime import datetime
import threading
import time

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY") or st.secrets["openai_api_key"]

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

# JSON storage configuration
DATA_DIR = "data"
PASSAGES_FILE = os.path.join(DATA_DIR, "passages.json")
USER_PROGRESS_FILE = os.path.join(DATA_DIR, "user_progress.json")
MAX_PASSAGES = 5  # Keep exactly 5 passages in rotation

# Create data directory if it doesn't exist
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Enhanced JSON storage functions
def load_passages_data():
    """Load all passages data from JSON file"""
    if os.path.exists(PASSAGES_FILE):
        with open(PASSAGES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('passages', []), data.get('current_index', 0)
    return [], 0

def save_passages_data(passages, current_index=0):
    """Save passages data with rotation management"""
    data = {
        'passages': passages,
        'current_index': current_index,
        'last_updated': datetime.now().isoformat(),
        'total_passages': len(passages)
    }
    
    with open(PASSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_next_passage():
    """Get the next passage in rotation and update index"""
    passages, current_index = load_passages_data()
    
    if not passages:
        return None, 0
    
    # Get current passage
    current_passage = passages[current_index]
    
    # Update index for next time (rotate through 5 passages)
    next_index = (current_index + 1) % len(passages)
    save_passages_data(passages, next_index)
    
    return current_passage, current_index

def add_or_replace_passage(new_passage_data):
    """Add new passage or replace oldest one if we have 5"""
    passages, current_index = load_passages_data()
    
    # Add timestamp and ID
    new_passage_data['created_at'] = datetime.now().isoformat()
    new_passage_data['id'] = len(passages) + 1 if len(passages) < MAX_PASSAGES else passages[0]['id'] + MAX_PASSAGES
    
    if len(passages) < MAX_PASSAGES:
        # Add new passage if we don't have 5 yet
        passages.append(new_passage_data)
    else:
        # Replace the oldest passage (FIFO rotation)
        replace_index = (current_index + len(passages) - 1) % len(passages)  # Replace the one that will be served last
        passages[replace_index] = new_passage_data
    
    save_passages_data(passages, current_index)
    return new_passage_data['id']

# Background generation functions
def generate_passage_background():
    """Generate a new passage in the background"""
    try:
        response = passage_model.invoke(passage_prompt.format(grade_level="4th"))
        
        # Prepare data for JSON storage
        passage_data = {
            "passage": response.passage,
            "vocabulary": {word.word: word.definition for word in response.vocabulary},
            "questions": [],
            "quiz": [],
            "status": "generating_questions"
        }
        
        # Generate questions
        questions_response = questions_model.invoke(question_prompt.format(passage=response.passage))
        passage_data["questions"] = questions_response.questions
        passage_data["status"] = "generating_quiz"
        
        # Generate quiz
        vocab_str = ", ".join([f"{word}: {definition}" for word, definition in passage_data["vocabulary"].items()])
        quiz_response = quiz_model.invoke(quiz_prompt.format(passage=response.passage, vocabulary=vocab_str))
        
        # Convert quiz questions to JSON-serializable format
        quiz_data = []
        for q in quiz_response.questions:
            quiz_data.append({
                "question": q.question,
                "options": [{"option": opt.option, "is_correct": opt.is_correct} for opt in q.options]
            })
        
        passage_data["quiz"] = quiz_data
        passage_data["status"] = "complete"
        
        # Add to rotation
        add_or_replace_passage(passage_data)
        
        return True
    except Exception as e:
        st.error(f"Background generation error: {e}")
        return False

def initialize_passages():
    """Initialize with 5 passages if none exist"""
    passages, _ = load_passages_data()
    
    if len(passages) < MAX_PASSAGES:
        st.info(f"Initializing reading passages... ({len(passages)}/{MAX_PASSAGES} ready)")
        
        # Generate missing passages
        for i in range(MAX_PASSAGES - len(passages)):
            if generate_passage_background():
                st.success(f"Generated passage {len(passages) + i + 1}/{MAX_PASSAGES}")
            else:
                st.error(f"Failed to generate passage {len(passages) + i + 1}")
        
        st.success("All passages ready!")

# JSON storage functions
def load_user_progress():
    """Load user progress from JSON file"""
    if os.path.exists(USER_PROGRESS_FILE):
        with open(USER_PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "points": 0,
        "passages_completed": 0,
        "vocab_learned": [],
        "quiz_scores": [],
        "last_updated": datetime.now().isoformat()
    }

def save_user_progress(progress_data):
    """Save user progress to JSON file"""
    progress_data['last_updated'] = datetime.now().isoformat()
    with open(USER_PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, indent=2, ensure_ascii=False)

# Initialize session state for points and progress
if "points" not in st.session_state:
    progress = load_user_progress()
    st.session_state.points = progress.get("points", 0)
if "passages_completed" not in st.session_state:
    progress = load_user_progress()
    st.session_state.passages_completed = progress.get("passages_completed", 0)
if "vocab_learned" not in st.session_state:
    progress = load_user_progress()
    st.session_state.vocab_learned = progress.get("vocab_learned", [])
if "generating_in_background" not in st.session_state:
    st.session_state.generating_in_background = False
if "speech_speed" not in st.session_state:
    st.session_state.speech_speed = 0.8  # Default slow speed

# Sidebar for progress tracking and data management
with st.sidebar:
    st.header("Your Progress")
    st.write(f"Points: {st.session_state.points}")
    st.write(f"Passages Completed: {st.session_state.passages_completed}")
    st.write(f"Vocabulary Learned: {len(st.session_state.vocab_learned)} words")
    if st.session_state.vocab_learned:
        st.write("Words Learned:")
        for word in st.session_state.vocab_learned:
            st.write(f"- {word}")
    
    st.header("Speech Settings")
    st.session_state.speech_speed = st.slider(
        "Speech Speed", 
        min_value=0.5, 
        max_value=1.5, 
        value=st.session_state.speech_speed, 
        step=0.1,
        help="0.5 = Very Slow, 1.0 = Normal, 1.5 = Fast"
    )
    speed_labels = {0.5: "Very Slow", 0.6: "Slow", 0.7: "Slow", 0.8: "Slow", 0.9: "Normal", 1.0: "Normal", 1.1: "Fast", 1.2: "Fast", 1.3: "Fast", 1.4: "Very Fast", 1.5: "Very Fast"}
    current_label = speed_labels.get(round(st.session_state.speech_speed, 1), "Custom")
    st.write(f"Current Speed: {current_label}")
    
    st.header("Passage Pool Status")
    passages, current_index = load_passages_data()
    st.write(f"Available Passages: {len(passages)}/{MAX_PASSAGES}")
    st.write(f"Next Passage Index: {current_index + 1}")
    
    if st.session_state.generating_in_background:
        st.write("🔄 Generating new content in background...")
    
    # st.header("Data Management")
    # if st.button("Save Progress"):
    #     progress_data = {
    #         "points": st.session_state.points,
    #         "passages_completed": st.session_state.passages_completed,
    #         "vocab_learned": st.session_state.vocab_learned
    #     }
    #     save_user_progress(progress_data)
    #     st.success("Progress saved!")
    
    # if st.button("Reset Passage Pool"):
    #     if os.path.exists(PASSAGES_FILE):
    #         os.remove(PASSAGES_FILE)
    #     st.success("Passage pool reset! Refresh to regenerate.")

# Simplified prompt templates for structured output
passage_prompt = PromptTemplate(
    input_variables=["grade_level"],
    template="""Generate a short, engaging reading passage suitable for a {grade_level} grader. 
    The passage should be fun, use simple vocabulary, and include 3-5 new words a 2th grader might not know.
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
        response = passage_model.invoke(passage_prompt.format(grade_level="2th"))
        
        # Prepare data for JSON storage
        passage_data = {
            "passage": response.passage,
            "vocabulary": {word.word: word.definition for word in response.vocabulary},
            "questions": [],
            "quiz": []
        }
        
        return response.passage, {word.word: word.definition for word in response.vocabulary}, passage_data
    except Exception as e:
        st.error(f"Error generating passage: {e}")
        # Fallback to simple passage
        passage_data = {
            "passage": "This is a sample passage for testing.",
            "vocabulary": {"sample": "example word"},
            "questions": [],
            "quiz": []
        }
        return "This is a sample passage for testing.", {"sample": "example word"}, passage_data

# Updated function to generate comprehension questions
def generate_questions(passage, passage_data=None):
    try:
        response = questions_model.invoke(question_prompt.format(passage=passage))
        questions = response.questions
        
        # Update passage data if provided
        if passage_data:
            passage_data["questions"] = questions
            
        return questions
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        questions = ["Sample question 1?", "Sample question 2?", "Sample question 3?"]
        if passage_data:
            passage_data["questions"] = questions
        return questions

# Updated function to generate vocabulary quiz
def generate_quiz(passage, vocab_dict, passage_data=None):
    try:
        vocab_str = ", ".join([f"{word}: {definition}" for word, definition in vocab_dict.items()])
        response = quiz_model.invoke(quiz_prompt.format(passage=passage, vocabulary=vocab_str))
        
        # Convert quiz questions to JSON-serializable format
        quiz_data = []
        for q in response.questions:
            quiz_data.append({
                "question": q.question,
                "options": [{"option": opt.option, "is_correct": opt.is_correct} for opt in q.options]
            })
        
        # Update passage data if provided
        if passage_data:
            passage_data["quiz"] = quiz_data
            
        return response.questions
    except Exception as e:
        st.error(f"Error generating quiz: {e}")
        if passage_data:
            passage_data["quiz"] = []
        return []

# Function for text-to-speech
def text_to_speech(text):
    tts = gTTS(text=text, lang="en", slow=st.session_state.speech_speed <= 0.8)
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    audio_b64 = base64.b64encode(audio_file.read()).decode()
    
    # Add speed control via HTML audio playback rate
    playback_rate = st.session_state.speech_speed if st.session_state.speech_speed > 0.8 else 1.0
    audio_html = f'''
    <audio controls onloadstart="this.playbackRate = {playback_rate};">
        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
    </audio>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var audioElements = document.querySelectorAll('audio');
            audioElements.forEach(function(audio) {{
                audio.playbackRate = {playback_rate};
            }});
        }});
    </script>
    '''
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

# Initialize passages on first run
# if st.button("Initialize Passage Pool") or len(load_passages_data()[0]) == 0:
#     initialize_passages()

if st.button("Get a New Reading Passage"):
    # Get next passage from rotation
    passage_data, passage_index = get_next_passage()
    
    if passage_data:
        # Load passage data into session state
        st.session_state.passage = passage_data['passage']
        st.session_state.vocab_dict = passage_data['vocabulary']
        st.session_state.questions = passage_data['questions']
        st.session_state.quiz = passage_data['quiz']
        st.session_state.current_passage_id = passage_data['id']
        
        # Update progress
        st.session_state.passages_completed += 1
        st.session_state.points += 10
        
        # Save progress automatically
        progress_data = {
            "points": st.session_state.points,
            "passages_completed": st.session_state.passages_completed,
            "vocab_learned": st.session_state.vocab_learned
        }
        save_user_progress(progress_data)
        
        st.success(f"Loaded passage {passage_index + 1} from the rotation!")
        
        # Start background generation for next batch
        if not st.session_state.generating_in_background:
            st.session_state.generating_in_background = True
            
            def background_task():
                time.sleep(1)  # Small delay to let UI update
                generate_passage_background()
                st.session_state.generating_in_background = False
            
            thread = threading.Thread(target=background_task)
            thread.daemon = True
            thread.start()
            
            st.info("🔄 Generating fresh content in the background for future sessions...")
    else:
        st.error("No passages available. Please initialize the passage pool first.")

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

    # # Comprehension questions
    # st.subheader("Comprehension Questions")
    # with st.form("comprehension_form"):
    #     answers = []
    #     for i, question in enumerate(st.session_state.questions[:3], 1):
    #         answer = st.text_input(f"Q{i}: {question}", key=f"q{i}")
    #         answers.append(answer)
    #     submitted = st.form_submit_button("Submit Answers")
    #     if submitted:
    #         st.session_state.points += 20  # Award points for submitting answers
    #         st.success("Great job! You earned 20 points for answering the questions!")

    # # Vocabulary quiz
    # st.subheader("Vocabulary Quiz")
    # if st.session_state.quiz:
    #     with st.form("quiz_form"):
    #         quiz_answers = []
    #         for i, quiz_question in enumerate(st.session_state.quiz[:3], 1):
    #             # Handle both structured and JSON loaded formats
    #             if isinstance(quiz_question, dict):
    #                 # JSON loaded format
    #                 options = [opt['option'] for opt in quiz_question['options']]
    #                 question_text = quiz_question['question']
    #             else:
    #                 # Structured format
    #                 options = [opt.option for opt in quiz_question.options]
    #                 question_text = quiz_question.question
                
    #             answer = st.radio(f"Q{i}: {question_text}", options, key=f"quiz_q{i}")
    #             quiz_answers.append(answer)
    #         quiz_submitted = st.form_submit_button("Submit Quiz")
    #         if quiz_submitted:
    #             # Check answers and calculate score
    #             correct_answers = 0
    #             for i, quiz_question in enumerate(st.session_state.quiz[:3]):
    #                 selected_option = quiz_answers[i]
                    
    #                 if isinstance(quiz_question, dict):
    #                     # JSON loaded format
    #                     correct_option = next((opt['option'] for opt in quiz_question['options'] if opt['is_correct']), None)
    #                 else:
    #                     # Structured format
    #                     correct_option = next((opt.option for opt in quiz_question.options if opt.is_correct), None)
                    
    #                 if selected_option == correct_option:
    #                     correct_answers += 1
                
    #             score_points = correct_answers * 5
    #             st.session_state.points += score_points
                
    #             # Save quiz score and progress
    #             progress_data = {
    #                 "points": st.session_state.points,
    #                 "passages_completed": st.session_state.passages_completed,
    #                 "vocab_learned": st.session_state.vocab_learned
    #             }
    #             save_user_progress(progress_data)
                
    #             st.success(f"Great! You got {correct_answers}/3 correct and earned {score_points} points!")

# Rewards section
st.header("Your Rewards")
if st.session_state.points >= 50:
    st.balloons()
    st.write("🎉 Congratulations! You've unlocked a new badge!")
if st.session_state.points >= 100:
    st.write("🏆 Super Reader! You've earned the Master Reader title!")