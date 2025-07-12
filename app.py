import streamlit as st
import os
import csv
from datetime import datetime
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

# CSV persistence configuration
CSV_DATA_DIR = "data"
PASSAGES_CSV = os.path.join(CSV_DATA_DIR, "passages.csv")
PROGRESS_CSV = os.path.join(CSV_DATA_DIR, "user_progress.csv")

# Create data directory if it doesn't exist
if not os.path.exists(CSV_DATA_DIR):
    os.makedirs(CSV_DATA_DIR)

# CSV helper functions
def load_passages_from_csv():
    """Load passages from CSV file"""
    if not os.path.exists(PASSAGES_CSV):
        return []
    
    passages = []
    try:
        with open(PASSAGES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse vocabulary from string format
                vocab_dict = {}
                if row['vocabulary']:
                    vocab_pairs = row['vocabulary'].split(',')
                    for pair in vocab_pairs:
                        if ':' in pair:
                            word, definition = pair.split(':', 1)
                            vocab_dict[word.strip()] = definition.strip()
                
                # Parse questions from string format
                questions = []
                if row['questions']:
                    questions = [q.strip() for q in row['questions'].split(';') if q.strip()]
                
                passages.append({
                    'passage': row['passage'],
                    'vocabulary': vocab_dict,
                    'questions': questions,
                    'created_at': row['created_at']
                })
    except Exception as e:
        st.error(f"Error loading passages from CSV: {e}")
        return []
    
    return passages

def save_passage_to_csv(passage, vocab_dict, questions):
    """Save a new passage to CSV file"""
    try:
        # Format vocabulary as string
        vocab_str = ','.join([f"{word}:{definition}" for word, definition in vocab_dict.items()])
        
        # Format questions as string
        questions_str = ';'.join(questions)
        
        # Prepare row data
        row_data = {
            'passage': passage,
            'vocabulary': vocab_str,
            'questions': questions_str,
            'created_at': datetime.now().isoformat()
        }
        
        # Check if file exists and has headers
        file_exists = os.path.exists(PASSAGES_CSV)
        
        with open(PASSAGES_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['passage', 'vocabulary', 'questions', 'created_at'])
            
            # Write headers if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row_data)
        
        return True
    except Exception as e:
        st.error(f"Error saving passage to CSV: {e}")
        return False

def load_user_progress_from_csv():
    """Load user progress from CSV file"""
    if not os.path.exists(PROGRESS_CSV):
        return {
            'points': 0,
            'passages_completed': 0,
            'vocab_learned': []
        }
    
    try:
        with open(PROGRESS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        if rows:
            # Get the most recent progress entry
            latest = rows[-1]
            vocab_learned = []
            if latest['vocab_learned']:
                vocab_learned = latest['vocab_learned'].split(',')
            
            return {
                'points': int(latest['points']),
                'passages_completed': int(latest['passages_completed']),
                'vocab_learned': vocab_learned
            }
    except Exception as e:
        st.error(f"Error loading user progress from CSV: {e}")
    
    return {
        'points': 0,
        'passages_completed': 0,
        'vocab_learned': []
    }

def save_user_progress_to_csv(points, passages_completed, vocab_learned):
    """Save user progress to CSV file"""
    try:
        # Format vocab_learned as string
        vocab_str = ','.join(vocab_learned)
        
        # Prepare row data
        row_data = {
            'points': points,
            'passages_completed': passages_completed,
            'vocab_learned': vocab_str,
            'last_updated': datetime.now().isoformat()
        }
        
        # Check if file exists and has headers
        file_exists = os.path.exists(PROGRESS_CSV)
        
        with open(PROGRESS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['points', 'passages_completed', 'vocab_learned', 'last_updated'])
            
            # Write headers if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(row_data)
        
        return True
    except Exception as e:
        st.error(f"Error saving user progress to CSV: {e}")
        return False

# Page configuration
st.set_page_config(page_title="English Reading Adventure", page_icon="📚")
st.title("📚 English Reading Adventure for 7th Graders")

# Initialize session state for points and progress
if "points" not in st.session_state:
    progress = load_user_progress_from_csv()
    st.session_state.points = progress['points']
if "passages_completed" not in st.session_state:
    progress = load_user_progress_from_csv()
    st.session_state.passages_completed = progress['passages_completed']
if "vocab_learned" not in st.session_state:
    progress = load_user_progress_from_csv()
    st.session_state.vocab_learned = progress['vocab_learned']

# Load existing passages from CSV
if "available_passages" not in st.session_state:
    st.session_state.available_passages = load_passages_from_csv()
if "current_passage_index" not in st.session_state:
    st.session_state.current_passage_index = 0

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
    
    st.header("Data Management")
    st.write(f"Available Passages: {len(st.session_state.available_passages)}")
    
    if st.button("Save Progress"):
        success = save_user_progress_to_csv(
            st.session_state.points,
            st.session_state.passages_completed,
            st.session_state.vocab_learned
        )
        if success:
            st.success("Progress saved to CSV!")
        else:
            st.error("Failed to save progress")
    
    if st.button("Clear All Data"):
        if st.button("Confirm Clear", key="confirm_clear"):
            # Clear CSV files
            if os.path.exists(PASSAGES_CSV):
                os.remove(PASSAGES_CSV)
            if os.path.exists(PROGRESS_CSV):
                os.remove(PROGRESS_CSV)
            
            # Reset session state
            st.session_state.points = 0
            st.session_state.passages_completed = 0
            st.session_state.vocab_learned = []
            st.session_state.available_passages = []
            st.session_state.current_passage_index = 0
            
            st.success("All data cleared!")

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

# Check if we have existing passages
if st.session_state.available_passages:
    st.info(f"You have {len(st.session_state.available_passages)} passages available from previous sessions!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Use Existing Passage"):
            # Use existing passage
            if st.session_state.current_passage_index < len(st.session_state.available_passages):
                passage_data = st.session_state.available_passages[st.session_state.current_passage_index]
                st.session_state.passage = passage_data['passage']
                st.session_state.vocab_dict = passage_data['vocabulary']
                st.session_state.questions = passage_data['questions']
                
                # Move to next passage for next time
                st.session_state.current_passage_index = (st.session_state.current_passage_index + 1) % len(st.session_state.available_passages)
                
                st.session_state.passages_completed += 1
                st.session_state.points += 10
                
                # Save progress
                save_user_progress_to_csv(
                    st.session_state.points,
                    st.session_state.passages_completed,
                    st.session_state.vocab_learned
                )
                
                st.success("Loaded existing passage!")
            else:
                st.error("No more existing passages available")
    
    with col2:
        if st.button("Generate New Passage"):
            # Generate new passage
            with st.spinner("Generating new reading passage..."):
                passage, vocab_dict = generate_passage()
                questions = generate_questions(passage)
                
                # Save to CSV
                if save_passage_to_csv(passage, vocab_dict, questions):
                    st.session_state.passage = passage
                    st.session_state.vocab_dict = vocab_dict
                    st.session_state.questions = questions
                    st.session_state.quiz = generate_quiz(passage)
                    st.session_state.passages_completed += 1
                    st.session_state.points += 10  # Award points for starting a passage
                    
                    # Add to available passages
                    st.session_state.available_passages.append({
                        'passage': passage,
                        'vocabulary': vocab_dict,
                        'questions': questions,
                        'created_at': datetime.now().isoformat()
                    })
                    
                    # Save progress
                    save_user_progress_to_csv(
                        st.session_state.points,
                        st.session_state.passages_completed,
                        st.session_state.vocab_learned
                    )
                    
                    st.success("New passage generated and saved!")
                else:
                    st.error("Failed to save passage to CSV")
else:
    # No existing passages, generate new one
    if st.button("Get Your First Reading Passage"):
        with st.spinner("Generating your first reading passage..."):
            passage, vocab_dict = generate_passage()
            questions = generate_questions(passage)
            
            # Save to CSV
            if save_passage_to_csv(passage, vocab_dict, questions):
                st.session_state.passage = passage
                st.session_state.vocab_dict = vocab_dict
                st.session_state.questions = questions
                st.session_state.quiz = generate_quiz(passage)
                st.session_state.passages_completed += 1
                st.session_state.points += 10  # Award points for starting a passage
                
                # Add to available passages
                st.session_state.available_passages.append({
                    'passage': passage,
                    'vocabulary': vocab_dict,
                    'questions': questions,
                    'created_at': datetime.now().isoformat()
                })
                
                # Save progress
                save_user_progress_to_csv(
                    st.session_state.points,
                    st.session_state.passages_completed,
                    st.session_state.vocab_learned
                )
                
                st.success("First passage generated and saved!")
            else:
                st.error("Failed to save passage to CSV")

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
                # Save progress when vocabulary is learned
                save_user_progress_to_csv(
                    st.session_state.points,
                    st.session_state.passages_completed,
                    st.session_state.vocab_learned
                )

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
            # Save progress when answers are submitted
            save_user_progress_to_csv(
                st.session_state.points,
                st.session_state.passages_completed,
                st.session_state.vocab_learned
            )
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
            # Save progress when quiz is submitted
            save_user_progress_to_csv(
                st.session_state.points,
                st.session_state.passages_completed,
                st.session_state.vocab_learned
            )
            st.success("Awesome! You earned 15 points for completing the quiz!")

# Rewards section
st.header("Your Rewards")
if st.session_state.points >= 50:
    st.balloons()
    st.write("🎉 Congratulations! You've unlocked a new badge!")
if st.session_state.points >= 100:
    st.write("🏆 Super Reader! You've earned the Master Reader title!")